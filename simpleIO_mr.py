__author__ = 'mbrebion'

from libraries.RotaryEncoder import RotaryEncoder
from time import sleep
from libraries.constants import MSG_SHUTDOWN,MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_WIFI
from libraries.tcpComm import ClientThread,connectToHost


class SimpleIo(object):
    """
    class dealing with IOs
    """

    def __init__(self,os):
        # setup encoders
        self.menuCtl=RotaryEncoder(13,15,11,"Menu")
        self.os=os # link to parent
        # init screen
        self.connectedToHost=False # set to true if connection is established with main hifi system
        self.client=None
        self.cth()



    def cth(self):
        skt=connectToHost()
        if skt!=False :
            self.client=ClientThread("unknown", 0, skt,self.os)
            self.connectedToHost=True


    def askBacklight(self):
        pass

    def startIO(self):
        """
        main loop of os
        :return:
        """
        self.goOn=True
        count=0
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


            # connect or reconnect to host :
            if self.connectedToHost==False and count %20 == 0:
                self.cth()

            count+=1
            sleep(0.25)



    def writeText(self,text,line):
        # LCD screen if connected
        pass

