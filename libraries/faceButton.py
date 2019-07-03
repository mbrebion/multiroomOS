__author__ = 'mbrebion'

from RPi import GPIO
import threading

class FaceButton(object):


    def __init__(self,port,id):
        self.port=port
        GPIO.setup(port, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        self.hasBeenSwitched=False
        self.id=id
        self.butLock = threading.Lock()


    def startDetect(self):
        GPIO.add_event_detect(self.port, GPIO.RISING, callback=self.eventRise, bouncetime=300)

    def eventRise(self,value):
        with self.butLock:
            self.hasBeenSwitched = True



    def getSwitch(self):
        with self.butLock:
            store = self.hasBeenSwitched
            self.hasBeenSwitched = False

        return store

