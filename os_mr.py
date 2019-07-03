__author__ = 'mbrebion'


from config import name
import signal
from io_mr import Io,sep
from menu import Menu
from libraries import system
import datetime,pytz
import time
from libraries.constants import MSG_BUTTON,MSG_BACK,MSG_MENU,MSG_SELECT,MSG_VOL,MSG_ORDER,MSG_REFRESH,MSG_SUBSCRIBE,MSG_UNSUBSCRIBE,ASK_ISPLAYING,ASW_FALSE,ASW_TRUE
from libraries.constants import MODE_BTSTREAM,MODE_LOCAL,MODE_SNAPSTREAM_IN,ORDER_SSTOP,ORDER_STOP,ORDER_SSYNC,MODE_SNAPSTREAM_OUT,ORDER_STARTEMIT,MSG_ASK
from threading import Lock
from uuid import getnode as get_mac
import random


shutdown=False
tz=pytz.timezone('Europe/Paris')

class Os(object):

    def __init__(self):

        self.askedExit=False
        self.lastOrder=0
        self.lock=Lock()
        self.cdInside=False
        self.minuteStop=random.randint(1,29)
        mac = get_mac()
        self.macAdrr=':'.join(("%012x" % mac)[i:i+2] for i in range(0, 12, 2))

        #settings :
        system.openShelf()

        # starting sevices (order is important)
        self.menu = Menu(self)
        self.io = Io(self)
        self.initMPD()

    def run(self):
        self.markTime()
        self.markFirstTime()

        self.io.mainLoop() # main os loop

    def setCDInside(self,bool):
        if bool!=self.cdInside:
            self.cdInside=bool
            self.updateView()

    def initMPD(self):

        system.switchToLocalOutput()

        try:
            self.volume = system.getDataFromShelf("MPDVolume")
            system.logDebug("found volume ", self.volume)
        except:
            self.volume = 85
            system.logDebug("default volume ", self.volume)

        self.changeMode(MODE_LOCAL)
        system.startCommand("mpc update")
        system.startCommand("mpc clear")  # clear last mpd playlist
        system.startCommand("mpc stop")

    def markFirstTime(self):
        self.firstTime = time.time()

    def markTime(self):
        self.lastActionTime = time.time()

    def ellapsedTimeSinceLastAction(self):
        return time.time()-self.lastActionTime

    def ellapsedTotalTime(self):
        return time.time()-self.firstTime

    def considerStoppingRebooting(self):
        now = datetime.datetime.now(tz=tz)
        restartTimes=[17]
        minimalInactivity=0 # half an hour
        minimalOperationalTime=90

        if self.ellapsedTimeSinceLastAction()<minimalInactivity or self.ellapsedTotalTime() < minimalOperationalTime or system.isMPDPlaying() or self.mode==MODE_SNAPSTREAM_IN:
            return

        for time in restartTimes:
            if now.hour == time and now.minute>= 42+ 0*self.minuteStop  :
                print("exiting at ",now.hour,":",now.minute)
                self._safeStop()

    def takeAction(self, action, value, source=name):
        """
    can be called by different means (and threads)
    :param action: kind of action to take
    :param value: parameter associated with the action asked
    :param source: remote which sent the order
    :return: nothing
    """
        with self.lock:

            self.markTime()
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

        self.markTime()
        if value == ORDER_STARTEMIT:
            if self.mode==MODE_LOCAL:
                system.logDebug("asked to start streaming music")
                self.startOutputtingToSnapCast()
            return


        if value == ORDER_SSYNC:
            if self.mode==MODE_LOCAL:
                self.startListeningToSnapCast(source)
            return

        if value == ORDER_SSTOP:
            if self.mode==MODE_SNAPSTREAM_IN:
                self.stopListeningToSnapCast()
            return

        if value == ORDER_STOP:
            if self.mode==MODE_SNAPSTREAM_OUT:
                system.logDebug("       asked to stop streaming")
                self.stopOutputtingToSnapCast()

            if self.mode==MODE_SNAPSTREAM_IN:
                system.logDebug("       asked to stop listening")
                self.stopListeningToSnapCast()

            if system.isMPDPlaying():
                self.askBack(1) # we can maybe do better no ?

    def stopListeningToSnapCast(self):
        system.stopSnapClient()
        self.io.sendMessageTo(MSG_UNSUBSCRIBE + sep + str(0), self.streamSource)
        self.streamSource = None
        self.changeMode(MODE_LOCAL)

    def startListeningToSnapCast(self, source):
        system.mpcStop()
        system.startSnapClient()
        self.streamSource = source
        self.io.sendMessageTo(MSG_SUBSCRIBE + sep + str(0), source)
        self.changeMode(MODE_SNAPSTREAM_IN)

    def stopOutputtingToSnapCast(self):
        self.io.sendMessageToAll(MSG_ORDER + sep + str(ORDER_SSTOP));
        self.lastOrder = ORDER_SSTOP
        self.streamSource = None
        system.stopSnapClient()
        system.switchToLocalOutput()
        self.changeMode(MODE_LOCAL)

    def startOutputtingToSnapCast(self):
        system.switchToSnapCastOutput()
        system.startSnapClient()
        self.io.sendMessageToAll(MSG_ORDER + sep + str(ORDER_SSYNC));
        self.lastOrder = ORDER_SSYNC
        self.streamSource = name
        self.changeMode(MODE_SNAPSTREAM_OUT)

    def askButtonAction(self, value):
        if self.mode == MODE_LOCAL or MODE_SNAPSTREAM_OUT:
            system.logDebug("ask button called : ", value)

            if value == 1:
                """
                mpd content in every room (snapcast)
                """

                if self.mode == MODE_LOCAL:
                    #
                    if system.isMPDPlaying():
                        # if local music is played
                        self.startOutputtingToSnapCast()
                    else:
                        # if no local music is played, we check wether other remotes play music
                        dest = []
                        for d in self.io.remoteNames:
                            if "local" not in d:
                                # this prevent remotes controls with name in xxx.local
                                dest.append(d)

                        for remote, answer in self.io.askMessageTo(MSG_ASK + sep + ASK_ISPLAYING, dest).items():

                            if answer == ASW_TRUE:
                                # we sync to the first remote which plays music
                                system.logDebug("starting listening to " + remote)
                                self.io.sendMessageTo(MSG_ORDER + sep + str(ORDER_STARTEMIT), remote);
                                self.startListeningToSnapCast(remote)
                                break

                        system.logDebug("")

                elif self.mode == MODE_SNAPSTREAM_OUT:
                    self.stopOutputtingToSnapCast()

                elif self.mode == MODE_SNAPSTREAM_IN:
                    self.stopListeningToSnapCast()

            elif value == 2:
                # mute other devices and stop snapcast if needed
                self.io.sendMessageToAll(MSG_ORDER + sep + str(ORDER_STOP));

            elif value == 3:
                self.menu.forceRadio()

            elif value == 4:
                global shutdown

                if shutdown :
                    self.io.goOn = False

                shutdown = True

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
            self.io.sendMessageTo(MSG_MENU +sep + str(dec), self.streamSource)

        self.menu.askRefreshFromOutside()

    def askSelect(self,value):
        self.menu.select()

        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:
            self.menu.askRefreshFromOutside()

        if self.mode==MODE_SNAPSTREAM_IN:
            self.io.sendMSGto(MSG_SELECT + sep + str(0), self.streamSource)

    def askBack(self,value):

        if self.mode==MODE_BTSTREAM:
            system.killBluetoothStream()

        if self.mode==MODE_LOCAL or MODE_SNAPSTREAM_OUT:
            self.menu.back()

        if self.mode==MODE_SNAPSTREAM_IN:
            self.io.sendMessageTo(MSG_BACK + sep + str(0), self.streamSource)

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
            system.mpcVolume(100)
            # in this case, mpd is put at max and we thus modify snapclient volume with the following awfull bash script
            realVol=self.mpcToSnapVolumConvert(self.volume)
            system.startCommand("bash /home/pi/os/scripts/setSnapVolume.sh " + self.macAdrr + " " + self.streamSource + " " + str(realVol))   ############### te be changed !!! it is not only piMain who streams
        else:
            # here, we directly modify mpd volume
            system.mpcVolume(self.volume)

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


            if self.mode==MODE_SNAPSTREAM_OUT:
                self.io.writeText("^ "+menu,1)
            else:
                self.io.writeText(menu,1)

            self.io.writeText(choice,2)
            self.io.writeText(choiceTwo,3)
            return

    def refreshView(self):
        """
        refresh the view if any changes has occurred
        :return: nothing
        """
        if self.menu.requireRefresh():
            self.updateView()
            return True
        return False

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
                        system.restartWifi(self.io)
                except:
                    pass

    def _safeStop(self,shutdown=False):
        """
        This function should never be called directelly. The programm might be stopped by ending the main io loop : io.goOn=False
        :param shutdown:
        :return:
        """
        system.logInfo("finishing")
        self.io.writeText("Exiting", 1)
        system.startCommand("mpc stop")
        system.startCommand("mpc clear")
        self.io.closeIO()
        system.closeShelf()
        self.io.writeText("power off", 1)
        system.logInfo("finished safely")
        if shutdown:
            system.startCommand("sudo reboot")


################ Launching app and dealing with sigterm, control-c

def sigterm_handler(signal, frame):
    # save the state here or do whatever you want
    os.io.goOn=False

signal.signal(signal.SIGTERM, sigterm_handler)

# start os !
global os
os = Os()
try:
    os.run()
except KeyboardInterrupt:
    print("received keyboard interrupt, exiting")
    pass

finally :
    os._safeStop(shutdown)
















