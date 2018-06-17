__author__ = 'mbrebion'

import subprocess
from menu import SubMenu,Bt
from config import radios, entries
import system



class SimpleMenu(SubMenu):

    def __init__(self,simple=True):
        SubMenu.__init__(self,self,"Menu")
        self.currentSub=self
        self.currentSelect=False
        self.previousSelect=False

        self.simple=simple
        self.mode="menu"
        system.startCommand("mpc volume  70")
        self.configureEntries()


    ######################################### special commands targeted with buttons actions
    def askRefreshFromOutside(self):
        pass

    def syncToSnapServer(self):
        system.startCommand("mpc clear")
        system.startSnapClientSimple()

    def stopSyncing(self):
        system.stopSnapClient()


    #########################################

    def configureEntries(self):
        self.addEntry(Off(self))

        if "bt" in entries :
            pass
            #self.addEntry(Bt(self))
        if "inter" in entries:
            self.addEntry(Radio(self,"inter","http://direct.franceinter.fr/live/franceinter-midfi.mp3"))
        if "culture" in entries:
            self.addEntry(Radio(self,"culture","http://direct.franceculture.fr/live/franceculture-midfi.mp3"))

    def next(self, dec=1):
            self.updateVolumeLevel(dec)

    def previous(self,dec=-1):
            self.updateVolumeLevel(dec)

    def updateVolumeLevel(self,dec):
        if dec>0:
            system.startCommand("amixer sset 'Master' "+str(dec)+"%+")
        else:
            system.startCommand("amixer sset 'Master' "+str(abs(dec))+"%-")
        print "change volume : " + str(dec)

    def update(self):
        try:
            self.previousSelect._back()
            self.currentSelect.onSelected()
        except:
            pass

    def info(self):
        if self.currentSub.explorable():
            return self.currentSub.name,self.currentSub.list[self.currentSub.count].name
        else :
            return self.currentSub.name,self.currentSub.actionTag


    def select(self):
        if self.mode=="menu":
            self.mode="vol"
            system.startCommand("mpc clear")
        else:
            self.mode="menu"
            system.startCommand("mpc clear")

            system.startCommand("mpc add 'http://direct.franceinter.fr/live/franceinter-midfi.mp3'" )
            system.startCommand("mpc play")

        print self.mode

    def back(self):
        pass





####################################### Radios menus
class Off(SubMenu):
    def __init__(self,parent):
        SubMenu.__init__(self,parent,"off")


class Radio(SubMenu):
    def __init__(self,parent,name,webAddr):
        SubMenu.__init__(self,parent,name)
        self.webAddr=webAddr
        self.actionTag="Listening"


    def onSelected(self):
        SubMenu.onSelected(self)
        system.startCommand("mpc clear")

        system.startCommand("mpc add \""+self.webAddr+"\"" )
        system.startCommand("mpc play")


    def _back(self):
        system.startCommand("mpc stop")
        SubMenu._back(self)


