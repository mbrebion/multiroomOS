__author__ = 'mbrebion'


from config import name
import signal
from io_mr import Io
from menu import Menu
import system
from libraries.constants import MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_ORDER,MSG_REFRESH,MSG_SUBSCRIBE,MSG_UNSUBSCRIBE
from libraries.constants import MODE_BTSTREAM,MODE_LOCAL,MODE_SNAPSTREAM_IN,ORDER_SSTOP,ORDER_STOP,ORDER_SSYNC,MODE_SNAPSTREAM_OUT
from threading import Lock
from uuid import getnode as get_mac

class Os(object):

    def __init__(self):

        self.askedExit=False
        self.lastOrder=0
        self.lock=Lock()
        self.cdInside=False
        mac = get_mac()
        self.macAdrr=':'.join(("%012x" % mac)[i:i+2] for i in range(0, 12, 2))

        #settings :
        system.openShelf()

        # starting sevices (order is important)
        self.menu = Menu(self)
        self.io = Io(self)
        self.initMPD()


    def run(self):
        self.io.mainLoop() # main os loop


    def initMPD(self):


        system.switchToLocalOutput()
        system.startCommand("mpc clear")  # clear last mpd playlist
        system.startCommand("mpc stop")
        try:
            self.volume = system.getDataFromShelf("MPDVolume")
            print("found volume " ,self.volume)
        except:
            self.volume=85
            print("default volume ", self.volume)

        self.changeMode(MODE_LOCAL)
        system.startCommand("mpc update")

    def takeAction(self, action, value, source=name):
        """
        can be called by different means (and threads)
        :param action: kind of action to take
        :param value: parameter associated with the action asked
        :param source: remote which sent the order
        :return: nothing
        """
        with self.lock:
            self.io.askBacklight()

            if action == MSG_VOL:
                self.askNewVolume(value)

            elif action == MSG_MENU:
                self.askScrollMenu(value)

            elif action == MSG_SELECT:
                self.askSelect(value)

            elif action == MSG_BACK:
                self.askBack(value)

            elif action == MSG_BUTTON:
                self.askButtonAction(value)

            elif action == MSG_ORDER:
                self.askedOrder(value, source)

            elif action == MSG_REFRESH:
                self.askRefresh(value)

            elif action == MSG_SUBSCRIBE:
                self.io.appendRemoteControls(source)

            elif action == MSG_UNSUBSCRIBE:
                if source in self.io.remoteControls:
                    self.io.removeRemoteControls(source)

    def askedOrder(self, value, source):
        """
        function called when specific order are received from remotes
        :param value: the kind of order received
        :param source: the remote which sent the order
        :return: nothing
        """
        if value == ORDER_SSYNC:
            system.startSnapClient()
            self.streamSource=source
            self.io.sendMessageTo(MSG_SUBSCRIBE+","+str(0),source)
            self.changeMode(MODE_SNAPSTREAM_IN)
            return

        if value == ORDER_SSTOP:
            system.stopSnapClient()
            self.streamSource = None
            self.io.sendMessageTo(MSG_UNSUBSCRIBE + "," + str(0),source)
            self.changeMode(MODE_LOCAL)
            return

        if value == ORDER_STOP:
            self.askBack(1) # we can maybe do better no ?

    def askButtonAction(self,value):
        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:

            if value == 1:
                """
                mpd content in every room (snapcast)
                """

                if self.mode == MODE_LOCAL:
                    system.switchToSnapCastOutput()
                    system.startSnapClient()
                    self.io.sendMessageToAll(MSG_ORDER+","+str(ORDER_SSYNC));
                    self.lastOrder=ORDER_SSYNC
                    self.streamSource=name
                    self.changeMode(MODE_SNAPSTREAM_OUT)

                elif self.mode == MODE_SNAPSTREAM_OUT:
                    self.io.sendMessageToAll(MSG_ORDER+","+str(ORDER_SSTOP));
                    self.lastOrder=ORDER_SSTOP
                    system.stopSnapClient()
                    system.switchToLocalOutput()
                    self.changeMode(MODE_LOCAL)

            elif value == 2:
                # mute other devices
                self.io.sendMessageToAll(MSG_ORDER + "," + str(ORDER_STOP));

            elif value == 3:
                self.menu.forceRadio()

            elif value == 4:
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
        if self.mode==MODE_SNAPSTREAM_IN:
            self.io.nUDP.sendMSG(MSG_MENU + "," + str(dec), dest=self.streamSource)

        self.menu.askRefreshFromOutside()

    def askSelect(self,value):
        self.menu.select()

        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:
            self.menu.askRefreshFromOutside()

        if self.mode==MODE_SNAPSTREAM_IN:
            self.io.nUDP.sendMSG(MSG_SELECT + "," + str(0), dest=self.streamSource)

    def askBack(self,value):

        if self.mode==MODE_BTSTREAM:
            system.killBluetoothStream()

        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:
            self.menu.back()

        if self.mode==MODE_SNAPSTREAM_IN:
            system.stopSnapClient()
            self.io.sendMessageTo(MSG_UNSUBSCRIBE + "," + str(0), self.streamSource)
            self.streamSource = None
            self.changeMode(MODE_LOCAL)

            # must be done automatically as it is the case for bt ; we can check for the existence of a snapclient alive for instance
            #TODO : we must advertize the device which broadcast so that if there is no more listener, it can stop broadcasting
            # to be done with json rpc messages (via telnet scripts maybe)

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

        # if still here, it means we must modify the volume
        # constants
        minVol=0
        maxVol=100

        maxDec=18
        ndec = max(min(maxDec,dec*2),-maxDec)
        self.volume = min(maxVol,max(minVol,self.volume +  ndec))
        self.io.writeText(" Vol : " +str(self.volume),4)

        """
        if kind==BIG :
            system.startCommand("amixer -c 0 -q -- set Digital "+str(self.volume)+"dB")
        else :
            # this hack is because hifiberry mini amp does not have a proper hardware mixer ; I would prefer a better and simpler solution !
            if self.mode == MODE_SNAPSTREAM_IN or self.mode == MODE_SNAPSTREAM_OUT:
                system.startCommand("mpc volume 70" ) # default volume : to be changed
                system.startCommand("bash /home/pi/os/scripts/setSnapVolume.sh "+self.macAdrr+" "+str(100 + 2 * newVol))       ############### to be changed !!! it is not only piMain who streams
            else:
                system.startCommand("mpc volume " + str(100 + 2 * newVol))
        """
        if self.mode == MODE_SNAPSTREAM_IN or self.mode == MODE_SNAPSTREAM_OUT:
            # it means that we are streaming or receiving stream
            system.startCommand("mpc volume 100")
            # in this case, mpd is put at max and we thus modify snapclient volume with the following awfull bash script
            realVol=self.mpcToSnapVolumConvert(self.volume)
            system.startCommand("bash /home/pi/os/scripts/setSnapVolume.sh " + self.macAdrr +" " + self.streamSource + " " + str(realVol))   ############### te be changed !!! it is not only piMain who streams
        else:
            # here, we directly modify mpd volume
            system.startCommand("mpc volume " + str(self.volume))

    def mpcToSnapVolumConvert(self,volIn):
        """
        same level in snapclient and mpd does not produce same sound level
        This function (found experimentally) maps mpc ratio (in [0,100]) into snapcast ratio (in [0,100])

        4   -> 1
        10  -> 3
        20  -> 7
        30  -> 13
        60  -> 40
        76  -> 62
        100 -> 100
        :return:
        """
        return 100*(volIn/100)**1.68


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
            # in snapstream mode : view is a copy of the host
            #self.io.writeText("SnapCast playing",1)
            #self.io.writeText("- back to stop -",2)
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
        self.askNewVolume(0) # update volume (mpd/snapclient)



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


    def safeStop(self):
        self.io.writeText("Exiting", 1)
        self.io.closeIO()
        system.startCommand("mpc stop")
        system.startCommand("mpc clear")
        system.closeShelf()
        print("finished safely")



################ Launching app and dealing with sigterm, control-c


def sigterm_handler(signal, frame):
    # save the state here or do whatever you want
    print('kill signal received, closing nicely')
    os.io.endLoop()

signal.signal(signal.SIGTERM, sigterm_handler)

# start os !
global os
os = Os()
try:
    os.run()
except KeyboardInterrupt:
    print("keyboard interrupt asked")
finally:
    os.safeStop()















