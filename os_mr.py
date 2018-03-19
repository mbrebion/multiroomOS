__author__ = 'mbrebion'


from io_mr import Io,MSG_VOL,MSG_WIFI,MSG_MENU,MSG_BACK,MSG_SELECT,MSG_BUTTON
from simpleIO_mr import SimpleIo
from menu import Menu
from simpleMenu import SimpleMenu
from config import simple
import system


class Os(object):

    def __init__(self):

        # constants
        self.minVol=-48
        self.maxVol=0
        self.volume=-11
        self.wifiEnabled=True


        if simple:
            self.menu=SimpleMenu()
            self.io=SimpleIo(self)

        else:
            self.menu=Menu()
            self.io=Io(self)

        self.askNewVolume(-1)
        # never ending loop
        try:
            system.startCommand("mpc clear") # clear last mpd playlist
            system.startCommand("mpc update")
            self.io.startIO()
        finally:
            Menu.clearProcesses()


    def takeAction(self,message,value):
        if message==MSG_WIFI:
            pass

        if message==MSG_VOL:
            self.askNewVolume(value)

        if message==MSG_MENU:
            self.askScrollMenu(value)

        if message==MSG_SELECT:
            self.askSelect(value)

        if message==MSG_BACK:
            self.askBack(value)

        if message==MSG_BUTTON:
            self.askButtonAction(value)



    def askButtonAction(self,value):
        if value==1 :
            print "button1"

        if value==2 :
            print "button2"

        if value==3 :
            print "button3"

        if value==4 :
            print "button4"


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


    def checkStopAsked(self):
        if system.isFile("/home/pi/os/.stop"):
            self.io.goOn=False
            system.startCommand("mpc stop")
            system.startCommand("mpc clear")
            system.startCommand("rm /home/pi/os/.stop")
            self.io.writeText("Exiting", 1)



    def askNewVolume(self,dec):
        try :
            ndec = max(min(12,dec),-12)
            newVol = min(self.maxVol,max(self.minVol,self.volume +  ndec))
            self.io.writeText("  Volume : " +str( newVol)+"dB",4)
            self.volume=newVol
            system.startCommand("amixer -c 0 -q -- set Digital "+str(newVol)+"dB")
        except:
            pass



os=Os()