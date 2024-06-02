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

fan_vu_meter_leds = BusOut([4, 5, 6, 7, 8, 9]) # Tacno za picoETF

overheating_led = Pin(11, Pin.OUT) #TODO: Treba da blinka ako je izmjerena temperatura >= kriticne temperature 

fan_pwm = PWM(Pin(22)) #TODO: OVO JE PROIZVOLJNO - provjeriti koji Pin se zapravo moze koristiti
fan_pwm.freq(500)


sensor_pin = ADC(Pin(28))
counter = 0
temp_sum = 0
measured_temp = 0
fan_controller = FanSpeedController(20,30,22)
fan_controller.set_current_temp(22)
CALIBRATION_OFFSET = -1790

def check_temperature(t):
    global sensor_pin, counter, temp_sum, measured_temp, CALIBRATION_OFFSET, fan_controller
    
    voltage = ((sensor_pin.read_u16() + CALIBRATION_OFFSET) / 65535) * 3.3
    #print("voltage:",voltage)
    temp_sum += round(voltage * 100,1)
    #print("temp=",temp)
    counter += 1
    if counter == 10:
        measured_temp = temp_sum / 10
        counter = 0
        temp_sum = 0
        print("temperature=", measured_temp)
        fan_controller.set_current_temp(measured_temp)
        speed = int(fan_controller.get_speed_u16())
        light = int(fan_controller.get_speed_binary())
        set_fan_speed(speed)
        update_vu_meter(light)
        print("brzina=",fan_controller.get_speed_u16())
        publish = str(measured_temp)
        CLIENT.publish(MQTT_TOPIC_MEASURED_TEMP, publish)

tim = Timer(period = 500, mode = Timer.PERIODIC, callback = check_temperature)

def update_vu_meter(binary_number): #TODO: Implementirati
    global fan_vu_meter_leds
    fan_vu_meter_leds.set_value(binary_number)
     
def set_fan_speed(duty_u16):
    fan_pwm.duty_u16(duty_u16)

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

while True:
    CLIENT.check_msg()
    CLIENT.check_msg()
    CLIENT.check_msg()
    sleep(1)
