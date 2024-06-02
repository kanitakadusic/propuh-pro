from machine import Pin, PWM, ADC, Timer
from time import sleep
from FanSpeedController import *
import network
import simple
from BusOut import *


# WiFi configuration
WIFI_SSID = "mirza"
WIFI_PASSWORD = "zakadiju"

# LM35 configuration
LM35_CALIBRATION_OFFSET = -1790
LM35_NUMBER_OF_SAMPLES = 10

# MQTT configuration
MQTT_SERVER = "broker.hivemq.com"
MQTT_CLIENT_NAME = "Propuh-Pro-Teren"

MQTT_TOPIC_TARGET_TEMP = b"Propuh-Pro/target_temp"
MQTT_TOPIC_CRITICAL_TEMP = b"Propuh-Pro/critical_temp"
MQTT_TOPIC_FAN_MODE = b"Propuh-Pro/fan_mode"
MQTT_TOPIC_MEASURED_TEMP = b"Propuh-Pro/measured_temp"


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

FAN_VU_METAR_LEDS = BusOut([4, 5, 6, 7, 8, 9])  # Tacno za picoETF

OVERHEATING_LED = Pin(11, Pin.OUT)
# TODO: Treba da blinka ako je izmjerena temperatura >= kriticne temperature

FAN_PWM = PWM(Pin(22))
FAN_PWM.freq(500)

LM35_SENSOR_PIN = ADC(Pin(28))

temp_sum = 0.0
measured_temp = 0.0
fan_controller = FanSpeedController(20, 30, 22)
fan_controller.set_current_temp(22)


sample_counter = 0

def check_temperature(t):
    global LM35_SENSOR_PIN, sample_counter, temp_sum, measured_temp, LM35_CALIBRATION_OFFSET, fan_controller

    voltage = ((LM35_SENSOR_PIN.read_u16() + LM35_CALIBRATION_OFFSET) / 65535) * 3.3
    # print("voltage:",voltage)
    temp_sum += round(voltage * 100, 1)
    # print("temp=",temp)
    sample_counter += 1
    if sample_counter == LM35_NUMBER_OF_SAMPLES:
        measured_temp = temp_sum / 10
        sample_counter = 0
        temp_sum = 0

        fan_controller.set_current_temp(measured_temp)

        speed = int(fan_controller.get_speed_u16())
        light = int(fan_controller.get_speed_binary())

        set_fan_speed(speed)
        update_vu_meter(light)

        print("temperature=", measured_temp)
        print("brzina=", fan_controller.get_speed_u16())

        send_data(measured_temp)


def update_vu_meter(binary_number):  # TODO: Implementirati
    global FAN_VU_METAR_LEDS
    FAN_VU_METAR_LEDS.set_value(binary_number)


def set_fan_speed(duty_u16):
    FAN_PWM.duty_u16(duty_u16)


def message_arrived_fan_mode(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_mode(FanMode(int(float(msg))))
    speed = int(fan_controller.get_speed_u16())
    light = int(fan_controller.get_speed_binary())
    set_fan_speed(speed)
    update_vu_meter(light)


def message_arrived_critical_temp(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_critical_temp(float(msg))
    speed = int(fan_controller.get_speed_u16())
    light = int(fan_controller.get_speed_binary())
    set_fan_speed(speed)
    update_vu_meter(light)


def message_arrived_target_temp(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_target_temp(float(msg))
    speed = int(fan_controller.get_speed_u16())
    light = int(fan_controller.get_speed_binary())
    set_fan_speed(speed)
    update_vu_meter(light)


def custom_dispatcher(topic, msg):
    if topic == MQTT_TOPIC_FAN_MODE:
        message_arrived_fan_mode(topic, msg)
    elif topic == MQTT_TOPIC_CRITICAL_TEMP:
        message_arrived_critical_temp(topic, msg)
    elif topic == MQTT_TOPIC_TARGET_TEMP:
        message_arrived_target_temp(topic, msg)


# Connect to MQTT broker
CLIENT = simple.MQTTClient(client_id=MQTT_CLIENT_NAME, server=MQTT_SERVER, port=1883)
CLIENT.connect()

# Subscribe to topics
CLIENT.set_callback(custom_dispatcher)
CLIENT.subscribe(MQTT_TOPIC_FAN_MODE)
CLIENT.subscribe(MQTT_TOPIC_CRITICAL_TEMP)
CLIENT.subscribe(MQTT_TOPIC_TARGET_TEMP)


def send_data(measured_temp):
    publish = str(measured_temp)
    CLIENT.publish(MQTT_TOPIC_MEASURED_TEMP, publish)


def recive_data():
    CLIENT.check_msg()
    CLIENT.check_msg()
    CLIENT.check_msg()


CHECK_TEMP_TIMER = Timer(period=500, mode=Timer.PERIODIC, callback=check_temperature)
RECIVE_DATA_TIMER = Timer(period=1000, mode=Timer.PERIODIC, callback=recive_data)


while True:
    pass
