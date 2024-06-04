from machine import Pin, PWM, ADC, Timer
from time import sleep, ticks_ms, ticks_diff
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

FAN_VU_METER_LEDS = BusOut([4, 5, 6, 7, 8, 9])

OVERHEATING_LED = Pin(11, Pin.OUT)

FAN_PWM = PWM(Pin(22))
FAN_PWM.freq(500)

ALARM_PWM = PWM(Pin(27))
ALARM_PWM.freq(1000)

ALARM_OFF_PIN = Pin(0, Pin.IN)

LM35_SENSOR_PIN = ADC(Pin(28))

temp_sum = 0.0
measured_temp = 0.0
sample_counter = 0
alarm = 0

fan_controller = FanSpeedController(22, 30, 22)
#fan_controller.set_current_temp(32)


DEBOUNCE_TIME_MS = 300
debounce = 0

def debouncing():
    global debounce
    if ticks_diff(ticks_ms(), debounce) < DEBOUNCE_TIME_MS:
        return False
    else:
        debounce = ticks_ms()
        return True
    
def update_system():
    global alarm, fan_controller
    speed = int(fan_controller.get_speed_u16())
    light = int(fan_controller.get_speed_binary())
    if fan_controller.get_alarm() == 1 and alarm == 0:
        turn_alarm_on()
    elif fan_controller.get_alarm() == 0 and alarm == 1:
        turn_alarm_off(ALARM_OFF_PIN)
    set_fan_speed(speed)
    update_vu_meter(light)

def check_temperature(t):
    global sample_counter, temp_sum, measured_temp, fan_controller

    voltage = ((LM35_SENSOR_PIN.read_u16() + LM35_CALIBRATION_OFFSET) / 65535) * 3.3
    temp_sum += round(voltage * 100, 1)
    sample_counter += 1

    if sample_counter == LM35_NUMBER_OF_SAMPLES:
        measured_temp = temp_sum / LM35_NUMBER_OF_SAMPLES
        sample_counter = 0
        temp_sum = 0
        print("Average temperature=", measured_temp)
        fan_controller.set_current_temp(measured_temp)
        publish = str(measured_temp)
        CLIENT.publish(MQTT_TOPIC_MEASURED_TEMP, publish)
        
        update_system()

def toggle_alarm(t):
    global alarm
    if OVERHEATING_LED.value() == 1:
        OVERHEATING_LED.off()
        if alarm == 1:
            ALARM_PWM.duty_u16(45000)
    else:
        OVERHEATING_LED.on()
        if alarm == 1:
            ALARM_PWM.duty_u16(10000)

def turn_alarm_off(pin):
    global fan_controller, alarm

    fan_controller.turn_alarm_off()
    alarm = 0
    ALARM_PWM.duty_u16(0)
    OVERHEATING_LED.off()
    #ALARM_TIMER.deinit()    

def set_fan_speed(duty_u16):
    FAN_PWM.duty_u16(duty_u16)

def update_vu_meter(number):
    FAN_VU_METER_LEDS.set_value(number)

def turn_alarm_on():
    global ALARM_TIMER, alarm
    alarm = 1
    OVERHEATING_LED.on()
    ALARM_PWM.duty_u16(3000)
    ALARM_TIMER = Timer(period = 500, mode = Timer.PERIODIC, callback = toggle_alarm)

def message_arrived_fan_mode(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_mode(FanMode(int(float(msg))))
    
    update_system()


def message_arrived_critical_temp(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_critical_temp(float(msg))
    
    update_system()


def message_arrived_target_temp(topic, msg):
    global fan_controller
    print("Message arrived on topic:", topic)
    print("Payload:", msg)
    fan_controller.set_target_temp(float(msg))
    
    update_system()


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

def recieve_data(t):
    CLIENT.check_msg()
    CLIENT.check_msg()
    CLIENT.check_msg()

def nop(t):
    pass


CHECK_TEMP_TIMER = Timer(period=500, mode=Timer.PERIODIC, callback=check_temperature)
RECIEVE_DATA_TIMER = Timer(period=1000, mode=Timer.PERIODIC, callback=recieve_data)
ALARM_OFF_PIN.irq(handler=turn_alarm_off, trigger=Pin.IRQ_RISING)
ALARM_TIMER = Timer(period = 100, mode = Timer.ONE_SHOT, callback = nop)

while True:
    pass
