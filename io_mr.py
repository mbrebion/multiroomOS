__author__ = 'mbrebion'

from libraries.i2clcda import lcd_init,lcd_string,LCD_LINE_1,LCD_LINE_2,LCD_LINE_3,LCD_LINE_4
from libraries.RotaryEncoder import RotaryEncoder
from libraries.backlight import Backlight
from libraries.faceButton import FaceButton
from time import sleep
from libraries.tcpComm import serverThread
from libraries.constants import MSG_SHUTDOWN,MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_WIFI
from config import rotOne,rotTwo

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
        buttonPorts=[10,8,16,18]
        buttonIds=[1,3,2,4]
        self.faceButtons=[]
        self.resend=False
        index=0
        for port in buttonPorts:
            self.faceButtons.append(FaceButton(port,buttonIds[index]))
            index+=1



        # init screen
        try :
            lcd_init()
        except IOError:
            print "no lcd screen connected"

        # TCP comm
        self.tcpServer=serverThread(os)

    def askBacklight(self):
        self.backlight.newCommand()

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
                self.os.takeAction(MSG_BACK,0)

            # select button status
            if self.menuCtl.getSwitch():
                self.os.takeAction(MSG_SELECT,0)

            for faceButton in self.faceButtons:
                if faceButton.getSwitch():
                    self.os.takeAction(MSG_BUTTON,faceButton.id)

            # exit ?
            if count%40 == 0 :
                # this test is now done less often than before to prevent sd card corruption and overflow.
                self.os.checkStopAsked()
                count=1

            # refresh view if any changes occurred
            self.os.refreshView()

            self._writeText()

            sleep(0.12)
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

    def writeText(self,text,line):
        """
        text is locally changed and display next time
        """
        id = line-1
        if self.lines[id] != text :
            self.lines[id] = text
            self.clines[id] = True

    def _writeText(self):
        """
        text is truly output by this function, which can only be called by main thread
        """
        if self.resend:
            for i in range(4):
                self.clines[i]=True
            self.resend=False

        for id in range(4):
            if self.clines[id]:
                self.clines[id] = False
                self.tcpServer.sendToAllRemotes(str(id+1)+";;"+self.lines[id])
                try :
                    lcd_string(self.lines[id],self.physicalLines[id])
                except :
                    pass