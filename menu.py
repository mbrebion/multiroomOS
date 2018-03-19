__author__ = 'mbrebion'

import subprocess
from config import radios, entries
from time import sleep
import system

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
        self.selectable=True

    def explorable(self):
        return len(self.list) != 0


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
        pass

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
            self.addEntry(Radios(self))
        if "localMusic" in entries :
            self.addEntry(Music(self))



    def next(self):
        self.currentSub._next()

    def previous(self):
        self.currentSub._previous()


    def info(self):
        if self.currentSub.explorable():
            return self.currentSub.name,self.currentSub.list[self.currentSub.count].name
        else :
            return self.currentSub.name,self.currentSub.actionTag


    def select(self):
        save= self.currentSub._select()
        if save!=False and save.selectable==True:
            self.currentSub =save
            if save.explorable():
                try :
                    save.list[save.count].onShowed()
                except:
                    pass

    def back(self):
        self.currentSub = self.currentSub._back()



####################################### BlueTooth menus
class Bt(SubMenu):
    def __init__(self,parent,name="Bluetooth"):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.actionTag="   Wifi Off"

    def onSelected(self):
        SubMenu.onSelected(self)
        system.startCommand('sudo /sbin/ifconfig wlan0 down')

    def _back(self):
        system.startCommand('sudo /sbin/ifconfig wlan0 up')
        return SubMenu._back(self)



####################################### Music menus

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
        output = subprocess.check_output("/usr/bin/mpc list AlbumArtist",shell=True)
        allArtists=output.split('\n')[0:-1] # this contains all artist which released at least an album !

        for name in allArtists:
            artist=Artist(self,name)
            self.addEntry(artist)

    def onSelected(self):
        SubMenu.onSelected(self)
        self.populate()



class Artist(SubMenu):
    def __init__(self,parent,name):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.populate()

    def populate(self):
        output = subprocess.check_output("/usr/bin/mpc list Album Artist \""+self.name+"\"",shell=True)
        allAlbums=output.split('\n')[0:-1] # this contains all artist which released at least an album !

        for name in allAlbums:
            album=Album(self,name)
            self.addEntry(album)


class Album(SubMenu):
    def __init__(self,parent,name):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.play=False
        self.loaded=False

    def updateTag(self,msg=False):
        """
        set tag to song name if no other message is provided.
        :param msg: message to put as a actionTag (displayed at the second line of lcd screen)
        :return: nothing
        """
        if msg==False:
            sleep(0.05)
            try :
                info = subprocess.check_output("mpc current",shell=True).split("-")[1].strip('\n')
            except:
                info=""
        else:
            info=msg
        self.actionTag=info


    def onSelected(self):
        SubMenu.onSelected(self)
        if self.loaded==False :
            system.startCommand("mpc clear")
            cmd="mpc search Album  \""+self.name+"\" artist \""+ self.parent.name+ "\" | mpc add"
            system.startCommand(cmd)
            self.loaded=True

        if self.play:
            system.startCommand("mpc pause")
            self.play=False
            self.updateTag(" - paused - ")
        else :
            system.startCommand("mpc play")
            self.play = True
            self.updateTag()


    def _next(self):
        system.startCommand("mpc next")
        self.updateTag()
        print self.actionTag

    def _previous(self):
        system.startCommand("mpc prev")
        self.updateTag()
        print self.actionTag

    def _back(self):
        system.startCommand("mpc stop")
        system.startCommand("mpc clear")
        self.play=False
        self.loaded=False
        self.updateTag(" - stopped - ")
        print self.actionTag
        return SubMenu._back(self)

class PlayList(SubMenu):
    def __init__(self,parent,name="Playlists"):
        SubMenu.__init__(self,parent,name)
        self.parent=parent



####################################### Radios menus
class Radios(SubMenu):
    def __init__(self,parent,name="Radios"):
        SubMenu.__init__(self,parent,name)

        for radio in radios:
            name=radio[0]
            webAddr=radio[1]
            self.addEntry(Radio(self,name,webAddr))

    def _back(self):
        system.startCommand("mpc stop")
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
        print "on showed + ", self.name
        system.startCommand("mpc clear")
        system.startCommand("mpc add \""+self.webAddr+"\"" )
        system.startCommand("mpc play")



