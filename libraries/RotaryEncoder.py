__author__ = 'maxence'

from RPi import GPIO
import time
# usefull to controll one rotary encoder

class RotaryEncoder(object):
    """
    this class is dedicated to deal with a rotary encoder and manage it
    """

    def __init__(self,switch,clk,dt,name):
        """

        :param clk: pin for clk
        :param dt: pin for ds
        :param switch: pin for switch
        :param name: name of this rotary encoder
        :return:
        """
        self.counter=0
        self.oldCounter=0
        self.clk=clk
        self.dt=dt
        self.switch=switch
        self.name=name


        # detection improvement
        self.last=[0,0,0]


        self.hasBeenSwitchedOn=False
        self.counts=0

        # GPIOs init
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.current=[GPIO.input(self.clk),GPIO.input(self.dt),0] # current state

        # add callback event
        GPIO.add_event_detect(self.clk, GPIO.BOTH, callback=self.rotaryCallState,bouncetime=15)
        GPIO.add_event_detect(self.dt, GPIO.BOTH, callback=self.rotaryCallState,bouncetime=15)
        GPIO.add_event_detect(self.switch, GPIO.BOTH, callback=self.switchCall,bouncetime=25)


    def switchCall(self,channel):
        if GPIO.input(self.switch) == 0:
            self.hasBeenSwitchedOn = True


    def rotaryCallState(self,chanel):
        state=GPIO.input(chanel)
        #print "event : "+ str(chanel)
        #print state

        if chanel==self.clk:
            target=self.clk
            index=0
        else :
            target = self.dt
            index=1

        if self.current[index]==state : # wrong hit : already in this state
            return

        self.last=self.current
        self.current[index]=state

        if target==self.clk: # clockwhise assumed here
            if state == 1 and self.last[1]==0:
                self.counts+=1
            if state == 0 and self.last[1]==1 :
                self.counts+=1

        if target == self.dt : # anti clockwise assumed here
            if state ==0 and self.last[0]==1:
                self.counts-=1
            if state ==1 and self.last[0]==0 :
                self.counts-=1



    def getDec(self):
        store=self.counts
        self.counts=0
        return store

    def getSwitch(self):
        if self.hasBeenSwitchedOn:
            self.hasBeenSwitchedOn = False
            return True

        return False




