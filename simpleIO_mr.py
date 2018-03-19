__author__ = 'mbrebion'

from libraries.i2clcda import lcd_init,lcd_string,LCD_LINE_1,LCD_LINE_2
from libraries.RotaryEncoder import RotaryEncoder
from time import sleep
from io_mr import MSG_SELECT,MSG_MENU,MSG_VOL,MSG_WIFI,MSG_BACK,MSG_SHUTDOWN,serverThread



class SimpleIo(object):
    """
    class dealing with IOs
    """

    def __init__(self,os):
        # setup encoders
        self.menuCtl=RotaryEncoder(13,15,11,"Menu")
        self.os=os # link to parent
        # init screen

        try :
            lcd_init()
        except IOError:
            print "no lcd screen connected"

        # TCP comm
        self.tcpServer=serverThread(os)


    def communicateTCP(self):
        pass


    def startIO(self):
        """
        main loop of os
        :return:
        """
        self.goOn=True
        while self.goOn:

            # change menu
            dec=self.menuCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_MENU,dec)

            # select button status
            if self.menuCtl.getSwitch():
                self.os.takeAction(MSG_SELECT,0)

            # exit ?
            self.os.checkStopAsked()

            self.menuCtl.updateCurrent()

            sleep(0.25)

        # close tcp server
        print "closing tcp server"
        self.tcpServer.shutDown()



    def writeText(self,text,line):
        # remote displays (if connected)
        self.tcpServer.sendToAll(str(line)+text)

        # LCD screen if connected
        pass

