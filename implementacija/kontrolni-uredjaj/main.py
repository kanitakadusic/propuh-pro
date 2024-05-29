from machine import Pin
from time import ticks_ms, ticks_diff, sleep

mode_button = Pin(18, Pin.IN)
increase_button = Pin(19, Pin.IN)
decrease_button = Pin(16, Pin.IN)
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


class InterfaceMode:
    CONFIGURATION = 0
    OPERATIONAL = 1
    length = 2


class FanMode:
    OFF = 0
    SLOW = 1
    MEDIUM = 2
    FAST = 3
    AUTO = 4
    length = 5


current_fan_mode = FanMode.OFF
current_mode = InterfaceMode.CONFIGURATION
current_temp = 0.0
target_temp = 22.0

STEP = 0
LIMIT = 0


def print_configuration():
    global current_fan_mode
    global target_temp

    fan_output = ""

    if current_fan_mode == FanMode.AUTO:
        fan_output = "AUTO"
    else:
        for i in range(current_fan_mode):
            fan_output += "#"
        for i in range(FanMode.length - current_fan_mode - 2):
            fan_output += "O"

    print()
    print()
    print("Target temp:", target_temp)
    print("Fan speed:", fan_output)


def change_mode(pin):
    global current_mode
    if debouncing() == False:
        return
    current_mode = (current_mode + 1) % InterfaceMode.length
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
    global current_fan_mode
    if debouncing() == False:
        return
    current_fan_mode = (current_fan_mode + 1) % FanMode.length
    print_configuration()


mode_button.irq(handler=change_mode, trigger=Pin.IRQ_RISING)
increase_button.irq(handler=increase_temp, trigger=Pin.IRQ_RISING)
decrease_button.irq(handler=decrease_temp, trigger=Pin.IRQ_RISING)
fan_button.irq(handler=change_fan_speed, trigger=Pin.IRQ_RISING)


print_configuration()
while True:
    pass
