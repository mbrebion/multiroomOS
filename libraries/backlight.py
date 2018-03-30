__author__ = 'mbrebion'

from RPi import GPIO
from config import blDelay
import time
import threading

class Backlight(threading.Thread):

    def __init__(self,port):
        threading.Thread.__init__(self)
        self.port=port
        GPIO.setup(port,GPIO.OUT)
        self.last=time.time()
        self.daemon=True
        self.alive=True
        self.start()

    def shutDown(self):
        self.alive=False
        GPIO.output(self.port,0)


    def test(self):
        if (time.time()-self.last)<blDelay:
            GPIO.output(self.port,1)
        else:
            GPIO.output(self.port,0)

        if blDelay<0: # in case of negative value : always enable backlight
            GPIO.output(self.port,1)


    def run(self):
        while(self.alive):
            self.test()
            time.sleep(0.3)

    def newCommand(self):
        self.last=time.time()
        self.test()

