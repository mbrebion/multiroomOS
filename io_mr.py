__author__ = 'mbrebion'

from libraries.i2clcda import lcd_init,lcd_string,LCD_LINE_1,LCD_LINE_2,LCD_LINE_3,LCD_LINE_4
from libraries.RotaryEncoder import RotaryEncoder
from libraries.backlight import Backlight
from libraries.faceButton import FaceButton
from time import sleep
from libraries.tcpComm import serverThread
from libraries.constants import MSG_SHUTDOWN,MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_WIFI



class Io(object):
    """
    class dealing with IOs
    """

    def __init__(self,os):
        # setup encoders
        self.volumeCtl=RotaryEncoder(19,23,21,"Volume")
        self.menuCtl=RotaryEncoder(11,15,13,"Menu")
        self.backlight=Backlight(22)
        self.os=os # link to parent

        buttonPorts=[10,8,16,18]
        buttonIds=[4,2,3,1]
        self.faceButtons=[]
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

    def startIO(self):
        """
        main loop of os
        :return:
        """
        self.goOn=True
        count=0
        while self.goOn:

            # change volume
            dec=self.volumeCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_VOL,dec)

            # change menu
            dec=self.menuCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_MENU,+dec)

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
            if count%20 == 0 :
                # this test is now done less often than before to prevent sd card corruption and overflow.
                self.os.checkStopAsked()


            sleep(0.2)
            count+=1

        # close tcp server
        print "closing tcp server"
        self.tcpServer.shutDown()
        self.backlight.shutDown()




    def writeText(self,text,line):

        # remote displays (if connected)
        self.tcpServer.sendToAllRemotes(str(line)+";;"+text)

        # LCD screen if connected
        try :
            if line==1:
                oline=LCD_LINE_1
                lcd_string(text,oline)
            if line==2:
                oline=LCD_LINE_2
                lcd_string(text,oline)
            if line==3:
                oline=LCD_LINE_3
                lcd_string(text,oline)
            if line==4:
                oline=LCD_LINE_4
                lcd_string(text,oline)

        except IOError:
            print "screen disconnected"

