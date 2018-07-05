__author__ = 'mbrebion'

import subprocess
from config import radios, entries
import system
from libraries.mpcHelper import MpcHelper
from config import lcdLines # dangerous, to be deleted# dangerous, to be deleted



#######################################
#######   Main menus classes    #######
#######################################

class SubMenu(object):
    processes=[]  # static var to store all the processes which must be killed on exit

    @staticmethod
    def clearProcesses():
        for p in SubMenu.processes:
            p.terminate()  # maybe dangerous if the process has been killed on his own or by someone else ; put a try except here
            returncode =p.wait()
        SubMenu.processes=[]

    def __init__(self,parent,name):
        self.name=name
        self.count = 0
        self.currentProc = False
        self.parent = parent
        self.list=[]

        self.actionTag=""
        self.actionTagTwo=""
        self.askRefresh=False # if set to true, a new refresh will be triggered at next io loop
        self.kind="menu"
        self.selectable=True

    def explorable(self):
        return len(self.list) != 0

    def subMenuShown(self):
        if len(self.list)==0:
            return self
        return self.list[self.count]

    def _next(self):
        self.count+=1
        if self.count>=len(self.list) :
            self.count=0
        self.list[self.count].onShowed()


    def _previous(self):
        self.count-=1
        if self.count<0 :
            self.count=len(self.list)-1
        self.list[self.count].onShowed()

    def onSelected(self):
        """
        called when item is selected
        :return: nothing
        """
        pass


    def getAncestorMenu(self):
        sub=self
        found=False
        while not found:
            print sub.name
            if sub.parent.name=="Menu":
                return sub.parent
            else :
                sub=sub.parent

    def onShowed(self):
        """
        function called when submenu shown from parent list but not yet selected
        :return:
        """
        pass

    def _select(self):
        if self.explorable() :
            self.list[self.count].onSelected()
            return self.list[self.count]
        else:
            self.onSelected()
            return False

    def _back(self):
        return self.parent

    def clearEntries(self):
        self.list=[] # clear previous list

    def addEntry(self,sub):
        self.list.append(sub)

class SubSetting(SubMenu):
    """
    this class defines a special kind of submenu dedicated to change settings
    these submenus can just be shown and not entered : they must display their attribute and can be modified with the volume rotary encoder
    """
    def __init__(self,parent,name,hint):
        SubMenu.__init__(self,parent,name)
        self.property=False # to be overriden
        self.hint=hint
        self.trueName=name
        self.actionTagTwo=hint
        self.kind="setting"
        self.selectable=False
        self.update(0)

    def _showProperty(self):
        """
        a string containing the property must be returned. Must be overiden.
        """
        pass

    def _modifyProperty(self,dec):
        """
        The property must be changed according to dec. Must be overiden.
        """
        pass

    def update(self,dec):
        self._modifyProperty(dec)
        out=self._showProperty()
        if lcdLines>2:
            self.actionTag= out
        else :
            self.name= self.trueName +" : "+  out

        self.parent.askRefresh=True

class Menu(SubMenu):

    def __init__(self,simple=False):
        SubMenu.__init__(self,self,"Menu")
        self.currentSub=self
        self.simple=simple
        self.configureEntries()



    def configureEntries(self):
        if "bt" in entries :
            self.addEntry(Bt(self))

        if "radios" in entries :
            self.radio=Radios(self)
            self.addEntry(self.radio)

        if "localMusic" in entries :
            self.addEntry(Music(self))

        if "alarm" in entries :
            self.alarm=Alarm(self)
            self.addEntry(self.alarm)

        if "cd" in entries :
            self.addEntry(CD(self))


    def getActiveAlarms(self):
        if "alarm" not in entries :
            return []
        else :
            return self.alarm.getActiveAlarms()



    ##########################################


    def next(self,dec=1):
        """
        this function is called when physical ROTARY encoder is turned + or when asked by remote control
        :return: Nothing
        """
        for i in range(dec):
            self.currentSub._next()

    def previous(self,dec=-1):
        """
        this function is called when physical ROTARY encoder is turned - or when asked by remote control
        :return: Nothing
        """
        for i in range(-dec):
            self.currentSub._previous()

    def askRefreshFromOutside(self):
        self.currentSub.askRefresh=True

    def requireRefresh(self):
        out = False
        if self.currentSub.askRefresh :
            out = True
            self.currentSub.askRefresh = False
        return out

    def info(self):
        # function use to provide output text
        if self.currentSub.explorable():
            return self.currentSub.name,self.currentSub.list[self.currentSub.count].name,self.currentSub.actionTagTwo
        else :
            return self.currentSub.name, self.currentSub.actionTag, self.currentSub.actionTagTwo

    def isSettingShown(self):
        return self.currentSub.subMenuShown().kind=="setting"

    def select(self):
        """
        this function is called when physical MENU button is pressed or when asked by remote control or by menu itself
        (for instance in the case of a single album in a artist submenu)
        :return: Nothing
        """
        save= self.currentSub._select()
        if save!=False and save.selectable == True:
            self.currentSub =save
            if save.explorable():
                try :
                    save.list[save.count].onShowed()
                except:
                    pass

    def forceRadio(self):
        """
        this force the radio menu : usefull for alarms
        :return: nothing
        """
        if "radios" in entries :
            self.currentSub=self.radio
            self.radio.list[0].onShowed()
            self.currentSub.askRefresh=True

    def back(self):
        """
        this function is called when physical VOLUME button is pressed or when asked by remote control
        :return: Nothing
        """

        self.currentSub = self.currentSub._back()
        self.currentSub[self.currentSub.count].onShowed()

