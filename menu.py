__author__ = 'mbrebion'

import os as osys
import subprocess
from config import pathToMusic


class SubMenu(object):
    processes=[]  # static var to store all the processed which must be killed on exit

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

    def explorable(self):
        return len(self.list) != 0


    def _next(self):
        self.count+=1
        if self.count>=len(self.list) :
            self.count=0


    def _previous(self):
        self.count-=1
        if self.count<0 :
            self.count=len(self.list)-1

    def onSelected(self):
        print "processes length : " , len(self.proc)

    def _select(self):
        if self.explorable() :
            self.list[self.count].onSelected()
            return self.list[self.count]
        else:
            self.onSelected()
            return False

    def _back(self):
        return self.parent

    def addEntry(self,sub):
        self.list.append(sub)




class Menu(SubMenu):

    def __init__(self):
        SubMenu.__init__(self,self,"Menu")
        self.currentSub=self

        self.addEntry(Bt(self))
        self.addEntry(Radio(self))
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
        if save!=False:
            self.currentSub =save

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
        osys.system('sudo /sbin/ifconfig wlan0 down')

    def _back(self):
        osys.system('sudo /sbin/ifconfig wlan0 up')
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

    def populate(self):
        self.list=[] # is it safe to create a new list instead of emptying it ?
        allArtists = [d for d in osys.listdir(pathToMusic) if osys.path.isdir(d)]
        count=0
        for name in allArtists:
            count+=1
            artist=Artist(self,name,pathToMusic+name+"/")
            self.addEntry(artist)
        print str(count) +"  artists added"

#TODO : define album class and populate artists with them

class Artist(SubMenu):
    def __init__(self,parent,name,path):
        SubMenu.__init__(self,parent,name)
        self.parent=parent
        self.path=path




class PlayList(SubMenu):
    def __init__(self,parent,name="Playlists"):
        SubMenu.__init__(self,parent,name)
        self.parent=parent



####################################### Radio menus
class Radio(SubMenu):
    def __init__(self,parent,name="Radio"):
        SubMenu.__init__(self,parent,name)
        self.addEntry(Inter(self))
        self.addEntry(Culture(self))
        self.addEntry(Info(self))
        self.addEntry(Rire(self))


    def onSelected(self):
        SubMenu.onSelected(self)
        # add code to start radio at this point


class Inter(SubMenu):
    def __init__(self,parent,name="France Inter"):
        SubMenu.__init__(self,parent,name)
        self.actionTag="Listening"


    def onSelected(self):
        SubMenu.onSelected(self)
        SubMenu.clearProcesses()
        SubMenu.processes.append(subprocess.Popen(["mpg321", "http://direct.franceinter.fr/live/franceinter-midfi.mp3", "&"]))


class Info(SubMenu):
    def __init__(self,parent,name="France Info"):
        SubMenu.__init__(self,parent,name)
        self.actionTag="Listening"

    def onSelected(self):
        SubMenu.onSelected(self)
        SubMenu.clearProcesses()
        SubMenu.processes.append(subprocess.Popen(["mpg321", "http://direct.franceinfo.fr/live/franceinfo-midfi.mp3", "&"]))

class Culture(SubMenu):
    def __init__(self,parent,name="France Culture"):
        SubMenu.__init__(self,parent,name)
        self.actionTag="Listening"


    def onSelected(self):
        SubMenu.onSelected(self)
        SubMenu.clearProcesses()
        SubMenu.processes.append(subprocess.Popen(["mpg321", "http://direct.franceculture.fr/live/franceculture-midfi.mp3", "&"]))


class Rire(SubMenu):
    def __init__(self,parent,name="Rire & Chanson"):
        SubMenu.__init__(self,parent,name)
        self.actionTag="Listening"


    def onSelected(self):
        SubMenu.onSelected(self)
        SubMenu.clearProcesses()
        SubMenu.processes.append(subprocess.Popen(["mpg321", "http://cdn.nrjaudio.fm/audio1/fr/30401/mp3_128.mp3?origine=fluxradios", "&"]))







