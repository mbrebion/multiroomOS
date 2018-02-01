__author__ = 'mbrebion'


from io_mr import Io,MSG_VOL,MSG_WIFI,MSG_MENU,MSG_BACK,MSG_SELECT
from menu import Menu
import os as osys


class Os(object):

    def __init__(self):

        # constants
        self.minVol=-48
        self.maxVol=0
        self.volume=-5
        self.wifiEnabled=True

        self.io=Io(self)
        self.askNewVolume(-1)
        self.menu=Menu()

        # never ending loop
        try:
            self.io.startIO()
        finally:
            Menu.clearProcesses()



    def takeAction(self,message,value):
        if message==MSG_WIFI:
            self.changeWifiState()

        if message==MSG_VOL:
            self.askNewVolume(value)

        if message==MSG_MENU:
            self.askScrollMenu(value)

        if message==MSG_SELECT:
            self.askSelect(value)

        if message==MSG_BACK:
            self.askBack(value)




    def changeWifiState(self):
        if self.wifiEnabled:
            pass
            #osys.system('sudo /sbin/ifconfig wlan0 down')
        else :
            pass
            #osys.system('sudo /sbin/ifconfig wlan0 up')

        self.wifiEnabled = not self.wifiEnabled
        self.io.writeText(" wifi  : " +str( self.wifiEnabled),1)


    # interact with menu
    def updateView(self):
        menu,choice = self.menu.info()
        if menu!="":
            self.io.writeText(menu,1)
        if choice!="":
            self.io.writeText(choice,2)

    def askScrollMenu(self,dec):
        if dec>0:
            self.menu.next()
        else :
            self.menu.previous()
        self.updateView()


    def askSelect(self,value):
        self.menu.select()
        self.updateView()

    def askBack(self,value):
        self.menu.back()
        self.updateView()



    def askNewVolume(self,dec):

        ndec = max(min(6,dec*abs(dec)),-6)
        newVol = min(self.maxVol,max(self.minVol,self.volume +  ndec))
        self.io.writeText("Volume : " +str( newVol)+"dB",2)
        self.volume=newVol
        osys.system("amixer -c 0 -q -- set Digital "+str(newVol)+"dB")





os=Os()