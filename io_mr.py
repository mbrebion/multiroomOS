__author__ = 'mbrebion'

from libraries.i2clcda import lcd_init,lcd_string,LCD_LINE_1,LCD_LINE_2
from libraries.RotaryEncoder import RotaryEncoder
from time import sleep
import os.path
import os as osys


MSG_WIFI="wifi"
MSG_VOL="vol"
MSG_MENU="menu"
MSG_SELECT="select"
MSG_BACK="prev"

MSG_SHUTDOWN="sd"


class Io(object):
    """
    class dealing with IOs
    """


    def __init__(self,os):
        # setup encoders
        self.volumeCtl=RotaryEncoder(11,13,15,"Volume")
        self.menuCtl=RotaryEncoder(19,21,23,"Menu")
        self.os=os # link to parent
        # init screen

        try :
            lcd_init()
        except IOError:
            print "no lcd screen connected"


    def checkStopAsked(self):
        if os.path.isfile("/home/pi/os/.stop"):
            self.goOn=False
            osys.system('rm /home/pi/os/.stop')
            self.writeText("Exiting", 1)


    def startIO(self):
        """
        main loop of os
        :return:
        """
        self.goOn=True
        while self.goOn:

            # change volume
            dec=self.volumeCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_VOL,dec)

            # change menu
            dec=self.menuCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_MENU,dec)

            # back button status
            if self.volumeCtl.getSwitch():
                self.os.takeAction(MSG_BACK,0)

            # select button status
            if self.menuCtl.getSwitch():
                self.os.takeAction(MSG_SELECT,0)


            # exit ?
            self.checkStopAsked()



            sleep(0.4)





    def writeText(self,text,line):
        try :
            if line==1:
                oline=LCD_LINE_1
                lcd_string(text,oline)
            if line==2:
                oline=LCD_LINE_2
                lcd_string(text,oline)
        except IOError:
            print "screen disconnected"

