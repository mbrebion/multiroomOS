__author__ = 'maxence'

from RPi import GPIO
import threading


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

        #self.current_A = 1
        #self.current_B = 1

        # add callback event
        #GPIO.add_event_detect(self.clk, GPIO.RISING, callback=self.rotary_interrupt)  # NO bouncetime
        #GPIO.add_event_detect(self.dt, GPIO.RISING, callback=self.rotary_interrupt)

        GPIO.add_event_detect(self.clk, GPIO.BOTH, callback=self.rotaryCallState,bouncetime=1) # bouncing has been removed and it seems to work well
        GPIO.add_event_detect(self.dt, GPIO.BOTH, callback=self.rotaryCallState,bouncetime=1)
        GPIO.add_event_detect(self.switch, GPIO.BOTH, callback=self.switchCall,bouncetime=300)

        # a test on the rotary showed that bouncetime did not exceded 10 \mu s
        # a value of 1ms is therefore safe

    def switchCall(self,channel):
        if GPIO.input(self.switch) == 0:
            self.rotLock.acquire()
            self.hasBeenSwitchedOn = True
            self.rotLock.release()

    def rotary_interrupt(self,A_or_B):
        """
        deprecated : half turns are missed
        :param A_or_B:
        :return:
        """
        # read both of the switches
        Switch_A = GPIO.input(self.clk)
        Switch_B = GPIO.input(self.dt)
        # now check if state of A or B has changed
        # if not that means that bouncing caused it
        if self.current_A == Switch_A and self.current_B == Switch_B:  # Same interrupt as before (Bouncing)?
            return  # ignore interrupt!

        self.current_A = Switch_A  # remember new state
        self.current_B = Switch_B  # for next bouncing check

        if (Switch_A and Switch_B):  # Both one active? Yes -> end of sequence
            if A_or_B == self.dt:  # Turning direction depends on
                self.countPP(+1)
            else:  # so depending on direction either
                self.countPP(-1)



    def rotaryCallState(self,chanel):
        state=GPIO.input(chanel)

        if chanel==self.clk:
            target=self.clk
            index=0
        else :
            target = self.dt
            index=1

        if self.current[index]==state : # wrong hit : already in this state
            #print("wrong hit : " + str(index) +" : "+str(state) )
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




