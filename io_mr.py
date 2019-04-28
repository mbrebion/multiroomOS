from libraries.networkUDP import NetworkUDP

__author__ = 'mbrebion'

from libraries.i2clcda import lcd_init,lcd_string
from libraries.RotaryEncoder import RotaryEncoder
from libraries.backlight import Backlight
from libraries.faceButtons import FaceButtons
from time import sleep,time
from libraries.constants import MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,BIG,MSG_PRINT
from config import rotOne,rotTwo,entries,name,kind
import datetime,pytz
from system import checkCDStatus
from threading import Lock
from RPi import GPIO


tz=pytz.timezone('Europe/Paris')

class Io(object):
    """
    class dealing with IOs
    """

    def __init__(self,os):
        """
        init io stuff
        :param os: os instance
        """
        self.os=os

        # setup encoders, buttons
        self.volumeCtl=RotaryEncoder(rotOne,"Volume")
        self.menuCtl=RotaryEncoder(rotTwo,"Menu")
        self.faceButtons=FaceButtons()

        self.sendLock=Lock()

        self.lines=["","","","",""]
        self.messageQueu = ["","","","",""]
        self.outMessage=[]
        self.message=""
        self.lastChange=0
        self.delay=2

        self.backlight=Backlight(os)
        if kind == BIG:
            self.lcdLines=4
        else :
            self.lcdLines=2

        # init screen
        try :
            lcd_init()
        except IOError:
            print("no lcd screen connected")
        self.resend=False


        # Network
        self.nUDP = NetworkUDP(name= name,fr=self.receivingRemoteMessage,fhu=self.updatingRemotesList)  # load network facilities (with default IP and port)

        # remotesControls
        self.remoteControls=[]

    def appendRemoteControls(self,name):
        if name not in self.remoteControls:
            self.remoteControls.append(name)
            self.askResendTexts()
            print("remotes controls : ",self.remoteControls)

    def removeRemoteControls(self,name):
        if name in self.remoteControls:
            self.remoteControls.remove(name)
            print("remotes controls : ", self.remoteControls)

        if len(self.remoteControls)==0 :
            # do something when last subscriber left
            pass


    def receivingRemoteMessage(self,message,source):
        """
        function called when a message is received from a remote
        :param message: the message received
        :param source: the remote name who sent the message
        :return: nothing
        """
        msg = message.split(",")
        # message must be : "order,intValue"
        if msg[0] == MSG_PRINT :
            ### print messages concern io and are dealt with right here
            self.writeTextFromRemote(msg[1])
        else:
            self.os.takeAction(msg[0], int(msg[1]), source)


    def updatingRemotesList(self,remotes):
        """
        This function is called whenever there is a known change in the remote devices
        WARNING : a remote present in this list might be disconnected at the moment this function is called.
        :param remotes: dictionnary containing information about the remote devices.
        :return: nothing
        """
        self.remoteNames=list(remotes.keys())
        if name in self.remoteNames:
            self.remoteNames.remove(name) # is it modifying remoteNames ?
        ####################################################################### TODO : in case of streaming, one can stop the stream if all host disconnected or sent a stop message

        # remove a remote controls if it disconnects
        toKill=[]
        for title in self.remoteControls:
            if title not in self.remoteNames:
                toKill.append(title)
        for title in toKill:
            print("remove remote control : ", title)
            self.removeRemoteControls(title)

        print("known hosts : ",self.remoteNames)

    def sendMessageToAll(self, text):
        """
        This function send to message "text" to all other known remotes.
        A remote that is not yet registeer WILL NOT receive this message
        :param text: the message to be sent 
        :return: nothing
        """
        self.nUDP.sendMSG(text,dest=self.remoteNames)

    def sendMessageTo(self, text,dest):
        """
        This function send to message "text" to all other known remotes.
        A remote that is not yet registeer WILL NOT receive this message
        :param text: the message to be sent
        :param dest: list of remotes which must receive this message
        :return: nothing
        """
        self.nUDP.sendMSG(text,dest=dest)


    def askBacklight(self):
        self.backlight.newCommand()

    def dealWithCD(self):
        if "cd" not in entries:
            return

        out=checkCDStatus()
        if out==False:
            self.os.cdInside=False
        else:
            self.os.cdInside=True


        self.os.menu.setCDInfos(out)

    def updateRotariesStates(self):
        self.volumeCtl.updateState()
        self.menuCtl.updateState()

    ##############################################################################################
    ########################################## MAIN LOOP #########################################
    ##############################################################################################
    def mainLoop(self):
        """
        main loop of os
        outputs to devices and lcds should only be performed from this thread to prevent concurrency
        Other thread might ask for an output refresh
        :return: nothing
        """
        self.goOn = True
        count = 0

        while self.goOn:

            # change volume
            dec=self.volumeCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_VOL, dec)
                count = 1

            # change menu
            dec=self.menuCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_MENU, dec)
                count = 1

            # back button status
            if self.volumeCtl.getSwitch():
                self.os.takeAction(MSG_BACK, 0)
                count = 1

            # select button status
            if self.menuCtl.getSwitch():
                self.os.takeAction(MSG_SELECT, 0)
                count = 1

            # front buttons
            for id in self.faceButtons.getPressed():
                self.os.takeAction(MSG_BUTTON,id)
                count = 1

            #alarms
            now = datetime.datetime.now(tz=tz)
            for alarm in self.os.menu.getActiveAlarms():
                if now.hour == alarm.hour and now.minute >= alarm.minute and alarm.reseted:
                    alarm.reseted=False
                    self.os.menu.forceRadio()


            if now.hour==0 and now.minute==0 :
                for alarm in self.os.menu.getActiveAlarms():
                    alarm.reseted=True # reset all alarms at midnight

            # not very often
            if count % 160 == 0:
                count = 1
                self.dealWithCD()
                self.updateRotariesStates()


            # not often
            if count % 40 == 0:
                # this test is now done less often than before to prevent sd card corruption and overflow.
                self.os.dealWithBluetoothCon()
                self.backlight.test()


            # refresh view if any changes occurred
            self.os.refreshView()


            self.checkTemporaryWrite()
            self.sendLinesToRemotes()

            sleep(0.06)
            count+=1

    ##############################################################################################
    ##############################################################################################
    ##############################################################################################

    def endLoop(self):
        self.goOn=False

    def closeIO(self):
        self.goOn=False
        self.backlight.shutDown()
        self.askResendTexts()
        self.nUDP.leaveNetwork()
        GPIO.cleanup()


    def resetScreen(self):
        lcd_init()
        self.askResendTexts()

    def askResendTexts(self):
        for i in range(len(self.lines)):
            self.writeText(self.lines[i],i,force=True)

    def writeText(self, text, line, force=False):
        """
        text is locally changed and display next time
        negative delay means text stay forever ;
        """
        if self.lines[line] != text or force:
            self.lines[line] = text

            if line < self.lcdLines:
                lcd_string(text, line)

            elif line == self.lcdLines:
                self.message=text
                self.checkTemporaryWrite()
            else:
                # in this case, the lcd does not have enough lines and temporary messaged are printed
                self.messageQueu[line] = text
                self.checkTemporaryWrite(True)

            if len(self.remoteControls) > 0:
                with self.sendLock:
                    self.outMessage.append(str(line)+"%"+text+";")



    def sendLinesToRemotes(self):
        if len(self.outMessage)==0:
            return

        with self.sendLock:
            out="("
            while len(self.outMessage)>0:
                mess=self.outMessage.pop()
                out+=mess
        out=out[:-1]+")"
        self.sendMessageTo(MSG_PRINT + "," + out, self.remoteControls)

    def checkTemporaryWrite(self, force=False):
        tim = time()
        if (tim > self.lastChange + self.delay or force):
            # we can print a new message
            for k in range(self.lcdLines, len(self.messageQueu)):

                if self.messageQueu[k] != "":
                    lcd_string(self.messageQueu[k], self.lcdLines)
                    self.messageQueu[k] = ""
                    self.lastChange = tim
                    return

            lcd_string(self.message, self.lcdLines)

    def writeTextFromRemote(self,outMessage):
        """
        This function take a message from remotes and display it on screen
        :param outMessage:
        :return:
        """
        out=outMessage[1:-1].split(";")
        for elem in out:
            elems=elem.split("%")
            line = int(elems[0])
            text=elems[1]
            if "Vol :" not in text:
                self.writeText(text,line)
        print()














