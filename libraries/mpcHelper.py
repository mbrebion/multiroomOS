__author__ = 'mbrebion'

import time
import threading
from system import startReturnCommand

class MpcHelper(threading.Thread):

    exist=False

    def __init__(self,subMenu,tracks=[]):
        threading.Thread.__init__(self)
        self.tracks=tracks


        self.daemon = True
        self.alive = True

        self.lastText = ""
        self.lastStatus = ""

        self.sm = subMenu
        MpcHelper.exist = True
        self.start()


    def shutDown(self):
        self.alive = False

    def updateView(self):
        """
        To be improved
        :return:
        """

        text = ""
        status = ""
        output = startReturnCommand("/usr/bin/mpc")
        if len(output) == 1:
            self.sm.actionTagTwo = "  end  "
            self.sm.askRefresh = True
            self.alive=False



        if len(output) == 4:
            if "cdda" in output[0]:
                # audio CD in this case
                index=int(output[0].split("///")[1].lstrip(" "))
                text=self.tracks[index-1]
                status=" -- "+output[1].split("]")[0].lstrip("[") + " -- " +output[1].split("#")[1].split(" ")[0]

            else :
                # MP3s
                text =  output[0].split("-")[1].lstrip(" ")
                status = " -- "+output[1].split("]")[0].lstrip("[") + " -- " +output[1].split("#")[1].split(" ")[0]


        if self.lastText != text or self.lastStatus != status:
            self.lastText = text
            self.lastStatus = status
            self.sm.actionTag = text
            self.sm.actionTagTwo = status
            self.sm.askRefresh = True


    def run(self):
        while(self.alive):
            self.updateView()
            time.sleep(0.2)
        MpcHelper.exist = False
