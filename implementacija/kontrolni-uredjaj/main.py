from machine import Pin, I2C, Timer
from time import ticks_ms, ticks_diff
from FanSpeedController import *
from InterfaceMode import *
from utime import sleep
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd
import network
import simple

# WiFi configuration
wifi_ssid = "Edge 40 Neo - Haris"
wifi_password = "nope1234"

# MQTT configuration
mqtt_server = "broker.hivemq.com"
mqtt_topic_target_temp = b"Propuh-Pro/target_temp"
mqtt_topic_critical_temp = b"Propuh-Pro/critical_temp"
mqtt_topic_fan_mode = b"Propuh-Pro/fan_mode"
mqtt_topic_measured_temp = b"Propuh-Pro/measured_temp"

mqtt_client_name = "Propuh-Pro-Control"

# Initialize network
print("Connecting to WiFi: ", wifi_ssid)
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(wifi_ssid, wifi_password)

# Wait until connected
while not wifi.isconnected():
    pass

print("Connected to network!")
print("IP address:", wifi.ifconfig()[0])

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

def message_arrived_measured_temp(topic, msg):
    global current_temp
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    current_temp = float(msg)
    print_configuration()

# Connect to MQTT broker
client = simple.MQTTClient(client_id=mqtt_client_name, server=mqtt_server, port=1883)
client.connect()

client.set_callback(message_arrived_measured_temp)
client.subscribe(mqtt_topic_measured_temp)

def send_data(t):
    publish = str(fan_mode.get_mode())
    client.publish(mqtt_topic_fan_mode, publish)

    publish = str(target_temp)
    client.publish(mqtt_topic_target_temp, publish)

    publish = str(critical_temp)
    client.publish(mqtt_topic_critical_temp, publish)
    
    
    
    print("Sent!")
    

t = Timer(period=10000, callback=send_data, mode=Timer.PERIODIC)


while True:
    client.check_msg()
    sleep(0.5)
    pass

