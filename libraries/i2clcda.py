__author__ = 'osoyoo'

# _____ _____ _____ __ __ _____ _____
#|     |   __|     |  |  |     |     |
#|  |  |__   |  |  |_   _|  |  |  |  |
#|_____|_____|_____| |_| |_____|_____|
#
# Project Tutorial Url:http://osoyoo.com/?p=1031
#
import smbus
import time
from config import iTwoCAddr
from threading import Lock

# Define some device parameters
I2C_ADDR  = iTwoCAddr # I2C device address, if any error, change this address to 0x3f
LCD_WIDTH = 20   # Maximum characters per line

# lock
writeLock=Lock()

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line
physicalLines=[LCD_LINE_1,LCD_LINE_2,LCD_LINE_3,LCD_LINE_4]

LCD_BACKLIGHT_ON  = 0x08  # On
LCD_BACKLIGHT_OFF = 0x00  # Off
LCD_BACKLIGHT = LCD_BACKLIGHT_ON

def enableBacklight():
    global LCD_BACKLIGHT
    LCD_BACKLIGHT = LCD_BACKLIGHT_ON

def disableBacklight():
    global LCD_BACKLIGHT
    LCD_BACKLIGHT = LCD_BACKLIGHT_OFF

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0002 #E_PULSE = 0.0005
E_DELAY = 0.0002

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

def lcd_init():
    # Initialise display
    lcd_byte(0x33,LCD_CMD) # 110011 Initialise
    lcd_byte(0x32,LCD_CMD) # 110010 Initialise
    lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
    lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size : 4 bits
    lcd_byte(0x01,LCD_CMD) # 000001 Clear display
    time.sleep(E_DELAY)


def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = the data
    # mode = 1 for data
    #        0 for command

    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

    # High bits
    #bus.write_byte(I2C_ADDR, bits_high)
    lcd_toggle_enable(bits_high)

    # Low bits
    #bus.write_byte(I2C_ADDR, bits_low)
    lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
    # Toggle enable
    #time.sleep(E_DELAY)
    bus.write_byte(I2C_ADDR, (bits | ENABLE))
    time.sleep(E_PULSE)
    bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
    time.sleep(E_DELAY)

lines=["","","",""]
def lcd_string(message,myLine):
    """
    threadsafe and smart writeToLCD function
    :param message: the message to be printed
    :param line: the line concerned
    :return: nothing
    """
    global lines
    line=myLine-1
    with writeLock:
        if lines[line] != message:
            lines[line]=message
        else:
            return
        mess = message.ljust(LCD_WIDTH, " ")
        lcd_byte(physicalLines[line], LCD_CMD)

        for i in range(LCD_WIDTH):
            lcd_byte(ord(mess[i]),LCD_CHR)


#use :
# lcd_init()
#lcd_string(message,line)

