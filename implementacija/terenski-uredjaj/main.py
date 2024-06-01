from machine import Pin, PWM, ADC, Timer
#from BusOut  import *

#TODO:  DHT11 - https://www.upesy.com/blogs/tutorials/use-dht11-humidity-temperature-sensor-on-pi-pico-with-micro-python-script 
#       Although it is straightforward, this tool is limited in speed, as it can only measure once per second.

#fan_vu_metar_leds = BusOut([4, 5, 6, 7, 8, 9]) # Tacno za picoETF
overheating_led = Pin(11, Pin.OUT) #TODO: Treba da blinka ako je izmjerena temperatura >= kriticne temperature 

fan_pwm = PWM(Pin(1)) #TODO: OVO JE PROIZVOLJNO - provjeriti koji Pin se zapravo moze koristiti
fan_pwm.freq(500)

sensor_pin = ADC(Pin(27))
counter = 0
temperature = 0
average_temperature = 0
CALIBRATION_OFFSET = -1790

def check_temperature(t):
    global sensor_pin, counter, temperature, average_temperature, CALIBRATION_OFFSET
    
    voltage = ((sensor_pin.read_u16() + CALIBRATION_OFFSET) / 65535) * 3.3
    print("voltage:",voltage)
    temperature += round(voltage * 100,1) #mozda bez -0.5
    #print("temperature=",temperature)
    counter += 1
    if counter == 10:
        average_temperature = temperature / 10
        counter = 0
        print("temperature=",average_temperature)
        #TODO: send temperature with mqtt
        temperature = 0

tim = Timer(period = 3000, mode = Timer.PERIODIC, callback = check_temperature)

def update_vu_meter(duty_u16): #TODO: Implementirati
    pass 

def set_fan_speed(duty_u16):
    pass
    #fan_pwm.duty_u16(duty_u16)
while True:
    pass