#######################################
#########    Alarm  menus     #########
#######################################

class Alarm(SubMenu):
    def __init__(self,parent,name="Reveil"):
        SubMenu.__init__(self,parent,name)
        self.items=[]
        self.populate()
        print(self.list)

    def getActiveAlarms(self):
        out=[]
        for alarm in self.items:
            if alarm.enable :
                out.append(alarm)
        return out


    def addItem(self,item):
        self.items.append(item)

    def removeItem(self,item):
        self.items.remove(item)

    def populate(self):
        self.clearEntries()
        for item in self.items :
            self.addEntry(item)
        self.addEntry(NewAlarm(self))

class NewAlarm(SubMenu):
    def __init__(self,parent,name="ajout Reveil"):
        SubMenu.__init__(self,parent,name)
        self.th=TimeHour(self)
        self.tm=TimeMinute(self)
        self.addEntry(self.th)
        self.addEntry(self.tm)
        self.addEntry(CreateAlarm(self))

    def _back(self):
        self.parent.populate()
        return SubMenu._back(self)

class CreateAlarm(SubMenu):
    def __init__(self,parent,name="Ajouter"):
        SubMenu.__init__(self,parent,name)
        self.actionTag="Ajoutee"


    def onSelected(self):
        SubMenu.onSelected(self)
        item=AlarmItem(self.parent.parent,self.parent.th.property,self.parent.tm.property)
        self.parent.parent.addItem(item)


class TimeHour(SubSetting):
    def __init__(self,parent,name="Heure ", hint="selection heure"):
        SubSetting.__init__(self,parent,name,hint)
        self.property=7

    def _showProperty(self):
        if self.property<10:
            return "0"+str(self.property)
        else:
            return str(self.property)

    def _modifyProperty(self,dec):
        nh=self.property+dec
        if nh>23:
            nh = 0
        if nh<0:
            nh=23
        self.property=nh
        print nh

class TimeMinute(SubSetting):
    def __init__(self,parent,name="Minute", hint="selection minute"):
        SubSetting.__init__(self,parent,name,hint)
        self.property=0

    def _showProperty(self):
        if self.property<10:
            return "0"+str(self.property)
        else:
            return str(self.property)

    def _modifyProperty(self,dec):
        nh=self.property+dec
        if nh>59:
            nh = 0
        if nh<0:
            nh=59
        self.property=nh

class AlarmItem(SubMenu):
    def __init__(self,parent,hour,minute,name="heure : "):
        SubMenu.__init__(self,parent,name)
        self.hour=hour
        self.minute=minute
        self.enable=True
        self.reseted=True
        self.updateName()

    def updateName(self):
        if self.enable:
            oute="oui"
        else :
            oute="non"
        self.name = "a : " + str(self.hour)+":"+str(self.minute)+" " + oute


    def onSelected(self):
        self.enable != self.enable
        self.onShowed()
        self.askRefresh=True

#######################################
#########   BlueTooth menus   #########  to be deleted
#######################################

class Bt(SubMenu):
    def __init__(self,parent,name="Bluetooth"):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.actionTag="   Wifi Off"

    def onSelected(self):
        SubMenu.onSelected(self)
        print("set wifi off")
        system.startCommand('sudo /sbin/ifconfig wlan0 down')

    def _back(self):
        system.startCommand('sudo /sbin/ifconfig wlan0 up')
        return SubMenu._back(self)

