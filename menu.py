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
            if sub.parent.name=="Menu":
                return sub.parent
            else :
                sub=sub.parent

    def onShowed(self):
        """
        function called when submenu shown from parent list but not yet selected
        :return:
        """
        self.parent.actionTagTwo=""
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
    def __init__(self,parent,name,hint,default="ndef",saved=False):
        """

        :param parent: parent subsetting menu
        :param name: name
        :param hint: displayed tex
        :param saved: if True, the property saved and retrieved from shelf
        :return: nothing
        """
        SubMenu.__init__(self,parent,name)
        self.saved=saved

        if saved:
            try :
                self.property=system.getDataFromShelf(name)
            except :
                self.property=default # to be overriden
        else:
            self.property=default

        self.hint=hint
        self.trueName=name
        self.actionTagTwo=hint
        self.kind="setting"
        self.selectable=False
        self.update(0)

    def onShowed(self):
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
            self.name= self.hint
            self.parent.actionTagTwo= out
        else :
            self.name= self.trueName +" : "+  out

        if self.saved:
            system.putToShelf(self.trueName,self.property)

        self.getAncestorMenu().askRefreshFromOutside()

class Menu(SubMenu):

    def __init__(self,os,simple=False):
        SubMenu.__init__(self,self,"Menu")
        self.currentSub=self
        self.simple=simple
        self.os=os
        self.configureEntries()


    def setCDInfos(self,items):
        if "cd" not in entries:
            return
        print "cd infos : " , items
        if items==False:
            self.cd.title=""
            self.cd.artist=""
            self.cd.tracks=[]
            self.cd.inDB=""
            self.cd.update()
            return

        #items =[cdName,cdArtist,tracks,inDB]
        self.cd.title=items[0]
        self.cd.artist=items[1]
        self.cd.tracks=items[2]
        self.cd.inDB=items[3]
        self.cd.update()


    def configureEntries(self):

        if "radios" in entries :
            self.radio=Radios(self)
            self.addEntry(self.radio)

        if "localMusic" in entries :
            self.addEntry(Music(self))

        if "alarm" in entries :
            self.alarm=Alarm(self)
            self.addEntry(self.alarm)

        if "cd" in entries :
            self.cd=CD(self)
            self.addEntry(self.cd)

        if "settings" in entries :
            self.settings = Settings(self)
            self.addEntry(self.settings)


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
            self.getAncestorMenu().askRefreshFromOutside()

    def back(self):
        """
        this function is called when physical VOLUME button is pressed or when asked by remote control
        :return: Nothing
        """

        self.currentSub = self.currentSub._back()
        self.currentSub.list[self.currentSub.count].onShowed()

#######################################
#########    Alarm  menus     #########
#######################################

class Alarm(SubMenu):
    def __init__(self,parent,name="Reveil"):
        SubMenu.__init__(self,parent,name)
        self.items=[]
        self.populate()

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
        SubSetting.__init__(self,parent,name,hint,7,False)


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

class TimeMinute(SubSetting):
    def __init__(self,parent,name="Minute", hint="selection minute"):
        SubSetting.__init__(self,parent,name,hint,0,False)


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
        self.getAncestorMenu().askRefreshFromOutside()



#######################################
######### Local music menus   #########
#######################################


class Music(SubMenu):
    def __init__(self,parent,name="Local music"):
        SubMenu.__init__(self,parent,name)
        self.addEntry(Artists(self))
        self.addEntry(PlayList(self))


class Artists(SubMenu):
    def __init__(self,parent,name="Artists"):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.populate()

    def populate(self):
        self.clearEntries()
        system.startCommand("mpc update")
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

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class Settings(SubMenu):
    def __init__(self,parent,name="Reglages"):
        SubMenu.__init__(self,parent,name)
        if "cd"  in entries:
            self.addEntry(MagicMode(self))
        self.addEntry(MPDVolume(self))

        self.addEntry(SettingsWL(self))


