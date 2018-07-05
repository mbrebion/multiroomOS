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
buttons=[10,8,16,18]
lcdLines=4


# param of local player
simple=False  # in simple mode, only one rotary encoder : to be deleted soon
entries=["radios","localMusic","cd"] # top menus that are available on the device
server = False # true for main hifi station ; false for other devices which then tries to connect to main hifi
autoDisableWifiOnBt=False # turn wifi off while Bluetooth device is playing music ; then turn on




# host ip address
host="piMain"
hortPort=15555

# backlight param
blDelay=10    # backlight time in s (negative for unlimited)
