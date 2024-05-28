from machine import Pin
from time import ticks_ms, ticks_diff, sleep

mode_button = Pin(17, Pin.IN)
increase_button = Pin(16, Pin.IN)
decrease_button = Pin(18, Pin.IN)
fan_button = Pin(19, Pin.IN)

class Mode():
    CONFIGURATION = 1
    OPERATIONAL = 2
    length = 2

class FanSpeed():
    OFF = 1
    SLOW = 2
    MEDIUM = 3
    FAST = 4
    AUTO = 5
    length = 5
fan_speeds = [1,2,3,4,5]    
current_fan_speed = FanSpeed.OFF
current_mode = Mode.CONFIGURATION
current_temp = 0.0
target_temp = 22.0
debounce = 0

STEP = 0
LIMIT = 0

def debouncing():
    global debounce
    if(ticks_diff(ticks_ms(),debounce) < 100):
        return False
    else:
        debounce = ticks_ms()
        return True


def change_mode(pin):
    global current_mode
    if(debouncing() == False):
        return
    current_mode = (current_mode + 1) % Mode.length
    print("MODE: ",current_mode)

def increase_temp(pin):
    global target_temp
    if(debouncing() == False):
        return
    target_temp += 0.5 #dodati granice
    print("TEMP: ",target_temp)

def decrease_temp(pin):
    global target_temp
    if(debouncing() == False):
        return
    target_temp -= 0.5 # dodati granice
    print("TEMP: ",target_temp)

def change_fan_speed(pin):
    global current_fan_speed
    if(debouncing() == False):
        return
    current_fan_speed = (current_fan_speed + 1) % FanSpeed.length
    print("SPEED: ",current_fan_speed)

mode_button.irq(handler=change_mode, trigger = Pin.IRQ_RISING)
increase_button.irq(handler=increase_temp, trigger = Pin.IRQ_RISING)
decrease_button.irq(handler=decrease_temp, trigger = Pin.IRQ_RISING)
fan_button.irq(handler=change_fan_speed, trigger = Pin.IRQ_RISING)

while True:
    print("a")
    sleep(0.1)
    pass

