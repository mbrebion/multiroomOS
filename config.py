__author__ = 'mbrebion'


pathToMusic="/home/pi/Music/"

radios=[]
radios.append(["France Inter","http://direct.franceinter.fr/live/franceinter-midfi.mp3"])
radios.append(["France Info","http://direct.franceinfo.fr/live/franceinfo-midfi.mp3"])
radios.append(["France Culture","http://direct.franceculture.fr/live/franceculture-midfi.mp3"])
radios.append(["Rire & Chansons","http://cdn.nrjaudio.fm/audio1/fr/30401/mp3_128.mp3?origine=fluxradios"])




# param of local player
simple=False  # in simple mode, only one rotary encoder
entries=["bt","radios","localMusic"]




# host ip address
host="192.168.0.12"
hortPort=15555

# backlight param
blDelay=10    # backlight time in s (negative for unlimited)
