__author__ = 'mbrebion'


pathToMusic="/home/pi/Music/"

radios=[]
radios.append(["France Inter","http://direct.franceinter.fr/live/franceinter-midfi.mp3"])
radios.append(["France Info","http://direct.franceinfo.fr/live/franceinfo-midfi.mp3"])
radios.append(["France Culture","http://direct.franceculture.fr/live/franceculture-midfi.mp3"])
radios.append(["Rire & Chansons","http://cdn.nrjaudio.fm/audio1/fr/30401/mp3_128.mp3?origine=fluxradios"])

rotOne=[15,13,11]
rotTwo=[23,19,21]
buttons=[18,16,10,8]
lcdLines=2
iTwoCAddr=0x3F

# param of local player
simple=False  # in simple mode, only one rotary encoder
server=False
#entries=["bt","radios","localMusic"]
entries=["radios","localMusic","alarm","settings"]
autoDisableWifiOnBt=True

host="piMain"
hortPort=15555
blDelay=12
