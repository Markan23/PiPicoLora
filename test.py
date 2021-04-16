# I created this to test the various interfaces this works 
# and has been set running for over a week as main.py
# my intention is to use this to monitor a remote site
#
from time import sleep
import machine, onewire, ds18x20, time
from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import framebuf
import utime
import sys
import time
import random 
import SDL_Pi_INA3221
from ulora import LoRa, ModemConfig, SPIConfig
WIDTH  = 128                                            # oled display width
HEIGHT = 64                                            # oled display height
ina3221 = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)
#
# the three channels of the INA3221 named for Solar Power Controller
LIPO_BATTERY_CHANNEL = 1
SOLAR_CELL_CHANNEL   = 2
OUTPUT_CHANNEL       = 3
# Lora Parameters
RFM95_RST = 9
RFM95_SPIBUS = SPIConfig.pico
RFM95_CS = 5
RFM95_INT = 8
RF95_FREQ = 868.1
RF95_POW = 20
CLIENT_ADDRESS = 1
SERVER_ADDRESS = 2
x = 0
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000) 
ds_pin = machine.Pin(16)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()
print('Found a ds18x20 device')
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)                  # Init oled display

# Thermometer logo as 32x32 bytearray
buffer = bytearray(b"\x00\x03\xc0\x00\x00\x07\xe0\x00\x00\x0e\x70\x00\x00\x0c\x30\x00\x00\x0c\x30\x00\x00\x0c\x30\x00\x00\x0c\x30\x00\x00\x0c\x30\x00\x00\x0c\x30\x00\x00\x0c\x30\x00\x00\x0c\x30\x00\x00\x0c\x30\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x0d\xb0\x00\x00\x1d\xb8\x00\x00\x1b\xd8\x00\x00\x37\xec\x00\x00\x37\xec\x00\x00\x37\xec\x00\x00\x33\xcc\x00\x00\x19\x98\x00\x00\x1c\x38\x00\x00\x0f\xf0\x00\x00\x03\xc0\x00")

# Load the thermometer logo into the framebuffer (the image is 32x32)
fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB)
# initialise radio
lora = LoRa(RFM95_SPIBUS, RFM95_INT, CLIENT_ADDRESS, RFM95_CS, reset_pin=RFM95_RST, freq=RF95_FREQ, tx_power=RF95_POW, acks=True)


# loop and send data
while True:
    x=x+1
    ds_sensor.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
    #print(ds_sensor.read_temp(rom))
      temperature = ds_sensor.read_temp(rom)

    #print("================================")
    shuntvoltage1 = 0
    busvoltage1   = 0
    current_mA1   = 0
    loadvoltage1  = 0


    busvoltage1 = ina3221.getBusVoltage_V(LIPO_BATTERY_CHANNEL)
    shuntvoltage1 = ina3221.getShuntVoltage_mV(LIPO_BATTERY_CHANNEL)
    # minus is to get the "sense" right.   - means the battery is charging, + that it is discharging
    current_mA1 = ina3221.getCurrent_mA(LIPO_BATTERY_CHANNEL)  

    loadvoltage1 = busvoltage1 + (shuntvoltage1 / 1000)
    lora_ch1="1,"+str(busvoltage1)+","+str(shuntvoltage1)+","+str(current_mA1)+","+str(loadvoltage1)

    shuntvoltage2 = 0
    busvoltage2 = 0
    current_mA2 = 0
    loadvoltage2 = 0

    busvoltage2 = ina3221.getBusVoltage_V(SOLAR_CELL_CHANNEL)
    shuntvoltage2 = ina3221.getShuntVoltage_mV(SOLAR_CELL_CHANNEL)
    current_mA2 = -ina3221.getCurrent_mA(SOLAR_CELL_CHANNEL)
    loadvoltage2 = busvoltage2 + (shuntvoltage2 / 1000)
    lora_ch2="2,"+str(busvoltage2)+","+str(shuntvoltage2)+","+str(current_mA2)+","+str(loadvoltage2)

    shuntvoltage3 = 0
    busvoltage3 = 0
    current_mA3 = 0
    loadvoltage3 = 0

    busvoltage3 = ina3221.getBusVoltage_V(OUTPUT_CHANNEL)
    shuntvoltage3 = ina3221.getShuntVoltage_mV(OUTPUT_CHANNEL)
    current_mA3 = ina3221.getCurrent_mA(OUTPUT_CHANNEL)
    loadvoltage3 = busvoltage3 + (shuntvoltage3 / 1000)
    lora_ch3="3,"+str(busvoltage3)+","+str(shuntvoltage3)+","+str(current_mA3)+","+str(loadvoltage3)    
    
    if x==5:
      lora.send_to_wait("T"+str(int(temperature)), SERVER_ADDRESS)
    if x==10:
      lora.send_to_wait(lora_ch1, SERVER_ADDRESS)
    if x==15:
      lora.send_to_wait(lora_ch2, SERVER_ADDRESS)
    if x==20:
      lora.send_to_wait(lora_ch3, SERVER_ADDRESS)
    
    #print (lora_ch1,lora_ch2,lora_ch3)
    print("sent ",x)    
    
    # Clear the oled display in case it has junk on it.
    oled.fill(0)

    # Blit the image from the framebuffer to the oled display
    oled.blit(fb, 96, 0)

    # Add text with temperature
    oled.text(" This Room",5,2)
    oled.text("Temperature",5,13)
    oled.text("  is " + str(int(temperature)) +  "C",5,25)
    oled.text("  LoRa   "+str(x),5,49)
    if x>=20:
        x=0
    # Update the oled display so the image & text is displayed
    oled.show()

    # Sleep 2 seconds before measure again
    sleep(2)

