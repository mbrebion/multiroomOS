from RPi import GPIO
import time

GPIO.setmode(GPIO.BOARD)

clk=23
dt=21
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

oclk=GPIO.input(clk)
idt=GPIO.input(dt)
printS=False
out=[]
n=0
while n<100000 :
    if GPIO.input(clk)!=oclk and not printS:
        printS=True
        tzero=time.time()
        print("begin")

    if printS == True:
        n=n+1
        out.append([time.time()-tzero,GPIO.input(clk),GPIO.input(dt)])

print("end")

output=open("data.dat","wb")
for dat in out:
    output.write(str(dat[0])+","+ str(dat[1])+","+ str(dat[2])+ "\n")
output.close()