#######################################
######### Local music menus   #########
#######################################


class Music(SubMenu):
    def __init__(self,parent,name="Local music"):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.addEntry(Artists(self))
        self.addEntry(PlayList(self))


class Artists(SubMenu):
    def __init__(self,parent,name="Artists"):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.populate()

    def populate(self):
        self.clearEntries()
        # add mpc update here ?
        output = subprocess.check_output("/usr/bin/mpc list AlbumArtist",shell=True)
        allArtists=output.split('\n')


        self.clearEntries()
        for name in allArtists:
            if name.strip("")!="":
                artist=Artist(self,name)
                self.addEntry(artist)

    def onSelected(self):
        SubMenu.onSelected(self)
        self.populate()
        # here, the artist menu is repopulated every time it is selected so that new artists can be retrieved


class Artist(SubMenu):
    def __init__(self,parent,name):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.populate()

    def populate(self):
        output = subprocess.check_output("/usr/bin/mpc list Album AlbumArtist \""+self.name+"\"",shell=True)
        allAlbums=output.split('\n')[0:-1] # this contains all artist which released at least an album !
        self.clearEntries()
        for name in allAlbums:
            album=Album(self,name)
            self.addEntry(album)

    def onSelected(self):
        SubMenu.onShowed(self)
        if len(self.list)==1 :
            # the artist has only one album so that the later can be already selected
            #self._select()
            pass

    def onShowed(self):
        if lcdLines>2 :
            self.parent.actionTagTwo = "  -- [" + str(self.parent.count+1)+"/"+str(len(self.parent.list)) +"] --"
        else :
            self.parent.name="Artists " + "[" + str(self.parent.count+1)+"/"+str(len(self.parent.list)) +"]"


class Album(SubMenu):
    def __init__(self,parent,name):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.play=False
        self.loaded=False


    def killHelper(self):
        if MpcHelper.exist :
            self.mpcH.shutDown()
            system.sleep(0.3)

    def resetHelper(self):
        self.killHelper() # kill helper if necessary
        self.mpcH=MpcHelper(self)


    def onSelected(self):
        SubMenu.onSelected(self)

        # if content is not yet loaded in mpc, mpc playlist is cleared and then content is loaded
        # mpc helper is also started

        if self.loaded==False :
            system.startCommand("mpc clear")
            cmd="mpc search Album  \""+self.name+"\" albumartist \""+ self.parent.name+ "\" | mpc add"
            system.startCommand(cmd)
            self.loaded=True
            self.resetHelper()


        if self.play:
            system.startCommand("mpc pause")
            self.mpcH.updateView()
            self.play=False
        else :
            system.startCommand("mpc play")
            self.mpcH.updateView()
            self.play = True


    def _next(self):
        system.startCommand("mpc next")
        self.mpcH.updateView()

    def _previous(self):
        system.startCommand("mpc prev")
        self.mpcH.updateView()

    def _back(self):
        system.startCommand("mpc stop")
        system.startCommand("mpc clear")
        self.play=False
        self.loaded=False
        self.killHelper()
        return SubMenu._back(self)

    def onShowed(self):
        self.parent.actionTagTwo = "  -- [" + str(self.parent.count+1)+"/"+str(len(self.parent.list)) +"] --"


class PlayList(SubMenu):
    def __init__(self,parent,name="Playlists"):
        SubMenu.__init__(self,parent,name)
        self.parent=parent


#######################################
#########     Radios menus    #########
#######################################

class Radios(SubMenu):
    def __init__(self,parent,name="Radios"):
        SubMenu.__init__(self,parent,name)

        for radio in radios:
            name=radio[0]
            webAddr=radio[1]
            self.addEntry(Radio(self,name,webAddr))

    def _back(self):
        system.startCommand("mpc clear")
        return SubMenu._back(self)

    def onSelected(self):
        SubMenu.onSelected(self)


class Radio(SubMenu):
    def __init__(self,parent,name,webAddr):
        SubMenu.__init__(self,parent,name)
        self.webAddr=webAddr
        self.actionTag="Listening"
        self.selectable=False


    def onShowed(self):
        SubMenu.onShowed(self)

        system.startCommand("mpc clear")
        system.startCommand("mpc add \""+self.webAddr+"\"" )
        system.startCommand("mpc play")


