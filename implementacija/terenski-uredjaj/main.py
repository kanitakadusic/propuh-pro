from machine import Pin, PWM, ADC, Timer
from time import sleep, ticks_ms, ticks_diff
from FanSpeedController import *
import network
import simple
from BusOut import *


# WiFi konfiguracija 
WIFI_SSID = "Haris HotSpot"
WIFI_PASSWORD = "nope1234"

# MQTT konfiguracija
MQTT_SERVER = "broker.hivemq.com"
MQTT_CLIENT_NAME = "Propuh-Pro-Teren"

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

while not WIFI.isconnected():
    pass

print("Connected to network!")
print("IP address:", WIFI.ifconfig()[0])

#Glavni program - početna konfiguracija

FAN_VU_METER_LEDS = BusOut([4, 5, 6, 7, 8, 9])

OVERHEATING_LED = Pin(11, Pin.OUT)

FAN_PWM = PWM(Pin(22))
FAN_PWM.freq(500)

ALARM_PWM = PWM(Pin(27))
ALARM_PWM.freq(1000)

ALARM_OFF_PIN = Pin(0, Pin.IN)

# LM35 konfiguracija
LM35_CALIBRATION_OFFSET = -1200
LM35_NUMBER_OF_SAMPLES = 10
LM35_SENSOR_PIN = ADC(Pin(28))

temp_sum = 0.0
measured_temp = 0.0
sample_counter = 0
alarm = 0

# FanSpeedController sadrži sve neophodne informacije za rad sistema
fan_controller = FanSpeedController(22, 30, 22)

DEBOUNCE_TIME_MS = 300
debounce = 0


def debouncing():
    global debounce
    if ticks_diff(ticks_ms(), debounce) < DEBOUNCE_TIME_MS:
        return False
    else:
        debounce = ticks_ms()
        return True

# Ažuriranje snage ventilatora i stanja LED
def update_system():
    global alarm, fan_controller

    # Uzimanje trenutnih podataka unutar kontrolera
    speed = int(fan_controller.get_speed_u16())
    light = int(fan_controller.get_led_binary())

    # Ukoliko se alarm treba upaliti, a prethodno nije bio
    if fan_controller.is_alarm() and alarm == 0:
        turn_alarm_on()

    # Ukoliko je alarm upaljen, a treba se ugasiti
    elif (not fan_controller.is_alarm()) and alarm == 1:
        turn_alarm_off(ALARM_OFF_PIN)

    set_fan_speed(speed)
    update_vu_meter(light)

# Očitavanje trenutne temperature
def check_temperature(t):
    global sample_counter, temp_sum, measured_temp, fan_controller

    voltage = ((LM35_SENSOR_PIN.read_u16() + LM35_CALIBRATION_OFFSET) / 65535) * 3.3
    temp_sum += round(voltage * 100, 1)
    sample_counter += 1

    # Uzima se prosjek
    if sample_counter == LM35_NUMBER_OF_SAMPLES:
        measured_temp = temp_sum / LM35_NUMBER_OF_SAMPLES

        sample_counter = 0
        temp_sum = 0
        print("Average temperature=", measured_temp)
        
        #Ažuriranje podataka unutar kontrolera
        fan_controller.set_current_temp(measured_temp)
        
        # Slanje izmjerene temperature
        publish = str(measured_temp)
        CLIENT.publish(MQTT_TOPIC_MEASURED_TEMP, publish)

        update_system()

# Paljenje/gašenje LED i emitovanje zvuka
def toggle_alarm(t):
    global alarm

    if OVERHEATING_LED.value() == 1:
        OVERHEATING_LED.off()
        ALARM_PWM.duty_u16(45000)
    else:
        OVERHEATING_LED.on()
        ALARM_PWM.duty_u16(10000)

# Klikom na taster se gasi alarm
def turn_alarm_off(pin):
    global fan_controller, measured_temp

    fan_controller.turn_alarm_off()
    ALARM_PWM.duty_u16(0)
    OVERHEATING_LED.off()

    # Deinicijalizira se tajmer za alarm 
    ALARM_TIMER.deinit()

# Postavlja se brzina ventilatora putem PWM izlaza
def set_fan_speed(duty_u16):
    FAN_PWM.duty_u16(duty_u16)

# Ažuriranje LED
def update_vu_meter(number):
    FAN_VU_METER_LEDS.set_value(number)

# Paljenje alarma
def turn_alarm_on():
    global ALARM_TIMER, alarm, OVERHEATING_LED, ALARM_PWM

    alarm = 1
    OVERHEATING_LED.on()
    ALARM_PWM.duty_u16(3000)

    # Inicijalizira se tajmer za paljenje/gašenje LED i emitovanje zvuka
    ALARM_TIMER = Timer(period=500, mode=Timer.PERIODIC, callback=toggle_alarm)

# Primljena nova vrijednost stanja ventilatora preko MQTT
def message_arrived_fan_mode(topic, msg):
    global fan_controller

    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_fan_mode(FanMode(int(float(msg))))

    update_system()

# Primljena nova vrijednost kritične temperature
def message_arrived_critical_temp(topic, msg):
    global fan_controller

    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_critical_temp(float(msg))

    update_system()

# Primljena nova vrijednost željene temperature
def message_arrived_target_temp(topic, msg):
    global fan_controller

    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_target_temp(float(msg))

    update_system()

# Filtriranje primljenih poruka
def custom_dispatcher(topic, msg):
    
    if topic == MQTT_TOPIC_FAN_MODE:
        message_arrived_fan_mode(topic, msg)
    elif topic == MQTT_TOPIC_CRITICAL_TEMP:
        message_arrived_critical_temp(topic, msg)
    elif topic == MQTT_TOPIC_TARGET_TEMP:
        message_arrived_target_temp(topic, msg)


# Povezivanje na MQTT broker
CLIENT = simple.MQTTClient(client_id=MQTT_CLIENT_NAME, server=MQTT_SERVER, port=1883)
CLIENT.connect()

# Pretplata na teme
CLIENT.set_callback(custom_dispatcher)
CLIENT.subscribe(MQTT_TOPIC_FAN_MODE)
CLIENT.subscribe(MQTT_TOPIC_CRITICAL_TEMP)
CLIENT.subscribe(MQTT_TOPIC_TARGET_TEMP)

# Primanje podataka sa MQTT
def recieve_data(t):
    CLIENT.check_msg()
    CLIENT.check_msg()
    CLIENT.check_msg()

# no operation
def nop(t):
    pass

# Tajmer za očitavanje vrijednosti LM35
CHECK_TEMP_TIMER = Timer(period=500, mode=Timer.PERIODIC, callback=check_temperature)
# Tajmer za primanje podataka
RECIEVE_DATA_TIMER = Timer(period=1000, mode=Timer.PERIODIC, callback=recieve_data)

# Klikom na taster se gasi alarm
ALARM_OFF_PIN.irq(handler=turn_alarm_off, trigger=Pin.IRQ_RISING)
ALARM_TIMER = Timer(period=100, mode=Timer.ONE_SHOT, callback=nop)

while True:
    pass