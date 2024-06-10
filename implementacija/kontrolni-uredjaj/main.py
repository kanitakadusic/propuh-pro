from machine import Pin, I2C, Timer
from time import ticks_ms, ticks_diff
from FanMode import *
from InterfaceMode import *
from utime import sleep
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd
import network
import simple

# Display konfiguracija
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

I2C_BUS = I2C(1, sda=Pin(26), scl=Pin(27), freq=400000)
LCD_DISPLAY = I2cLcd(I2C_BUS, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

# WiFi konfiguracija 
WIFI_SSID = "mirza"
WIFI_PASSWORD = "zakadiju"

# MQTT konfiguracija
MQTT_SERVER = "broker.hivemq.com"
MQTT_CLIENT_NAME = "Propuh-Pro-Control"

MQTT_TOPIC_TARGET_TEMP = b"Propuh-Pro/target_temp"
MQTT_TOPIC_CRITICAL_TEMP = b"Propuh-Pro/critical_temp"
MQTT_TOPIC_FAN_MODE = b"Propuh-Pro/fan_mode"
MQTT_TOPIC_MEASURED_TEMP = b"Propuh-Pro/measured_temp"


# Povezivanje na internet
print("Connecting to WiFi: ", WIFI_SSID)
WIFI = network.WLAN(network.STA_IF)
WIFI.active(True)
WIFI.config(pm=0xA11140) 
WIFI.connect(WIFI_SSID, WIFI_PASSWORD)

LCD_DISPLAY.putstr("Connecting...")

while not WIFI.isconnected():
    pass

print("Connected to network!")
print("IP address:", WIFI.ifconfig()[0])

# Glavni program - početna konfiguracija
NEXT_MODE_BUTTON = Pin(16, Pin.IN)
PREVIOUS_MODE_BUTTON = Pin(19, Pin.IN)
INCREASE_BUTTON = Pin(17, Pin.IN)
DECRESE_BUTTON = Pin(18, Pin.IN)

    # Dozvoljena razlika željene i kritične temperature
MINIMUM_TEMP_DIFFERENCE = 5.0

DEBOUNCE_TIME_MS = 300

fan_mode = FanMode()
interface_mode = InterfaceMode()
current_temp = 22.0
target_temp = 21.0
critical_temp = 35.0

debounce = 0
debounce_value_change = 0
    # Da li se u toku rada programa pojavio alarm
alarm = False
    # Da li je trenutno aktivan alarm 
alarm_now = False


def debouncing():
    global debounce
    if ticks_diff(ticks_ms(), debounce) < DEBOUNCE_TIME_MS:
        return False
    else:
        debounce = ticks_ms()
        return True


def value_change_debouncing():
    global debounce_value_change
    if ticks_diff(ticks_ms(), debounce_value_change) < DEBOUNCE_TIME_MS:
        return False
    else:
        debounce_value_change = ticks_ms()
        return True

def next_mode(pin):
    global alarm_now, interface_mode

    if debouncing() == False:
        return
    
    # Prekid alarma ukoliko je isti aktiviran
    alarm_now = False
    interface_mode.next()
    print_configuration()

def previous_mode(pin):
    global alarm_now, interface_mode

    if debouncing() == False:
        return
    
    # Prekid alarma ukoliko je isti aktiviran
    alarm_now = False
    interface_mode.previous()
    print_configuration()

def increase_value(pin):
    global target_temp
    global critical_temp
    global alarm_now
    if debouncing() == False or value_change_debouncing() == False:
        return

    # Prekid alarma ukoliko je isti aktiviran
    alarm_now = False

    # Da li su temperature u dozvoljenom opsegu
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
    global alarm_now

    if debouncing() == False or value_change_debouncing() == False:
        return
    
    # Prekid alarma ukoliko je isti aktiviran
    alarm_now = False

    # Da li su temperature u dozvoljenom opsegu
    if interface_mode.get_mode() == InterfaceMode.TARGET_TEMP_CONFIG:
        target_temp -= 0.5
    elif interface_mode.get_mode() == InterfaceMode.CRITICAL_TEMP_CONFIG:
        if critical_temp - target_temp > MINIMUM_TEMP_DIFFERENCE:
            critical_temp -= 0.5
    elif interface_mode.get_mode() == InterfaceMode.FAN_CONFIG:
        fan_mode.previous()

    print_configuration()

# Aktivacija alarma i prikaz upozorenja
def print_alarm():
    global alarm, alarm_now

    alarm = True
    alarm_now = True
    alarm_blink_counter = 0

    while alarm_blink_counter <= 5 and alarm_now:
        LCD_DISPLAY.clear()
        sleep(0.5)
        LCD_DISPLAY.putstr(
            "TEMPERATURE     CRITICAL: " + str(current_temp) + chr(223) + "C"
        )
        sleep(0.8)

        alarm_blink_counter += 1

# Ispis informacija na display
def print_configuration():
    
    # Ukoliko je alarm aktivan neće se ažurirati display
    if alarm_now:
        return

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
        output = "Target temp:    " + str(target_temp) + chr(223) + "C"
        print(output)
        LCD_DISPLAY.clear()
        LCD_DISPLAY.putstr(output)

    elif current_mode == InterfaceMode.CRITICAL_TEMP_CONFIG:
        output = "Critical temp:  " + str(critical_temp) + chr(223) + "C"
        print(output)
        LCD_DISPLAY.clear()
        LCD_DISPLAY.putstr(output)

    elif current_mode == InterfaceMode.FAN_CONFIG:
        output = "Fan speed:      " + str(fan_output)

        if fan_mode.get_mode() != FanMode.AUTO:
            output = output + "   " + fan_mode.get_mode_name()

        print(output)
        LCD_DISPLAY.clear()
        LCD_DISPLAY.putstr(output)

    else:
        output = "Current temp:   " + str(current_temp) + chr(223) + "C"
        print(output)
        LCD_DISPLAY.clear()
        LCD_DISPLAY.putstr(output)

# Primljena nova vrijednost izmjerene temperature
def message_arrived_measured_temp(topic, msg):
    global current_temp

    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    current_temp = round_to_nearest_half(float(msg))

    if current_temp >= critical_temp and alarm == False:
        print_alarm()
        return

    if value_change_debouncing() == False:
        return

    print_configuration()

# Korak za temperaturu je 0.5
def round_to_nearest_half(value) -> float:
    return round(value * 2) / 2

# Primljena nova vrijednost željene temperature
def message_arrived_target_temp(topic, msg):
    global target_temp

    print("Message arrived on topic:", topic)
    print("Payload:", msg)

    # Ukoliko primljena željena temp. nije validna ne ažurira se vrijednost
    if critical_temp - MINIMUM_TEMP_DIFFERENCE < float(msg):
        return

    target_temp = round_to_nearest_half(float(msg))

    if value_change_debouncing() == False:
        return

    print_configuration()

# Primljena nova vrijednost kritične temperature
def message_arrived_critical_temp(topic, msg):
    global critical_temp

    print("Message arrived on topic:", topic)
    print("Payload:", msg)

    # Ukoliko primljena kritična temp. nije validna ne ažurira se vrijednost
    if target_temp + MINIMUM_TEMP_DIFFERENCE > float(msg):
        return

    critical_temp = round_to_nearest_half(float(msg))
    if value_change_debouncing() == False:
        return
    print_configuration()

# Primljena nova vrijednost za fan mode
def message_arrived_fan_mode(topic, msg):
    global fan_mode

    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_mode.current_mode = int(msg)

    if value_change_debouncing() == False:
        return
    print_configuration()

# Filtriranje primljenih poruka
def custom_dispatcher(topic, msg):

    if topic == MQTT_TOPIC_MEASURED_TEMP:
        message_arrived_measured_temp(topic, msg)
    elif topic == MQTT_TOPIC_TARGET_TEMP:
        message_arrived_target_temp(topic, msg)
    elif topic == MQTT_TOPIC_CRITICAL_TEMP:
        message_arrived_critical_temp(topic, msg)
    elif topic == MQTT_TOPIC_FAN_MODE:
        message_arrived_fan_mode(topic, msg)


# Povezivanje na MQTT broker
CLIENT = simple.MQTTClient(client_id=MQTT_CLIENT_NAME, server=MQTT_SERVER, port=1883)
CLIENT.connect()

CLIENT.set_callback(custom_dispatcher)

# Pretplata na teme
CLIENT.subscribe(MQTT_TOPIC_MEASURED_TEMP)
CLIENT.subscribe(MQTT_TOPIC_TARGET_TEMP)
CLIENT.subscribe(MQTT_TOPIC_CRITICAL_TEMP)
CLIENT.subscribe(MQTT_TOPIC_FAN_MODE)

# Slanje podataka putem MQTT
def send_data(timer):
    publish = str(fan_mode.get_mode())
    CLIENT.publish(MQTT_TOPIC_FAN_MODE, publish)

    publish = str(target_temp)
    CLIENT.publish(MQTT_TOPIC_TARGET_TEMP, publish)

    publish = str(critical_temp)
    CLIENT.publish(MQTT_TOPIC_CRITICAL_TEMP, publish)

    print("Sent!")

# Provjera pristiglih podataka na MQTT
def recieve_data(timer):
    CLIENT.check_msg()
    CLIENT.check_msg()
    CLIENT.check_msg()
    CLIENT.check_msg()


# Tajmeri za slanje/primanje podataka
SEND_DATA_TIMER = Timer(period=3000, mode=Timer.PERIODIC, callback=send_data)
RECIEVE_DATA_TIMER = Timer(period=500, mode=Timer.PERIODIC, callback=recieve_data)

# Postavljanje hardverskih prekida
NEXT_MODE_BUTTON.irq(handler=next_mode, trigger=Pin.IRQ_RISING)
INCREASE_BUTTON.irq(handler=increase_value, trigger=Pin.IRQ_RISING)
DECRESE_BUTTON.irq(handler=decrease_value, trigger=Pin.IRQ_RISING)
PREVIOUS_MODE_BUTTON.irq(handler=previous_mode, trigger=Pin.IRQ_RISING)

print_configuration()

while True:
    pass
