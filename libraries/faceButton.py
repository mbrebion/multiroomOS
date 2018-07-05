__author__ = 'mbrebion'

from RPi import GPIO


class FaceButton(object):


    def __init__(self,port,id):
        self.port=port
        GPIO.setup(port, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        self.hasBeenSwitched=False
        self.id=id

        GPIO.add_event_detect(self.port, GPIO.RISING, callback=self.eventRise,bouncetime=30)


    def eventRise(self,value):
        self.hasBeenSwitched = True



    def getSwitch(self):
        store = self.hasBeenSwitched
        self.hasBeenSwitched = False
        return store

