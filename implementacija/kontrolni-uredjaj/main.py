from machine import Pin, I2C
from time import ticks_ms, ticks_diff
from FanSpeedController import *
from InterfaceMode import *
from utime import sleep
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

next_mode_button = Pin(18, Pin.IN)
previous_mode_button = Pin(17, Pin.IN)
increase_button = Pin(19, Pin.IN)
decrease_button = Pin(16, Pin.IN)


DEBOUNCE_TIME_MS = 300
debounce = 0


# TODO: Mozda ekstraktovati

# Konfiguracija za displej
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)


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
critical_temp = 35.0


def print_configuration():
    fan_output = ""

    if fan_mode == FanMode.AUTO:
        fan_output = "AUTO"
    else:
        mode_outputs = {
            FanMode.OFF: "O O O",
            FanMode.SLOW: "# O O",
            FanMode.MEDIUM: "# # O",
            FanMode.FAST: "# # #",
            FanMode.AUTO: "AUTO",
        }
        fan_output = mode_outputs.get(fan_mode.current_mode, "UNKNOWN")

    print()
    print()
    print("Mode:", interface_mode.get_mode_name())

    current_mode = interface_mode.get_mode()

    if current_mode == InterfaceMode.TARGET_TEMP_CONFIG:
        output = "Target temp:\n" + str(target_temp) + chr(223) + "C"
        print(output)
        lcd.clear()
        lcd.putstr(output)

    elif current_mode == InterfaceMode.CRITICAL_TEMP_CONFIG:
        output = "Critical temp:\n" + str(critical_temp) + chr(223) + "C"
        print(output)
        lcd.clear()
        lcd.putstr(output)

    elif current_mode == InterfaceMode.FAN_CONFIG:
        output = "Fan speed:\n" + str(fan_output)
        print(output)
        lcd.clear()
        lcd.putstr(output)

    else:
        output = "Current temp:\n" + str(current_temp) + chr(223) + "C"
        print(output)
        lcd.clear()
        lcd.putstr(output)


def next_mode(pin):

    if debouncing() == False:
        return

    interface_mode.next()
    print_configuration()


def previous_mode(pin):

    if debouncing() == False:
        return

    interface_mode.previous()
    print_configuration()


def increase_value(pin):
    global target_temp
    global critical_temp

    if debouncing() == False:
        return

    if interface_mode.get_mode() == InterfaceMode.TARGET_TEMP_CONFIG:
        target_temp += 0.5
    elif interface_mode.get_mode() == InterfaceMode.CRITICAL_TEMP_CONFIG:
        critical_temp += 0.5
    elif interface_mode.get_mode() == InterfaceMode.FAN_CONFIG:
        fan_mode.next()

    print_configuration()


def decrease_value(pin):
    global target_temp
    global critical_temp

    if debouncing() == False:
        return

    if interface_mode.get_mode() == InterfaceMode.TARGET_TEMP_CONFIG:
        target_temp -= 0.5
    elif interface_mode.get_mode() == InterfaceMode.CRITICAL_TEMP_CONFIG:
        critical_temp -= 0.5
    elif interface_mode.get_mode() == InterfaceMode.FAN_CONFIG:
        fan_mode.previous()

    print_configuration()


next_mode_button.irq(handler=next_mode, trigger=Pin.IRQ_RISING)
increase_button.irq(handler=increase_value, trigger=Pin.IRQ_RISING)
decrease_button.irq(handler=decrease_value, trigger=Pin.IRQ_RISING)
previous_mode_button.irq(handler=previous_mode, trigger=Pin.IRQ_RISING)


print_configuration()
while True:
    pass
