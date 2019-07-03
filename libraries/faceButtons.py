__author__ = 'mbrebion'

from config import buttons
from libraries.faceButton import FaceButton
from threading import Timer
from libraries.system import logDebug

class FaceButtons(object):

    def __init__(self):

        buttonPorts=buttons
        buttonIds=[1,2,3,4]
        self.buttons=[]
        self.detect = False
        index=0
        for port in buttonPorts:
            self.buttons.append(FaceButton(port,buttonIds[index]))
            index+=1

        ta = Timer(2.0, self.startDetect)
        tb = Timer(4.0, self.authorizedDetect)
        ta.start()
        tb.start()



    def getPressed(self):
        values=[]
        for faceButton in self.buttons:
            if faceButton.getSwitch() and self.detect:
                values.append(faceButton.id)
        return values


    def authorizedDetect(self):
        for faceButton in self.buttons:
            faceButton.getSwitch()  # read buttons states for the first time to purge their states
        logDebug("starting button detection")
        self.detect=True

    def startDetect(self):

        for faceButton in self.buttons:
            faceButton.startDetect()

