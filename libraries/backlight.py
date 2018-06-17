__author__ = 'mbrebion'

from config import blDelay
import time
import threading
from libraries.i2clcda import enableBacklight,disableBacklight

class Backlight(threading.Thread):

    def __init__(self,os):
        threading.Thread.__init__(self)
        self.last=time.time()
        self.os=os
        self.blOn=False
        self.daemon=True
        self.alive=True
        self.start()

    def shutDown(self):
        self.alive=False
        disableBacklight()

    def test(self):
        if (time.time()-self.last)<blDelay and not self.blOn:
            enableBacklight()
            self.blOn=True
            # self.os.menu.askRefreshFromOutside()

        if (time.time()-self.last)>blDelay and self.blOn:
            disableBacklight()
            self.blOn=False
            self.os.askRefresh(0)

    def run(self):
        while(self.alive):
            self.test()
            time.sleep(0.4)

    def newCommand(self):
        self.last=time.time()
        self.test()

