__author__ = 'mbrebion'


pathToMusic="/home/pi/Music/"

radios=[]
radios.append(["France Inter","http://direct.franceinter.fr/live/franceinter-midfi.mp3"])
radios.append(["France Info","http://direct.franceinfo.fr/live/franceinfo-midfi.mp3"])
radios.append(["France Culture","http://direct.franceculture.fr/live/franceculture-midfi.mp3"])
radios.append(["Rire & Chansons","http://cdn.nrjaudio.fm/audio1/fr/30401/mp3_128.mp3?origine=fluxradios"])

# rotaries
rotOne=[11,15,13]
rotTwo=[19,23,21]
buttons=[8,10,16,18]
lcdLines=4
iTwoCAddr=0x27

# param of local player
#simple=False  # in simple mode, only one rotary encoder
server=True
entries=["radios","localMusic","cd","settings"]


host="192.168.0.12"
hortPort="15555"
blDelay=10
