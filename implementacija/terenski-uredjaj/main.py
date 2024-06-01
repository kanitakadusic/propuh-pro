from machine import Pin, PWM, ADC, Timer
from FanSpeedController import *
import network
import simple
from BusOut  import *

#TODO:  DHT11 - https://www.upesy.com/blogs/tutorials/use-dht11-humidity-temperature-sensor-on-pi-pico-with-micro-python-script 
#       Although it is straightforward, this tool is limited in speed, as it can only measure once per second.

fan_vu_metar_leds = BusOut([4, 5, 6, 7, 8, 9]) # Tacno za picoETF

# WiFi configuration
wifi_ssid = "mirza"
wifi_password = "zakadiju"

# MQTT configuration
mqtt_server = "broker.hivemq.com"
mqtt_topic_target_temp = b"Propuh-Pro/target_temp"
mqtt_topic_critical_temp = b"Propuh-Pro/critical_temp"
mqtt_topic_fan_mode = b"Propuh-Pro/fan_mode"
mqtt_topic_measured_temp = b"Propuh-Pro/measured_temp"

mqtt_client_name = "Propuh-Pro-Teren"

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




overheating_led = Pin(11, Pin.OUT) #TODO: Treba da blinka ako je izmjerena temperatura >= kriticne temperature 

#fan_pwm = PWM(Pin(1)) #TODO: OVO JE PROIZVOLJNO - provjeriti koji Pin se zapravo moze koristiti
#fan_pwm.freq(500)


sensor_pin = ADC(Pin(27))
counter = 0
temp_sum = 0
measured_temp = 0
fan_controller = FanSpeedController(0, 0, FanMode())

CALIBRATION_OFFSET = -1790

def check_temperature(t):
    global sensor_pin, counter, temp_sum, measured_temp, CALIBRATION_OFFSET
    
    voltage = ((sensor_pin.read_u16() + CALIBRATION_OFFSET) / 65535) * 3.3
    print("voltage:",voltage)
    temp_sum += round(voltage * 100,1)
    #print("temp=",temp)
    counter += 1
    if counter == 10:
        measured_temp = temp_sum / 10
        counter = 0
        print("temperature=", measured_temp)

        publish = str(measured_temp)
        buf = '{{"Measured temp":{}}}'.format(publish)
        client.publish(mqtt_topic_measured_temp, publish)
        temp_sum = 0

tim = Timer(period = 500, mode = Timer.PERIODIC, callback = check_temperature)

def update_vu_meter(duty_u16): #TODO: Implementirati
    pass 

def set_fan_speed(duty_u16):
    pass
    #fan_pwm.duty_u16(duty_u16)

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
    if topic == mqtt_topic_fan_mode:
        message_arrived_fan_mode(topic, msg)
    elif topic == mqtt_topic_critical_temp:
        message_arrived_critical_temp(topic, msg)
    elif topic == mqtt_topic_target_temp:
        message_arrived_target_temp(topic, msg)

# Connect to MQTT broker
client = simple.MQTTClient(client_id=mqtt_client_name, server=mqtt_server, port=1883)
client.connect()

# Subscribe to topics
client.set_callback(custom_dispatcher)
client.subscribe(mqtt_topic_fan_mode)
client.subscribe(mqtt_topic_critical_temp)
client.subscribe(mqtt_topic_target_temp)


while True:
    pass