from machine import Pin, PWM
from BusOut  import *

#TODO:  DHT11 - https://www.upesy.com/blogs/tutorials/use-dht11-humidity-temperature-sensor-on-pi-pico-with-micro-python-script 
#       Although it is straightforward, this tool is limited in speed, as it can only measure once per second.

fan_vu_metar_leds = BusOut([4, 5, 6, 7, 8, 9]) # Tacno za picoETF

overheating_led = Pin(11, Pin.OUT) #TODO: Treba da blinka ako je izmjerena temperatura >= kriticne temperature 

fan_pwm = PWM(Pin(1)) #TODO: OVO JE PROIZVOLJNO - provjeriti koji Pin se zapravo moze koristiti
fan_pwm.freq(500)

def update_vu_meter(duty_u16): #TODO: Implementirati
    pass 

def set_fan_speed(duty_u16):
    fan_pwm.duty_u16(duty_u16)