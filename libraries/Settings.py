__author__ = 'mbrebion'
from libraries import system


class Settings():
    def __init__(self):
        self.readFromShelf()



    def readFromShelf(self):
        self.magicMode= system.getDataFromShelf("magicMode")
        self.mpcVol= system.getDataFromShelf("mpcVol")
        self.bluetooth= system.getDataFromShelf("bluetooth")
        self.wifi= system.getDataFromShelf("wifi")



    def update(self,key,data):
        system.putToShelf(key, data)
        if key=="magicMode":
            return

        if key=="mpcVol":
            system.startCommand("mpc volume " + str(data))

        if key=="bluetooth":
             return

        if key=="wifi":
            return

