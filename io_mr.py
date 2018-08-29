__author__ = 'mbrebion'

from libraries.i2clcda import lcd_init,lcd_string,LCD_LINE_1,LCD_LINE_2,LCD_LINE_3,LCD_LINE_4
from libraries.RotaryEncoder import RotaryEncoder
from libraries.backlight import Backlight
from libraries.faceButtons import FaceButtons
from time import sleep
from libraries.tcpComm import serverThread,connectToHost,ClientThread
from libraries.constants import MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_PROPAGATE_ORDER
from config import rotOne,rotTwo,server,lcdLines,entries
import datetime,pytz
from system import checkCDStatus

tz=pytz.timezone('Europe/Paris')

class Io(object):
    """
    class dealing with IOs
    """

    def __init__(self,os):
        # setup encoders
        self.volumeCtl=RotaryEncoder(rotOne,"Volume")
        self.menuCtl=RotaryEncoder(rotTwo,"Menu")
        self.backlight=Backlight(os)
        self.os=os # link to parent
        #
        self.lines=["","","",""]
        self.clines=[False,False,False,False]
        self.physicalLines=[LCD_LINE_1,LCD_LINE_2,LCD_LINE_3,LCD_LINE_4]
        #
        self.faceButtons=FaceButtons()
        self.resend=False

        # init screen
        try :
            lcd_init()
        except IOError:
            print "no lcd screen connected"

        # TCP comm
        if server :
            self.tcpServer=serverThread(os)
        else :
            self.cth()

    def cth(self):
        self.connectedToHost=False # set to true if connection is established with main hifi system
        self.client=None
        skt=connectToHost()
        if skt!=False :
            self.client=ClientThread("unknown", 0, skt,self.os)
            self.connectedToHost=True

    def sendMessageToAll(self,text):
        if server:
            self.tcpServer.sendToAllDevices(text)
        else:
            if self.connectedToHost:
                self.client.send(MSG_PROPAGATE_ORDER+","+text)

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

            # change menu
            dec=self.menuCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_MENU, dec)

            # back button status
            if self.volumeCtl.getSwitch():
                self.os.takeAction(MSG_BACK, 0)

            # select button status
            if self.menuCtl.getSwitch():
                self.os.takeAction(MSG_SELECT, 0)

            # front buttons
            for id in self.faceButtons.getPressed():
                self.os.takeAction(MSG_BUTTON,id)

            #alarms
            now = datetime.datetime.now(tz=tz)
            for alarm in self.os.menu.getActiveAlarms():
                if now.hour == alarm.hour and  now.minute >= alarm.minute and alarm.reseted:
                    alarm.reseted=False
                    self.os.menu.forceRadio()


            if now.hour==0 and now.minute==0 :
                for alarm in self.os.menu.getActiveAlarms():
                    alarm.reseted=True # reset all alarms at midnight


            # not very often
            if count % 8 ==0 :
                self.os.dealWithBluetoothCon()
                if not self.os.cdInside:
                    self.dealWithCD() # cd drive is checked more often after eject has been asked

            # not often
            if count % 40 == 0:
                # this test is now done less often than before to prevent sd card corruption and overflow.
                self.os.checkStopAsked()

                if self.os.cdInside:
                    self.dealWithCD()

                if not server and not self.connectedToHost:
                    self.cth()
                count = 1


            # refresh view if any changes occurred
            self.os.refreshView()

            self._writeText()

            sleep(0.1)
            count+=1

        # close tcp server
        self.tcpServer.shutDown()
        self.backlight.shutDown()
        self.askResendTexts()



    def resetScreen(self):
        lcd_init()
        self.askResendTexts()

    def askResendTexts(self):
        self.resend=True

    def writeText(self,text,line,delay=-1):
        """
        text is locally changed and display next time
        negative delay means text stay forever ;
        """
        if line==4 and text != "":
            line=lcdLines

        id = line-1
        if self.lines[id] != text :
            self.lines[id] = text
            self.clines[id] = True

    def _writeText(self):
        """
        text is truly output by this function, which can only be called by main thread
        """
        if self.resend:
            for i in range(lcdLines):
                self.clines[i]=True
            self.resend=False


        for id in range(lcdLines):
            if self.clines[id]:
                self.clines[id] = False
                if server :
                    self.tcpServer.sendToAllRemotes(str(id+1)+";;"+self.lines[id])
                try :
                    lcd_string(self.lines[id],self.physicalLines[id])
                except :
                    pass