class MagicMode(SubSetting):
    def __init__(self,parent,name="Magic Mode", hint="lecture silencieuse"):
        SubSetting.__init__(self,parent,name,hint,False,True)
        self.property=False

    def _showProperty(self):
        if self.property:
            return "v"
        else :
            return "x"

    def _modifyProperty(self,dec):
        if dec != 0:
            self.property = not self.property

class MPDVolume(SubSetting):
    def __init__(self,parent,name="MPDVolume", hint="Volume MPD"):
        SubSetting.__init__(self,parent,name,hint,70,True)

    def _showProperty(self):
        return str(self.property)

    def _modifyProperty(self,dec):
        self.property = max(min(100,self.property+dec),0) # new sound is targeted
        system.startCommand("mpc volume "+str(self.property)) # action is taken


class SettingsWL(SubMenu):
    def __init__(self,parent,name="Reglages Wireless"):
        SubMenu.__init__(self,parent,name)
        self.addEntry(WifiOn(self))
        self.addEntry(WifiAuto(self))

class WifiOn(SubSetting):
    def __init__(self,parent,name="Wifi", hint="Wifi"):
        SubSetting.__init__(self,parent,name,hint,True,True)

    def _showProperty(self):
        if self.property:
            return " - on - "
        else :
            return " - off - "

    def _modifyProperty(self,dec):

        if dec != 0:
            self.property = not self.property

        if self.property:
            system.restartWifi()
        else :
            system.shutdownWifi()

class WifiAuto(SubSetting):
    def __init__(self,parent,name="WifiAuto", hint="Wifi while Bt"):
        SubSetting.__init__(self,parent,name,hint,True,True)

    def _showProperty(self):
        if self.property:
            return " - on - "
        else :
            return " - off - "

    def _modifyProperty(self,dec):
        if dec != 0:
            self.property = not self.property


#######################################
##########     CDs menus    ###########
#######################################


class CD(SubMenu):
    def __init__(self,parent,name="Lecteur CD"):
        SubMenu.__init__(self,parent,name)

        self.inDB=False
        self.tracks=[]
        self.title=""
        self.oldTitle="nope"
        self.artist=""

    def update(self):
        if self.title==self.oldTitle:
            return


        self.oldTitle=self.title
        self.clearEntries()
        if self.getAncestorMenu().os.cdInside==True:
            self.addEntry(CDPlayer(self,name="Lecture "))
            self.addEntry(Eject(self))

            if not self.inDB:
                self.addEntry(Rip(self))
            self.name="Lecteur CD"
            self.actionTagTwo=self.title
            self.selectable=True

        else:
            self.name="Lecteur CD (vide)"
            self.actionTagTwo=""
            self.selectable=False

        self.getAncestorMenu().askRefreshFromOutside()


class Rip(SubMenu):
    def __init__(self,parent,name="Ripping"):
        SubMenu.__init__(self,parent,name)
        self.selectable = False
        self.state=""

    def onSelected(self):
        if self.state=="":
            self.state="on duty"
            system.startCommand(" abcde -N & ")
        else:
            self.state=""
            system.startCommand(" pkill abcde ; pkill cdpara ")

        self.name="Ripping "+self.state


class Eject(SubMenu):
    def __init__(self,parent,name="Ejection"):
        SubMenu.__init__(self,parent,name)
        self.selectable = False

    def onSelected(self):
        self.getAncestorMenu().back()
        self.getAncestorMenu()
        self.getAncestorMenu().askRefreshFromOutside()
        system.startCommand("sudo eject &")
        self.getAncestorMenu().os.cdInside=False


class CDPlayer(SubMenu):
    def __init__(self,parent,name="Lecture"):
        SubMenu.__init__(self,parent,name)
        self.play=False
        self.loaded=False


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
        self.mpcH=MpcHelper(self,self.parent.tracks)


    def onSelected(self):
        SubMenu.onSelected(self)

        if self.loaded==False :
            system.startCommand("mpc clear")
            for i in range(len(self.parent.tracks)):
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




























