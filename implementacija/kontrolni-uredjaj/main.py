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
WIFI_SSID = "Edge 40 Neo - Haris"
WIFI_PASSWORD = "nope1234"

# MQTT configuration
MQTT_SERVER = "broker.hivemq.com"
MQTT_TOPIC_TARGET_TEMP = b"Propuh-Pro/target_temp"
MQTT_TOPIC_CRITICAL_TEMP = b"Propuh-Pro/critical_temp"
MQTT_TOPIC_FAN_MODE = b"Propuh-Pro/fan_mode"
MQTT_TOPIC_MEASURED_TEMP = b"Propuh-Pro/measured_temp"

MQTT_CLIENT_NAME = "Propuh-Pro-Control"

# Initialize network
print("Connecting to WiFi: ", WIFI_SSID)
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

# Wait until connected
while not wifi.isconnected():
    pass

print("Connected to network!")
print("IP address:", wifi.ifconfig()[0])

next_mode_button = Pin(18, Pin.IN)
previous_mode_button = Pin(17, Pin.IN)
increase_button = Pin(19, Pin.IN)
decrease_button = Pin(16, Pin.IN)


# Display configuration
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)


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
next_mode_button.irq(handler=next_mode, trigger=Pin.IRQ_RISING)
increase_button.irq(handler=increase_value, trigger=Pin.IRQ_RISING)
decrease_button.irq(handler=decrease_value, trigger=Pin.IRQ_RISING)
previous_mode_button.irq(handler=previous_mode, trigger=Pin.IRQ_RISING)


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


print_configuration()


def message_arrived_measured_temp(topic, msg):
    global current_temp
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    current_temp = float(msg)
    print_configuration()


# Connect to MQTT broker
client = simple.MQTTClient(client_id=MQTT_CLIENT_NAME, server=MQTT_SERVER, port=1883)
client.connect()

client.set_callback(message_arrived_measured_temp)
client.subscribe(MQTT_TOPIC_MEASURED_TEMP)


def send_data(timer):
    publish = str(fan_mode.get_mode())
    client.publish(MQTT_TOPIC_FAN_MODE, publish)

    publish = str(target_temp)
    client.publish(MQTT_TOPIC_TARGET_TEMP, publish)

    publish = str(critical_temp)
    client.publish(MQTT_TOPIC_CRITICAL_TEMP, publish)

    print("Sent!")


def recive_data(timer):
    client.check_msg()


SEND_DATA_TIMER = Timer(period=5000, callback=send_data, mode=Timer.PERIODIC)
RECIVE_DATA_TIMER = Timer(period=500, callback=recive_data, mode=Timer.PERIODIC)


while True:
    pass
