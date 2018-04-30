__author__ = 'mbrebion'


from config import simple
if simple:
    from simpleIO_mr import SimpleIo
    from simpleMenu import SimpleMenu
else:
    from io_mr import Io
    from menu import Menu

import system
from libraries.constants import MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_PRINT,MSG_ORDER,MSG_REFRESH
from threading import Lock

class Os(object):

    def __init__(self):

        # constants
        self.minVol=-48
        self.maxVol=0
        self.volume=-15
        self.wifiEnabled=True
        self.askedExit=False
        self.lastOrder=0
        self.lock=Lock()


        if simple:
            self.menu=SimpleMenu()
            self.io=SimpleIo(self)

        else:
            self.menu=Menu()
            self.io=Io(self)

        self.askNewVolume(-1)
        # never ending loop

        system.startCommand("mpc clear") # clear last mpd playlist
        system.startCommand("mpc update")
        system.switchToLocalOutput()
        self.io.mainLoop() # main os thread

        if simple==False:
            Menu.clearProcesses()

    def takeAction(self,message,value):
        """
        can be called by different means (and threads)
        :param message: kind of action to take
        :param value: parameter associated with the action asked
        :return: nothing
        """
        with self.lock:
            self.io.askBacklight()

            if message == MSG_VOL:
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

            if message==MSG_REFRESH:
                self.askRefresh(value)

    def connectionLost(self):
        self.io.connectedToHost=False

    def askOrder(self,value):
        if value==25:
            self.menu.syncToSnapServer()
        if value==26:
            self.menu.stopSyncing()

    def askPrint(sel,value):
        print value

    def askButtonAction(self,value):
        print value

        if value==1 :
            """
            mpd content in every room
            """
            syncOrder=25
            endSyncOrder=26

            if self.lastOrder!=syncOrder:
                order=syncOrder
                system.switchToSnapCastOutput()
                self.menu.syncToSnapServer()
                self.io.tcpServer.sendToAllDevices(MSG_ORDER+","+str(order));
                self.lastOrder=order

            else :
                order=endSyncOrder
                self.io.tcpServer.sendToAllDevices(MSG_ORDER+","+str(order));
                self.lastOrder=order
                self.menu.stopSyncing()
                system.switchToLocalOutput()


        if value==2 :
            if self.askedExit:
                self.safeStop()
            else:
                self.io.writeText("Shutdown ? (Y-2,N-4)",4)
                self.askedExit=True



        if value==4 :
            if self.askedExit==True:
                self.askNewVolume(0)
                self.askedExit=False
            else :
                self.io.resetScreen()

    def askRefresh(self,value):
        """
        re-send all text lines to every one (local devices + remotes controls)
        :return: nothing
        """
        self.io.askResendTexts()

    def askScrollMenu(self,dec):
        if dec>0:
            self.menu.next(dec)
        else :
            self.menu.previous(dec)
        self.menu.askRefreshFromOutside()

    def askSelect(self,value):
        self.menu.select()
        self.menu.askRefreshFromOutside()

    def askBack(self,value):
        self.menu.back()
        self.menu.askRefreshFromOutside()

    def askNewVolume(self,dec):
        """ must be changed to fulfill with updateView patern asked from main thread in update is required
        :param dec:
        :return:
        """
        try :
            ndec = max(min(12,dec),-12)
            newVol = min(self.maxVol,max(self.minVol,self.volume +  ndec))
            self.io.writeText(" Vol : " +str( newVol)+"dB",4)
            self.volume=newVol
            system.startCommand("amixer -c 0 -q -- set Digital "+str(newVol)+"dB")
        except:
            pass


######## - ######

    def updateView(self):
        menu,choice,choiceTwo = self.menu.info()
        if menu!="":
            self.io.writeText(menu,1)
        if choice!="":
            self.io.writeText(choice,2)
        if choice!="":
            self.io.writeText(choiceTwo,3)

    def safeStop(self):
        self.io.goOn=False
        system.startCommand("mpc stop")
        system.startCommand("mpc clear")
        self.io.writeText("Exiting", 1)
        system.shutdownPi()

    def checkStopAsked(self):
        if system.isFile("/home/pi/os/.stop"):
            system.startCommand("rm /home/pi/os/.stop")
            self.safeStop()

    def refreshView(self):
        """
        refresh the view if any changes has occurred with mpd
        :return: nothing
        """
        if self.menu.requireRefresh():
            self.updateView()





# start os !
os=Os()
