from machine import Pin, PWM, ADC, Timer
from time import sleep
from FanSpeedController import *
import network
import simple
from BusOut import *


# WiFi configuration
WIFI_SSID = "mirza"
WIFI_PASSWORD = "zakadiju"

# MQTT configuration
MQTT_SERVER = "broker.hivemq.com"
MQTT_TOPIC_TARGET_TEMP = b"Propuh-Pro/target_temp"
MQTT_TOPIC_CRITICAL_TEMP = b"Propuh-Pro/critical_temp"
MQTT_TOPIC_FAN_MODE = b"Propuh-Pro/fan_mode"
MQTT_TOPIC_MEASURED_TEMP = b"Propuh-Pro/measured_temp"

MQTT_CLIENT_NAME = "Propuh-Pro-Teren"

# Initialize network
print("Connecting to WiFi: ", WIFI_SSID)
WIFI = network.WLAN(network.STA_IF)
WIFI.active(True)
WIFI.config(pm = 0xa11140) # Disable powersave mode
WIFI.connect(WIFI_SSID, WIFI_PASSWORD)

# Wait until connected
while not WIFI.isconnected():
    pass

print("Connected to network!")
print("IP address:", WIFI.ifconfig()[0])


FAN_VU_METAR_LEDS = BusOut([4, 5, 6, 7, 8, 9])  # Tacno za picoETF

OVERHEATING_LED = Pin(
    11, Pin.OUT
)  # TODO: Treba da blinka ako je izmjerena temperatura >= kriticne temperature

# fan_pwm = PWM(Pin(1)) #TODO: OVO JE PROIZVOLJNO - provjeriti koji Pin se zapravo moze koristiti
# fan_pwm.freq(500)


LM35_PIN = ADC(Pin(27))
counter = 0
temp_sum = 0
measured_temp = 0
fan_controller = FanSpeedController(0, 0, FanMode())


def update_vu_meter(duty_u16):  # TODO: Implementirati
    pass


def set_fan_speed(duty_u16):
    pass
    # fan_pwm.duty_u16(duty_u16)


def message_arrived_fan_mode(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_mode(int(float(msg)))
    set_fan_speed(fan_controller.get_speed_u16)


def message_arrived_critical_temp(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_critical_temp(float(msg))
    set_fan_speed(fan_controller.get_speed_u16)


def message_arrived_target_temp(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_target_temp(float(msg))
    set_fan_speed(fan_controller.get_speed_u16)


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


def recive_data(timer):
    CLIENT.check_msg()


def send_data(measured_temp):
    publish = str(measured_temp)
    # buf = '{{"Measured temp":{}}}'.format(publish)
    CLIENT.publish(MQTT_TOPIC_MEASURED_TEMP, publish)


LM35_CALIBRATION_OFFSET = -1790


def measure_temp(timer):
    global LM35_PIN, counter, temp_sum, measured_temp, LM35_CALIBRATION_OFFSET

    voltage = ((LM35_PIN.read_u16() + LM35_CALIBRATION_OFFSET) / 65535) * 3.3
    print("voltage:", voltage)
    temp_sum += round(voltage * 100, 1)
    # print("temp=",temp)
    counter += 1
    if counter == 10:
        measured_temp = temp_sum / 10
        counter = 0
        print("temperature=", measured_temp)

        send_data(measured_temp)
        temp_sum = 0


CHECK_TEMP_TIMER = Timer(period=500, mode=Timer.PERIODIC, callback=measure_temp)
RECIVE_DATA_TIMER = Timer(period=5000, mode=Timer.PERIODIC, callback=recive_data)

while True:
    pass
