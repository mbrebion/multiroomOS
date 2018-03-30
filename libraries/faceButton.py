__author__ = 'mbrebion'

from RPi import GPIO


class FaceButton(object):



    def __init__(self,port,id):
        self.port=port
        print port
        GPIO.setup(port, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        self.hasBeenSwitched=False
        self.isSwitched=False
        self.id=id

        GPIO.add_event_detect(self.port, GPIO.FALLING, callback=self.event,bouncetime=100)


    def event(self,channel):
        if GPIO.input(self.port)==False:
            self.hasBeenSwitched=True


    def getSwitch(self):
        store=self.hasBeenSwitched
        self.hasBeenSwitched=False
        return store

    def isSwitched(self):
        return GPIO.INPUT(self.port)