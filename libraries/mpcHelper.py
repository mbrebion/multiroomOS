__author__ = 'mbrebion'

import time
import threading
import subprocess

class MpcHelper(threading.Thread):


    def __init__(self,subMenu):
        threading.Thread.__init__(self)
        self.daemon=True
        self.alive=True
        self.lastText=""
        self.sm=subMenu
        self.start()


    def shutDown(self):
        self.alive=False

    def updateView(self):
        """
        To be improved
        :return:
        """
        output = subprocess.check_output("/usr/bin/mpc current ",shell=True).split("-")[1].strip('\n')
        print "output : " , output
        if self.lastText!=output:
            self.lastText=output
            self.sm.actionTag=output
            self.sm.askRefresh=True

    def run(self):
        while(self.alive):
            print "alive mpc helper"
            self.updateView()
            time.sleep(0.5)
