__author__ = 'maxence'

from RPi import GPIO

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

        # counts
        self.hasBeenSwitchedOn=False
        self.counts=0

        # GPIOs init
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.clkLastState = GPIO.input(self.clk)


        # add callback event
        GPIO.add_event_detect(self.clk, GPIO.BOTH, callback=self.rotaryCall,bouncetime=40)
        GPIO.add_event_detect(self.switch, GPIO.BOTH, callback=self.switchCall,bouncetime=50)


    def switchCall(self,channel):
        if GPIO.input(self.switch) == 0:
            self.hasBeenSwitchedOn = True

    def rotaryCall(self,channel):
        #print GPIO.input(self.clk), GPIO.input(self.dt)

        if GPIO.input(self.dt)==0:
            self.counts+=1
        else:
            self.counts-=1

       # print self.counts


    def getDec(self):
        store=self.counts
        self.counts=0
        return store

    def getSwitch(self):
        if self.hasBeenSwitchedOn:
            self.hasBeenSwitchedOn = False
            return True

        return False





























































































    def counterChanged(self):

        clkState = GPIO.input(self.clk)
        dtState = GPIO.input(self.dt)
        #print clkState,dtState
        if clkState != self.clkLastState :
            self.clkLastState = clkState
            if dtState != clkState:
                return True,1
            else:
                return True,-1
        return False,0



