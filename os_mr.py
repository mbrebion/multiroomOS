__author__ = 'mbrebion'


from config import server
from io_mr import Io
from menu import Menu
import system
from libraries.constants import MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_PRINT,MSG_ORDER,MSG_REFRESH,MSG_PROPAGATE_ORDER
from libraries.constants import MODE_BTSTREAM,MODE_LOCAL,MODE_SNAPSTREAM_IN,ORDER_SSTOP,ORDER_STOP,ORDER_SSYNC,MODE_SNAPSTREAM_OUT
from threading import Lock

class Os(object):

    def __init__(self):

        # constants
        self.minVol=-50
        self.maxVol=0
        self.volume=-15

        self.askedExit=False
        self.lastOrder=0
        self.lock=Lock()
        self.cdInside=False



        #settings :
        system.openShelf()


        self.menu=Menu(self)
        self.io=Io(self)

        #self.askNewVolume(-1)
        self.changeMode(MODE_LOCAL)
        # never ending loop

        system.startCommand("mpc clear") # clear last mpd playlist
        system.startCommand("mpc update")
        system.switchToLocalOutput()


        self.io.mainLoop() # main os thread
        system.closeShelf()


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

            if message==MSG_PROPAGATE_ORDER:
                self.propagateOrder(value)



    def connectionLost(self):
        self.io.connectedToHost=False


    def askOrder(self,value):
        if value==ORDER_SSYNC:
            if server:
                system.startSnapClient()
            else:
                system.startSnapClientSimple()

            self.changeMode(MODE_SNAPSTREAM_IN)
            return


        if value==ORDER_SSTOP:
            system.stopSnapClient()
            self.changeMode(MODE_LOCAL)
            return

        if value == ORDER_STOP:
            self.askBack(1)
            self.askOrder(ORDER_SSTOP)



    def askPrint(sel,value):
        print value

    def askButtonAction(self,value):
        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:

            if value==1 :
                """
                mpd content in every room
                """

                if self.lastOrder != ORDER_SSYNC:
                    print "start syncing"
                    system.switchToSnapCastOutput()
                    self.changeMode(MODE_SNAPSTREAM_OUT)

                    system.startSnapClient()
                    self.io.sendMessageToAll(MSG_ORDER+","+str(ORDER_SSYNC));
                    self.lastOrder=ORDER_SSYNC

                else :
                    print "stop syncing"
                    self.io.sendMessageToAll(MSG_ORDER+","+str(ORDER_SSTOP));
                    self.lastOrder=ORDER_SSTOP
                    self.changeMode(MODE_LOCAL)
                    system.stopSnapClient()
                    system.switchToLocalOutput()


            if value==2 :
                # clear other devices
                self.io.sendMessageToAll(MSG_ORDER + "," + str(ORDER_STOP));

            if value==3 :
                self.menu.forceRadio()

            if value==4 :
                pass



    def askRefresh(self,value):
        """
        re-send all text lines to every one (local devices + remotes controls)
        :return: nothing
        """
        self.io.askResendTexts()

    def askScrollMenu(self,dec):

        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:
            if dec>0:
                self.menu.next(dec)
            else :
                self.menu.previous(dec)

        self.menu.askRefreshFromOutside()

    def askSelect(self,value):
        self.menu.select()

        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:
            self.menu.askRefreshFromOutside()

    def askBack(self,value):

        if self.mode==MODE_BTSTREAM:
            system.killBluetoothStream()

        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:
            self.menu.back()

        if self.mode==MODE_SNAPSTREAM_IN:
            system.stopSnapClient()
            self.mode=MODE_LOCAL # must be done automatically as it is the case for bt ; we can check for the existence of a snapclient alive for instance
            #TODO : we must advertize the device which broadcast so that if there is no more listener, it can stop broadcasting


        self.menu.askRefreshFromOutside()

    def askNewVolume(self,dec):
        """ must be changed to fulfill with updateView patern asked from main thread in update is required
        :param dec:
        :return:
        """
        "if current submenu is a setting menu ; this control is used to modify the property"
        if self.menu.isSettingShown() and self.mode==MODE_LOCAL:
            self.menu.currentSub.subMenuShown().update(dec)
            return

        try :
            ndec = max(min(12,dec),-12)
            newVol = min(self.maxVol,max(self.minVol,self.volume +  ndec))
            self.io.writeText(" Vol : " +str( newVol)+"dB",4)
            self.volume=newVol

            if server :
                system.startCommand("amixer -c 0 -q -- set Digital "+str(newVol)+"dB")
            else :
                # this hack is because hifiberry mini amp does not have a proper hardware mixer ; I would prefer a better and simpler solution !
                system.startCommand("mpc volume "+str(100+2*newVol))
                system.startCommand("amixer -- sset 'Master' "+ str(100+2*newVol)+"%")

        except:
            pass


######## - ######

    def updateView(self):
        """
        outputs texts according to display state
        :return:
        """

        if self.mode==MODE_BTSTREAM:
            self.io.writeText("BT playing",1)
            self.io.writeText("- back to stop -",2)
            return

        if self.mode==MODE_SNAPSTREAM_IN:
            self.io.writeText("SnapCast playing",1)
            self.io.writeText("- back to stop -",2)
            return

        if self.mode==MODE_LOCAL or self.mode==MODE_SNAPSTREAM_OUT:
            menu,choice,choiceTwo = self.menu.info()

            if menu!="":
                if self.mode==MODE_SNAPSTREAM_OUT:
                    self.io.writeText("* "+menu,1)
                else:
                    self.io.writeText(menu,1)
            if choice!="":
                self.io.writeText(choice,2)
            if choice!="":
                self.io.writeText(choiceTwo,3)
            return

    def safeStop(self):
        self.io.goOn=False
        system.startCommand("mpc stop")
        system.startCommand("mpc clear")
        self.io.writeText("Exiting", 1)
        system.closeShelf()
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


    def changeMode(self, newMode):
        self.mode=newMode
        self.menu.askRefreshFromOutside()
        self.io.askBacklight()



    def dealWithBluetoothCon(self):
        """
        If autodisablewifionbt is set to True, ths os detects when music is streamed from bluetooth and can switch off wifi to ease signal reception.
        In addiation, a text message is displayed (before wifi's off) to advert listeners
        :return: nothing
        """
        if system.isBluetoothDevicePlaying():
            if not self.mode==MODE_BTSTREAM:
                self.menu.askRefreshFromOutside()
                self.changeMode(MODE_BTSTREAM)
                try:
                    if system.getDataFromShelf("WifiAuto"):
                        system.shutdownWifi()
                except:
                    pass
        else:
            if self.mode==MODE_BTSTREAM:
                self.menu.askRefreshFromOutside()
                self.changeMode(MODE_LOCAL)
                try :
                    if system.getDataFromShelf("WifiAuto"):
                        system.restartWifi()
                except:
                    pass



# start os !
global os
os=Os()















