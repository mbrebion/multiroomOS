__author__ = 'maxence'

from RPi import GPIO
import threading
from threading import Timer
import time


class RotaryEncoder(object):
    """
    this class is dedicated to deal with a rotary encoder and manage it
    """

    def __init__(self,pins,name):
        """
        # pins=[switch,clk,dt]
        :param clk: pin for clk
        :param dt: pin for ds
        :param switch: pin for switch
        :param name: name of this rotary encoder
        :return:
        """
        self.counter=0
        self.oldCounter=0
        self.clk=pins[1]
        self.dt=pins[2]
        self.switch=pins[0]
        self.name=name
        self.rotLock = threading.Lock()
        self.butLock = threading.Lock()
        self.lastTime=time.time()-10


        # detection improvement
        self.last=[0,0,0]


        self.hasBeenSwitchedOn=False
        self.counts=0

        # GPIOs init
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # should we avoid pull up ?
        GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.updateState()
        t = Timer(4.0, self.startDetect)
        t.start()


    def startDetect(self):
        GPIO.add_event_detect(self.clk, GPIO.BOTH, callback=self.rotaryCallState,bouncetime=1)
        GPIO.add_event_detect(self.dt, GPIO.BOTH, callback=self.rotaryCallState,bouncetime=1)
        GPIO.add_event_detect(self.switch, GPIO.BOTH, callback=self.switchCall,bouncetime=300)
        # a test on the rotary showed that bouncetime did not exceded 10 \mu s
        # a value of 1ms is therefore safe


    def switchCall(self,channel):
        if GPIO.input(self.switch) == 0:
            with self.butLock:
                self.hasBeenSwitchedOn = True



    def rotaryCallState(self,chanel):
        state=GPIO.input(chanel)
        self.lastTime=time.time()

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

        if target==self.clk and self.counts>=0: # clockwise assumed here
            if state == 1 and self.last[1]==0:
                self.countPP(1)
                return
            if state == 0 and self.last[1]==1 :
                self.countPP(1)
                return

        if target == self.dt and self.counts<=0: # anti clockwise assumed here
            if state ==0 and self.last[0]==1:
                self.countPP(-1)
                return
            if state ==1 and self.last[0]==0 :
                self.countPP(-1)
                return

    def countPP(self,p):
        with self.rotLock:
            self.counts+=p

    def updateState(self):
        if time.time()-self.lastTime>2:
            #only update after rotaries are not used
            self.current = [GPIO.input(self.clk), GPIO.input(self.dt), 0]  # current state

    def getDec(self):
        with self.rotLock:
            store=self.counts
            self.counts=0

        return store

    def getSwitch(self):
        with self.butLock:
            value=self.hasBeenSwitchedOn
            self.hasBeenSwitchedOn = False

        return value




