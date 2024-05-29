from machine import Pin
from time import ticks_ms, ticks_diff, sleep
from FanSpeedController import FanMode
from InterfaceMode import *

mode_button = Pin(18, Pin.IN)
increase_temp_button = Pin(19, Pin.IN)
decrease_temp_button = Pin(16, Pin.IN)
fan_button = Pin(17, Pin.IN)


DEBOUNCE_TIME_MS = 300

debounce = 0


def debouncing():
    global debounce
    if ticks_diff(ticks_ms(), debounce) < DEBOUNCE_TIME_MS:
        return False
    else:
        debounce = ticks_ms()
        return True


fan_mode = FanMode()
interface_mode = InterfaceMode()
current_temp = 0.0
target_temp = 22.0

STEP = 0
LIMIT = 0


def print_configuration():
    global fan_mode
    global target_temp

    fan_output = ""

    if fan_mode == FanMode.AUTO:
        fan_output = "AUTO"
    else:
        mode_outputs = {
            FanMode.OFF: "OOO",
            FanMode.SLOW: "#OO",
            FanMode.MEDIUM: "##O",
            FanMode.FAST: "###",
            FanMode.AUTO: "AUTO",
        }
        fan_output = mode_outputs.get(fan_mode.current_mode, "UNKNOWN")

    print()
    print()
    print("Target temp:", target_temp)
    print("Fan speed:", fan_output)


def change_mode(pin):
    global interface_mode
    if debouncing() == False:
        return
    interface_mode.switch()
    print_configuration()


def increase_temp(pin):
    global target_temp
    if debouncing() == False:
        return
    target_temp += 0.5  # dodati granice
    print_configuration()


def decrease_temp(pin):
    global target_temp
    if debouncing() == False:
        return
    target_temp -= 0.5  # dodati granice
    print_configuration()


def change_fan_speed(pin):
    global fan_mode
    if debouncing() == False:
        return
    fan_mode.next()
    print_configuration()


mode_button.irq(handler=change_mode, trigger=Pin.IRQ_RISING)
increase_temp_button.irq(handler=increase_temp, trigger=Pin.IRQ_RISING)
decrease_temp_button.irq(handler=decrease_temp, trigger=Pin.IRQ_RISING)
fan_button.irq(handler=change_fan_speed, trigger=Pin.IRQ_RISING)


print_configuration()
while True:
    pass