#######################################
########     Controls menus    ########
#######################################


class Settings(SubMenu):
    def __init__(self,parent,name="Reglages"):
        SubMenu.__init__(self,parent,name)
        self.addEntry(SettingsCD(self))
        self.addEntry(SettingsMPD(self))
        self.addEntry(SettingsWL(self))


class SettingsCD(SubMenu):
    def __init__(self,parent,name="Reglages CD"):
        SubMenu.__init__(self,parent,name)

class MagicMode(SubSetting):
    def __init__(self,parent,name="Magic Mode", hint="lecture silencieuse"):
        SubSetting.__init__(self,parent,name,hint)
        self.property=False



class SettingsMPD(SubMenu):
    def __init__(self,parent,name="Reglages MPD"):
        SubMenu.__init__(self,parent,name)

class SettingsWL(SubMenu):
    def __init__(self,parent,name="Reglages Wireless"):
        SubMenu.__init__(self,parent,name)

#######################################
##########     CDs menus    ###########
#######################################


class CD(SubMenu):
    def __init__(self,parent,name="Lecteur CD"):
        SubMenu.__init__(self,parent,name)
        self.addEntry(CDPlayer(self))
        self.addEntry(Eject(self))
        self.addEntry(Rip(self))
        self.upToDate = False
        self.inDB=False

    def onShowed(self):
        pass


class Rip(SubMenu):
    def __init__(self,parent,name="Ripping"):
        SubMenu.__init__(self,parent,name)
        self.selectable = False
        self.state=""

    def onSelected(self):
        if self.state=="":
            self.state="on duty"
            system.startCommand(" {abcde -N}& ")
        else:
            self.state=""
            system.startCommand(" pkill abcde ; pkill cdpara ")
        self.name="Ripping "+self.state




class Eject(SubMenu):
    def __init__(self,parent,name="Ejection"):
        SubMenu.__init__(self,parent,name)
        self.selectable = False

    def onSelected(self):
        system.startCommand("sudo eject")
        self.parent.upToDate = False

class CDPlayer(SubMenu):
    def __init__(self,parent,name="Lecture"):
        SubMenu.__init__(self,parent,name)
        self.cdName=""
        self.cdArtist=""
        self.tracksNB=0
        self.tracks=[]
        self.play=False
        self.loaded=False

    def onShowed(self):
        self.updateInfos()

    def _back(self):
        system.startCommand("mpc clear")
        self.loaded=False
        self.play=False
        self.killHelper()
        return SubMenu._back(self)


    def killHelper(self):
        if MpcHelper.exist :
            self.mpcH.shutDown()
            system.sleep(0.3)

    def resetHelper(self):
        self.killHelper() # kill helper if necessary
        self.mpcH=MpcHelper(self,self.tracks)

    def updateInfos(self):
        if not self.parent.upToDate:
            self.loaded=False
            try:
                output = system.startReturnCommand(" /usr/bin/cdcd tracks")
                self.cdName = output[0].split("name:")[1].lstrip(' ')
                self.cdArtist = output[1].split("artist:")[1].lstrip(' ')
                self.tracksNB=int(output[2].split("tracks:")[1].split("Disc")[0].lstrip(' '))
                self.name="CD : "+self.cdName
                self.getAncestorMenu().askRefresh=True
                self.output=output
                self.parent.upToDate=True
                self.parent.inDB=system.checkCDinDB(self.cdName,self.cdArtist)
                print "found : " +str(self.parent.inDB)
            except:
                pass



    def onSelected(self):
        SubMenu.onSelected(self)

        if not self.parent.upToDate :
            self.actionTagTwo="  not ready yet"
            return

        if self.loaded==False :
            output=self.output
            idec=6
            system.startCommand("mpc clear")
            self.tracks=[]
            for i in range(self.tracksNB):
                self.tracks.append(output[idec+i].split("]")[1].lstrip(' '))
                system.startCommand("mpc add cdda:///"+str(i+1))
            self.loaded=True
            self.resetHelper()

        if self.play==False:
            system.startCommand("mpc play")
            self.mpcH.updateView()
        else:
            system.startCommand("mpc pause")
            self.mpcH.updateView()

        self.play = not self.play


    def _next(self):
        system.startCommand("mpc next")
        self.mpcH.updateView()

    def _previous(self):
        system.startCommand("mpc prev")
        self.mpcH.updateView()




























