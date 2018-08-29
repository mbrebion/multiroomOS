__author__ = 'mbrebion'

from config import buttons
from libraries.faceButton import FaceButton

class FaceButtons(object):

    def __init__(self):

        buttonPorts=buttons
        buttonIds=[1,2,3,4]
        self.buttons=[]
        index=0
        for port in buttonPorts:
            self.buttons.append(FaceButton(port,buttonIds[index]))
            index+=1



    def getPressed(self):
        values=[]
        for faceButton in self.buttons:
            if faceButton.getSwitch():
                values.append(faceButton.id)
                print "boutton : " ,faceButton.id
        return values
