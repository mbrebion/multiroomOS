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
        system.startCommand("mpc volume  50")
        self.configureEntries()


    def configureEntries(self):
        self.addEntry(Off(self))

        if "bt" in entries :
            pass
            #self.addEntry(Bt(self))
        if "inter" in entries:
            self.addEntry(Radio(self,"inter","http://direct.franceinter.fr/live/franceinter-midfi.mp3"))
        if "culture" in entries:
            self.addEntry(Radio(self,"culture","http://direct.franceculture.fr/live/franceculture-midfi.mp3"))

    def next(self):
        if self.mode=="menu":
            self.currentSub._next()
            self.previousSelect=self.currentSelect
            self.currentSelect=self.list[self.count]
            self.update()
        else:
            self.updateVolumeLevel(1)

    def previous(self):
        if self.mode=="menu":
            self.currentSub._previous()
            self.previousSelect=self.currentSelect
            self.currentSelect=self.list[self.count]
            self.update()
        else:
            self.updateVolumeLevel(-1)

    def updateVolumeLevel(self,dec):
        if dec>0:
            system.startCommand("mpc volume  +4")
        else:
            system.startCommand("mpc volume -4")

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
        else:
            self.mode="menu"

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


