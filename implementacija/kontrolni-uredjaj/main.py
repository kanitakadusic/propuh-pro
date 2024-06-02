from machine import Pin, I2C, Timer
from time import ticks_ms, ticks_diff
from FanMode import *
from InterfaceMode import *
from utime import sleep
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd
import network
import simple

# WiFi configuration
WIFI_SSID = "Malisevic"
WIFI_PASSWORD = "Ari_bjelov"

# MQTT configuration
MQTT_SERVER = "broker.hivemq.com"
MQTT_TOPIC_TARGET_TEMP = b"Propuh-Pro/target_temp"
MQTT_TOPIC_CRITICAL_TEMP = b"Propuh-Pro/critical_temp"
MQTT_TOPIC_FAN_MODE = b"Propuh-Pro/fan_mode"
MQTT_TOPIC_MEASURED_TEMP = b"Propuh-Pro/measured_temp"

MQTT_CLIENT_NAME = "Propuh-Pro-Control"

# Initialize network
print("Connecting to WiFi: ", WIFI_SSID)
WIFI = network.WLAN(network.STA_IF)
WIFI.active(True)
WIFI.config(pm=0xA11140)  # Disable powersave mode
WIFI.connect(WIFI_SSID, WIFI_PASSWORD)

# Wait until connected
while not WIFI.isconnected():
    pass

print("Connected to network!")
print("IP address:", WIFI.ifconfig()[0])

NEXT_MODE_BUTTON = Pin(18, Pin.IN)
PREVIOUS_MODE_BUTTON = Pin(17, Pin.IN)
INCREASE_BUTTON = Pin(19, Pin.IN)
DECRESE_BUTTON = Pin(16, Pin.IN)


# Display configuration
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

I2C_BUS = I2C(1, sda=Pin(26), scl=Pin(27), freq=400000)
LCD_DISPLAY = I2cLcd(I2C_BUS, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)


# Debounce configuration
DEBOUNCE_TIME_MS = 300
debounce = 0


def debouncing():
    global debounce
    if ticks_diff(ticks_ms(), debounce) < DEBOUNCE_TIME_MS:
        return False
    else:
        debounce = ticks_ms()
        return True


# Main program
fan_mode = FanMode()
interface_mode = InterfaceMode()
current_temp = 0.0
target_temp = 22.0
critical_temp = 35.0

MINIMUM_TEMP_DIFFERENCE = 5.0


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
        if critical_temp - target_temp > MINIMUM_TEMP_DIFFERENCE:
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
        if critical_temp - target_temp > MINIMUM_TEMP_DIFFERENCE:
            critical_temp -= 0.5
    elif interface_mode.get_mode() == InterfaceMode.FAN_CONFIG:
        fan_mode.previous()

    print_configuration()


# Input triggers
NEXT_MODE_BUTTON.irq(handler=next_mode, trigger=Pin.IRQ_RISING)
INCREASE_BUTTON.irq(handler=increase_value, trigger=Pin.IRQ_RISING)
DECRESE_BUTTON.irq(handler=decrease_value, trigger=Pin.IRQ_RISING)
PREVIOUS_MODE_BUTTON.irq(handler=previous_mode, trigger=Pin.IRQ_RISING)


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
    print("Mode:", interface_mode.get_mode_name())

    current_mode = interface_mode.get_mode()

    if current_mode == InterfaceMode.TARGET_TEMP_CONFIG:
        output = "Target temp:\n" + str(target_temp) + chr(223) + "C"
        print(output)
        LCD_DISPLAY.clear()
        LCD_DISPLAY.putstr(output)

    elif current_mode == InterfaceMode.CRITICAL_TEMP_CONFIG:
        output = "Critical temp:\n" + str(critical_temp) + chr(223) + "C"
        print(output)
        LCD_DISPLAY.clear()
        LCD_DISPLAY.putstr(output)

    elif current_mode == InterfaceMode.FAN_CONFIG:
        output = "Fan speed:\n" + str(fan_output)
        print(output)
        LCD_DISPLAY.clear()
        LCD_DISPLAY.putstr(output)

    else:
        output = (
            "Current temp:\n"
            + str(round_to_nearest_half(current_temp))
            + chr(223)
            + "C"
        )
        print(output)
        LCD_DISPLAY.clear()
        LCD_DISPLAY.putstr(output)


print_configuration()


def message_arrived_measured_temp(topic, msg):
    global current_temp
    
    print()
    print()
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    current_temp = float(msg)
    print_configuration()


# Connect to MQTT broker
CLIENT = simple.MQTTClient(client_id=MQTT_CLIENT_NAME, server=MQTT_SERVER, port=1883)
CLIENT.connect()

CLIENT.set_callback(message_arrived_measured_temp)
CLIENT.subscribe(MQTT_TOPIC_MEASURED_TEMP)


def send_data(timer):
    publish = str(fan_mode.get_mode())
    CLIENT.publish(MQTT_TOPIC_FAN_MODE, publish)

    publish = str(target_temp)
    CLIENT.publish(MQTT_TOPIC_TARGET_TEMP, publish)

    publish = str(critical_temp)
    CLIENT.publish(MQTT_TOPIC_CRITICAL_TEMP, publish)

    print("Sent!")


def recive_data(timer):
    CLIENT.check_msg()


SEND_DATA_TIMER = Timer(period=5000, mode=Timer.PERIODIC, callback=send_data)
RECIVE_DATA_TIMER = Timer(period=500, mode=Timer.PERIODIC, callback=recive_data)


def round_to_nearest_half(value) -> float:
    return round(value * 2) / 2


while True:
    pass
