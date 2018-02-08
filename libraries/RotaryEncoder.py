__author__ = 'maxence'

from RPi import GPIO
import time
# usefull to controll one rotary encoder

class RotaryEncoder(object):
    """
    this class is dedicated to deal with a rotary encoder and manage it
    """

    def __init__(self,clk,dt,switch,name):
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
        self.lastSide=0
        self.changeSideDt=0.150 # minimal time before change in rotation side in second
        self.lastCall=0
        self.askRefresh=True
        self.last=[0,0,0]


        self.hasBeenSwitchedOn=False
        self.counts=0

        # GPIOs init
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.current=[GPIO.input(self.clk),GPIO.input(self.dt),0] # current state


        # add callback event
        GPIO.add_event_detect(self.clk, GPIO.BOTH, callback=self.rotaryCallState,bouncetime=6)
        GPIO.add_event_detect(self.dt, GPIO.BOTH, callback=self.rotaryCallState,bouncetime=6)

        GPIO.add_event_detect(self.switch, GPIO.BOTH, callback=self.switchCall,bouncetime=25)


    def switchCall(self,channel):
        if GPIO.input(self.switch) == 0:
            self.hasBeenSwitchedOn = True


    def updateCurrent(self,force=False):
        if (time.time()-self.lastCall >0.25 and self.askRefresh) or force :    # this test prevent from modification while rotary is in use
            self.current=[GPIO.input(self.clk),GPIO.input(self.dt),-1]
            self.askRefresh=False

    def rotaryCallState(self,chanel):
        self.last=self.current

        # check if event missed
        if chanel==self.current[2]:
            # two events in a row of same chanel : event probably missed or rotary rotated forth and back
            #self.current=[1-self.current[0],1-self.current[1],chanel]
            time.sleep(0.005)
            self.updateCurrent(True)
        else : # no event missed
            if chanel==self.clk:
                self.current=[1-self.current[0],self.current[1],chanel]
            else:
                self.current=[self.current[0],1-self.current[1],chanel]

        self.rotaryCall()
        self.askRefresh=True



    def rotaryCall(self):

        now=time.time()
        dt=now-self.lastCall

        if self.last==[0,1,self.dt]:
            if self.current==[1,1,self.clk]:
                # turning clockwise
                if self.lastSide==-1 and dt < self.changeSideDt :
                    # this might be an error : do nothing
                    time.sleep(0.005)
                    self.updateCurrent(True)
                else :
                    self.lastSide=1
                    self.counts+=1
                self.lastCall=time.time()

        if self.last==[1,0,self.clk]:
            if self.current==[1,1,self.dt]:
                # turning anti-clockwise
                if self.lastSide==1 and dt < self.changeSideDt :
                    # this might be an error : do nothing
                    time.sleep(0.005)
                    self.updateCurrent(True)
                else :
                    self.lastSide=-1
                    self.counts+=-1
                self.lastCall=time.time()




    def getDec(self):
        store=self.counts
        self.counts=0
        return store

    def getSwitch(self):
        if self.hasBeenSwitchedOn:
            self.hasBeenSwitchedOn = False
            return True

        return False




