__author__ = 'mbrebion'

from config import blDelay
import time
from libraries.i2clcda import enableBacklight,disableBacklight

class Backlight():

    def __init__(self,os):
        self.last=time.time()
        self.os=os
        self.blOn=False
        self.alive=True
        self.delayCheck=1

    def shutDown(self):
        disableBacklight()

    def test(self):
        if (time.time()-self.last) < blDelay and not self.blOn:
            enableBacklight()
            self.blOn = True
            return
            # self.os.menu.askRefreshFromOutside()

        if (time.time()-self.last)>blDelay and self.blOn:

            disableBacklight()
            self.blOn = False
            self.os.io.askResendTexts()
            return


    def newCommand(self):
        self.last=time.time()
        self.test()

