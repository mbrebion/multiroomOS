__author__ = 'mbrebion'


from config import simple

if simple:
    print "simple system selected"
    from simpleIO_mr import SimpleIo
    from simpleMenu import SimpleMenu
else:
    print "main system selected"
    from io_mr import Io
    from menu import Menu

import system
from libraries.constants import MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_WIFI,MSG_PRINT,MSG_ORDER


class Os(object):

    def __init__(self):

        # constants
        self.minVol=-48
        self.maxVol=0
        self.volume=-11
        self.wifiEnabled=True
        self.askExit=False
        self.lastOrder=0


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
            if simple==False:
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

        if message==MSG_PRINT:
            self.askPrint(value)

        if message==MSG_ORDER:
            self.askOrder(value)


        self.io.askBacklight()


    def connectionLost(self):
        self.io.connectedToHost=False


    def askOrder(self,value):
        if value==25:
            self.menu.outsideRadioAsk()
        if value==26:
            self.menu.clearMPD()


    def askPrint(sel,value):
        print value


    def askButtonAction(self,value):
        if value==1 :
            """
            radio in every room
            """
            radioOrder=25
            clearOrder=26
            if self.lastOrder!=radioOrder:
                order=radioOrder
                self.io.tcpServer.sendToAllDevices(MSG_ORDER+","+str(order));
                self.lastOrder=order
                system.sleep(0.1)
                self.menu.outsideRadioAsk()
            else :
                order=clearOrder
                self.io.tcpServer.sendToAllDevices(MSG_ORDER+","+str(order));
                self.lastOrder=order
                self.menu.clearMPD()



        if value==2 :
            self.askExit = not self.askExit
            if self.askExit:
                self.io.writeText("Shutdown ? (Y-3,N-4)",4)
            else:
                self.askNewVolume(0)

        if value==3 :
            if self.askExit==True:
                system.startCommand("sudo sleep 3 ; sudo shutdown now")
                self.safeStop()


        if value==4 :
            if self.askExit==True:
                self.askNewVolume(0)
                self.askExit=False



    def refreshView(self):
        if self.menu.requireRefresh():
            self.updateView()

    # interact with menu
    def updateView(self):
        menu,choice,choiceTwo = self.menu.info()
        if menu!="":
            self.io.writeText(menu,1)
        if choice!="":
            self.io.writeText(choice,2)
        if choice!="":
            self.io.writeText(choiceTwo,3)

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



    def safeStop(self):
        self.io.goOn=False
        system.startCommand("mpc stop")
        system.startCommand("mpc clear")
        self.io.writeText("Exiting", 1)

    def checkStopAsked(self):
        if system.isFile("/home/pi/os/.stop"):
            system.startCommand("rm /home/pi/os/.stop")
            self.safeStop()


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