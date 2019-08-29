from libraries.connect import Connect

__author__ = 'mbrebion'

from libraries.i2clcda import lcd_init,lcd_string
from libraries.RotaryEncoder import RotaryEncoder
from libraries.backlight import Backlight
from libraries.faceButtons import FaceButtons
from libraries.connect import Connect
from time import sleep,time
from libraries.constants import MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,BIG,MSG_PRINT,ASK_ISPLAYING,ASW_TRUE,ASW_FALSE,MODE_SNAPSTREAM_OUT
from config import rotOne,rotTwo,entries,name,kind
import datetime,pytz
from libraries.system import checkCDStatus,logDebug,logInfo,logWarning,isMPDPlaying
from threading import Lock
from RPi import GPIO


sep="?s?"
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

        self.loopTime=0.06

        self.backlight=Backlight(os)
        if kind == BIG:
            self.lcdLines=4
        else :
            self.lcdLines=2

        # init screen
        try :
            lcd_init()
        except IOError:
            logWarning("no lcd screen connected")
        self.resend=False

        # Network
        self.startNetwork()

    ############## gpio connected stuff ###########

    def askBacklight(self):
        self.backlight.newCommand()

    def dealWithCD(self):
        if "cd" not in entries:
            return

        out = checkCDStatus()
        if out == False:
            self.os.setCDInside(False)
        else:
            self.os.setCDInside(True)

        self.os.menu.setCDInfos(out)

    def updateRotariesStates(self):
        self.volumeCtl.updateState()
        self.menuCtl.updateState()

    ################### Networking ################

    def startNetwork(self):
        self.connect=Connect(fr=self.receivingRemoteMessage, fhu=self.updatingRemotesList, fe=self.errorHandling,fa=self.answerToQuestion, name=name)  # load network facilities (with default IP and port)
        self.remoteControls = []

    def answerToQuestion(self, question, sender):
        logDebug(" somebody (" + sender + ") asked " + question)
        if question == ASK_ISPLAYING:
            if isMPDPlaying():
                return ASW_TRUE
            else:
                return ASW_FALSE

    def appendRemoteControls(self,name):
        if name not in self.remoteControls:
            self.remoteControls.append(name)
            self.askResendTexts()
            logInfo("remotes controls (adding)  : ",self.remoteControls)

    def removeRemoteControls(self,name):
        if name in self.remoteControls:
            self.remoteControls.remove(name)
            logInfo("remotes controls (removing) : ", self.remoteControls)

        if len(self.remoteControls)==0 :
            # do something when last subscriber left
            pass

        stillOneActiveRemoteControls=False
        for d in self.remoteControls:
            if "local" not in d:
                stillOneActiveRemoteControls=True
        if not stillOneActiveRemoteControls:
            # in this case there is no more active listener (i.e. using snapcast).
            if self.os.mode==MODE_SNAPSTREAM_OUT :
                self.os.stopOutputtingToSnapCast()
            pass

    def errorHandling(self, error):
        # self.os._safeStop()
        logWarning("error happened in connect caused by message : ", error)

    def receivingRemoteMessage(self,message,source):
        """
        function called when a message is received from a remote
        :param message: the message received
        :param source: the remote name who sent the message
        :return: nothing
        """
        msg = message.split(sep)

        # message must be : "order,intValue"
        if msg[0] == MSG_PRINT :
            ### print messages concern io and are dealt with right here
            self.writeTextFromRemote(msg[1])
            return

        self.os.takeAction(msg[0], int(msg[1]), source)
        self.sendLinesToRemotes()

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
            self.removeRemoteControls(title)

        logInfo("known hosts : ",self.remoteNames)

    def sendMessageToAll(self, text):
        """
        This function send to message "text" to all other known remotes.
        A remote that is not yet register WILL NOT receive this message
        :param text: the message to be sent 
        :return: nothing
        """

        self.connect.sendMessage(text,dest=self.remoteNames)

    def askMessageTo(self, question, dest):
        """
        ask question to targeted remotes devices and return answers
        :param msg: question asked
        :param dest: remote device or list of remote devices
        :return: dict containing answers from devices (may contains False if remote has not answer within a TIMOUT)
        """
        return self.connect.askDevice(question, dest)

    def sendMessageTo(self, text, dest):
        """
        This function send to message "text" to all other known remotes.
        A remote that is not yet registeer WILL NOT receive this message
        :param text: the message to be sent
        :param dest: list of remotes which must receive this message
        :return: nothing
        """
        self.connect.sendMessage(text, dest=dest)


    ##############################################################################################
    ########################################## MAIN LOOP #########################################
    ##############################################################################################

    def mainLoop(self):
        """
        _main loop of os
        outputs to devices and lcds should only be performed from this thread to prevent concurrency
        Other thread might ask for an output refresh
        :return: nothing
        """
        self.goOn = True
        count = 0

        while self.goOn:
            begin=time()

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


            # not very often
            if count % int(180/self.loopTime) == 0:
                count = 1
                self.updateRotariesStates()



            # not often
            if count % int(2.5/self.loopTime) == 0:

                self.os.considerStoppingRebooting()

                # this test is now done less often than before to prevent sd card corruption and overflow.

                # alarms
                now = datetime.datetime.now(tz=tz)
                for alarm in self.os.menu.getActiveAlarms():
                    if int(now.hour) == int(alarm.hour) and int(now.minute) >= int(alarm.minute) and alarm.reseted:
                        alarm.reseted = False
                        logInfo("alarm found in io_mr")
                        self.os.menu.forceRadio()

                if int(now.hour) == 0 and int(now.minute) == 0:
                    for alarm in self.os.menu.getActiveAlarms():
                        alarm.reseted = True  # reset all alarms at midnight

                self.os.dealWithBluetoothCon()
                self.backlight.test()



            # refresh view if any changes occurred
            self.updateScreens()

            count += 1
            end=time()

            sleep(max(self.loopTime  - (end-begin),0.01))

    ##############################################################################################
    ##############################################################################################
    ##############################################################################################

    def closeIO(self):
        self.goOn = False
        self.backlight.shutDown()
        self.askResendTexts()
        GPIO.cleanup()
        Connect.instance.leavingNetwork()

    def updateScreens(self):
        self.os.refreshView()
        self.checkTemporaryWrite()
        self.sendLinesToRemotes()

    def resetScreen(self):
        lcd_init()
        self.askResendTexts()

    def askResendTexts(self):

        for i in range(1,len(self.lines)):
            self.writeText(self.lines[i],i,force=True)
        self.sendLinesToRemotes()

    def writeText(self, text, line, force=False):
        """
        text is locally changed and display next time
        """

        if self.lines[line] != text or force:   ############### we never pass this when change in backlight occur
            self.lines[line] = text
            if line < self.lcdLines:

                lcd_string(text, line)

            elif line == self.lcdLines:
                self.correctLastLine = False
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

        with self.sendLock:
            if len(self.outMessage) == 0:
                return

            out="("
            while len(self.outMessage)>0:
                mess=self.outMessage.pop()
                out+=mess
        out=out[:-1]+")"
        self.sendMessageTo(MSG_PRINT + sep + out, self.remoteControls)

    def checkTemporaryWrite(self, force=False):
        tim = time()

        if (tim > self.lastChange + self.delay or force):
            # we can print a new message
            for k in range(self.lcdLines, len(self.messageQueu)):

                if self.messageQueu[k] != "":
                    lcd_string(self.messageQueu[k], self.lcdLines)
                    self.messageQueu[k] = ""
                    self.lastChange = tim
                    self.correctLastLine = False
                    return

            if not self.correctLastLine:
                lcd_string(self.message, self.lcdLines)
                self.correctLastLine = True


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
                self.writeText(text.replace("^","v"),line)















