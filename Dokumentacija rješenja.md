# Kontrolni uređaj

## Main.py

Zadatak je napraviti koristični interfejs gdje je moguće postaviti željenu temperaturu i brzinu ventilatora za sistem ventilacije.
Izgled interfejsa prošao je više iteracija. Originalna zamisao je bila interakcija sa dva moda ekrana - operacioni i konfiguracijski mod. Međutim, pokazalo se da je bolje imati ekran za konfiguraciju svake od stakvi.

Osnovne stavke koje korisnik konfiguriše su:
* *Željena temperatura*
* *Kritična temperatura*
* *Brzina ventilatora*

Pored pogleda na ove tri vrijednosti, postoji i pogled na *mjerenu temperaturu*.

### Display

Za display korišten je LCD sa 16 kolona i 2 reda sa I2C modulom za jednostavniju implementaciju uz pomoć biblioteke [RPI-PICO-I2C-LCD](https://github.com/T-622/RPI-PICO-I2C-LCD). Ova biblioteka dosta pojednostavi rad sa pomenutim LCD ekranom ali se pokazala kao nedovoljno responzivna za češće osvježavanje ekrana. Konfiguracija dimenzija i izlaznih pinova displeja je data ispod. 

```python
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

# Display konfiguracija
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

I2C_BUS = I2C(1, sda=Pin(26), scl=Pin(27), freq=400000)
LCD_DISPLAY = I2cLcd(I2C_BUS, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
```
Sve interakcije sa ekranom, kao što je postavljanje ili uklanjanje sadržaja izvode se metodama *LCD_DISPLAY* objekta.

### Pogledi

Za rad sa modovima ekrana, uvedena je klasa InterfaceMode koja definiše dozvoljene modove ili poglede na informacije.

Mogući modovi interfejsa su:
* Current temp - zadnja izmjerena temperatura
* Target temp - željena temperatura
* Critical temp - temperatura pri kojoj se pali alarm
* Fan mode - mod ventilatora

Svaki od navedenih modova ima prateći pogled. U prvom redu ekrana ispisan je naziv pogleda dok je u drugom redu ispisana vrijednost.

Za navigaciju između modova i izmjene vrijednosti, koriste se tasteri. Ispis obrađuje funkcija *print_configuration()* koja se poziva nakon svakog klika na taster.

### Tasteri

Tasteri dostupni korisniku su:
* NEXT_MODE_BUTTON - GPIO16
* PREVIOUS_MODE_BUTTON - GPIO19
* INCREASE_BUTTON - GPIO17
* DECREASE_BUTTON - GPIO18

Ovim tasterima korisnik može mijenjati između četri pogleda te povećati i smanjivati vrijednosti u koracima. Nad svakim od tastera definisan je prekid koji poziva funkciju koja obavlja zadatak tog tastera.

```python
# Postavljanje hardverskih prekida
NEXT_MODE_BUTTON.irq(handler=next_mode, trigger=Pin.IRQ_RISING)
INCREASE_BUTTON.irq(handler=increase_value, trigger=Pin.IRQ_RISING)
DECREASE_BUTTON.irq(handler=decrease_value, trigger=Pin.IRQ_RISING)
PREVIOUS_MODE_BUTTON.irq(handler=previous_mode, trigger=Pin.IRQ_RISING)
```

#### Debouncing
Kako se za konfiguraciju vrijednosti koriste fizički tasteri, pogodno je uvesti funkciju za *debouncing*.
```python
debounce = 0

def debouncing():
    global debounce
    if ticks_diff(ticks_ms(), debounce) < DEBOUNCE_TIME_MS:
        return False
    else:
        debounce = ticks_ms()
        return True
```

Konstanta *DEBOUNCE_TIME_MS* određuje period na koji se blokira ponovni unos sa tastera. Vrijednost od 300ms je odabrana nakon više pokušaja upotrebe i dovoljno je kratka da ne dozvoljava bouncing bez značajno utjecaja na korisničko iskustvo.


#### Korak izmjene
Korak izmjene temperature je 0.5°C. Ova vrijednost za korak je odabrana jer predstavlja dobar kompromis između tačnosti senzora temperature i mogućnosti odabranog ventilatora.

Obzirom da vrijednosti koje se dostave sa terenskog uređaja nisu nužno zaokružene na najbližu polovinu stepena, za to se ovdje koristi funkcija:
```python
def round_to_nearest_half(value) -> float:
    return round(value * 2) / 2
```

([LM35](https://www.ti.com/lit/ds/symlink/lm35.pdf)) - korišteni senzor, ima grešku reda 0.5°C pri 25°C.

### MQTT Komunikacija

Komunikacija sa terenskim uređajem postiže se putem MQTT brokera. Ovo se pokazalo kao veoma jednostavan pristup rješavanju problema komunikacije više uređaja.

#### WiFi konektivnost

Kako je za MQTT potrebna internet konekcija, potrebno je vršiti spajanje na WiFi mrežu. WiFI SSID i lozinka se konfigurišu u kodu na sljedeći način:
```python
import network

# WiFi konfiguracija
WIFI_SSID = "naziv_mreze"
WIFI_PASSWORD = "password1234"

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
```

Obzirom da je sva ostala funkcionalnost uređaja ovisna o internet konekciji, ekran i sve ostale funkcionalnosti su blokirane dok se ne uspostavi WiFi konekcija sa datom mrežom. Na ekranu ostaje ispisan tekst "Connecting..." sve dok se konekcija uspostavlja. Nakon spajanja, u konzoli se ispisuje poruka o uspjehu i lokalna IP adresa.

#### MQTT Broker i teme

MQTT servis postavljen je kako slijedi:
```python
import simple
# MQTT konfiguracija
MQTT_SERVER = "broker.hivemq.com"
MQTT_CLIENT_NAME = "Propuh-Pro-Control"

MQTT_TOPIC_TARGET_TEMP = b"Propuh-Pro/target_temp"
MQTT_TOPIC_CRITICAL_TEMP = b"Propuh-Pro/critical_temp"
MQTT_TOPIC_FAN_MODE = b"Propuh-Pro/fan_mode"
MQTT_TOPIC_MEASURED_TEMP = b"Propuh-Pro/measured_temp"

# Povezivanje na MQTT broker
CLIENT = simple.MQTTClient(client_id=MQTT_CLIENT_NAME, server=MQTT_SERVER, port=1883)
CLIENT.connect()
```

Za svaku od četri stavke, postavljena je tema na MQTT brokeru *broker.himemq.com*.

*target_temp*, *critical_temp* i *measured_temp* predstavljeni su kao realni brojevi dok *fan_mode* uzima jednu od 5 dozvojenih vrijednosti definisanih u FanMode klasi.

Postavljen je klijent MQTT serivsa putem kojeg se šalju i dobavljaju vrijednosti za navedene teme.

#### Slanje podataka

Ovaj uređaj štalje vrijednosti željene i kritične temperature te mod ventilatora.

Nakon bilo koje promjene vrijednosti od strane korisnika, postavlja se timer na 3 sekunde. Nakon 3 sekunde, poziva se funkcija *send_data* koja na broker postavlja navedene vrijednosti.

Ova pauza od 3 sekunde pokazala se kao pogodan pristup za slanje podataka. Obzirom da se ove vrijednosti u praksi ne mijenjaju isuviše često, nije očigledna potreba za periodičnim slanjem.

```python
# Slanje podataka putem MQTT
def send_data(timer):
    publish = str(fan_mode.get_mode())
    CLIENT.publish(MQTT_TOPIC_FAN_MODE, publish)

    publish = str(target_temp)
    CLIENT.publish(MQTT_TOPIC_TARGET_TEMP, publish)

    publish = str(critical_temp)
    CLIENT.publish(MQTT_TOPIC_CRITICAL_TEMP, publish)

    print("Sent!")
```

#### Dobavljanje podataka

Podaci sa MQTT brokera se dobavljaju periodično. Funkcija recieve_data se poziva nakon svake sekunde i dobavlja vrijednost mjerene temperature i mod ventilatora koji je potencijalno postavljen na moblinom uređaju.

Kada se ustanovi da je postavljena nova vrijednost na brokeru *check_msg* metodom MQTT klijenta, poziva se *custom_dispatcher* koji tumači dostavljenu poruku na osnovu teme.

```python
# Filtriranje primljenih poruka
def custom_dispatcher(topic, msg):

    if topic == MQTT_TOPIC_MEASURED_TEMP:
        message_arrived_measured_temp(topic, msg)
    elif topic == MQTT_TOPIC_FAN_MODE:
        message_arrived_fan_mode(topic, msg)

CLIENT.set_callback(custom_dispatcher)

# Pretplata na teme
CLIENT.subscribe(MQTT_TOPIC_MEASURED_TEMP)
CLIENT.subscribe(MQTT_TOPIC_FAN_MODE)

# Provjera pristiglih podataka na MQTT
def recive_data(timer):
    CLIENT.check_msg()
    CLIENT.check_msg()

RECIVE_DATA_TIMER = Timer(period=1000, mode=Timer.PERIODIC, callback=recive_data)
```

### Rad sa temperaturama

Za svaku od tema uvedena je varijabla koja će čuvati odgovarajuću vrijednost na uređaju kako bi se njima manipulisalo u ostatku programa.

```python
interface_mode = InterfaceMode()
fan_mode = FanMode()
current_temp = 0.0
target_temp = 21.0
critical_temp = 35.0
```

Navedene početne vrijednosti za *target_temp* i *critical_temp* su odabrane iz razloga što predstavljaju uobičajen opseg temperatura za stambene prostore, mada nema razloga zašto ne mogu biti u bilo kojem drugom opsegu.

Uvedeno je ograničenje oko minimalne razlike kritične i željene temperature. Najmanja razlika je 5.0°C. Ovo je vrijednost za koju možemo pouzdano tvrditi da neće doći do alarma isključivo zbog greške u mjerenju obzirom da korišteni senzor ([LM35](https://www.ti.com/lit/ds/symlink/lm35.pdf)) ima grešku reda 0.5°C pri 25°C. Ova minimalna razlika se može posebno konfigurisati putem izdvojene konstante.

```python
# Dozvoljena razlika željene i kritične temperature
MINIMUM_TEMP_DIFFERENCE = 5.0
```

#### Alarm

Kada mjerena temperatura dosegne kritičnu temperaturu, dolazi do stanja alarma. Kontrolni uređaj na ekranu ispisuje posebnu treptajuću poruku s ciljem da privuće pažnju i upozori na situaciju. Za to vrijeme, neće se ispisivati standardni pogledi. Poruka o alarmu se može skloniti tasterima za promjenu pogleda.

Za potrebe implementacije alarm pogleda, koristi se varibajla *alarm_now*. Varijabla *alarm* služi kao *flag* da se dogodilo prekoračenje temperature što trenutno nema drugih koristi ali otvara mogućnost za neku vrstu dijagnostike u budućnosti.

```python
# Da li se u toku rada programa pojavio alarm
alarm = False
# Da li je trenutno aktivan alarm
alarm_now = False
```

# Terenski uređaj

# Pomoćne klase

## InterfaceMode

InterfaceMode je pomoćna klasa koja enkapsulira broj i naziv modova ili pogleda na ekran. Ova klasa prati *State pattern* i omogućava promjenu u naredno ili prethodno stanje. Validna stanja su predstavljena kao cijeli brojevi pa se mogu međusobno porediti. Potreba za ovom klasom nastala je jer MicroPython ne poznaje enum klase.

Konstruktor ove klase može da primi jedan parametar - početni pogled, ali je podrazumijevana vrijednost TARGET_TEMP_CONFIG. Primjer instanciranja objekta je dat ispod.

```python
interface_mode = InterfaceMode(InterfaceMode.FAN_CONFIG)
```

Stanja koja ova klasa poznaje su:
```python
VALID_MODES = {
    TARGET_TEMP_CONFIG,
    CRITICAL_TEMP_CONFIG,
    FAN_CONFIG,
    OPERATIONAL,
}
MODE_NAMES = {
    TARGET_TEMP_CONFIG: "TARGET_TEMP_CONFIG",
    CRITICAL_TEMP_CONFIG: "CRITICAL_TEMP_CONFIG",
    FAN_CONFIG: "FAN_CONFIG",
    OPERATIONAL: "OPERATION",
}    
```

Dostupne metode su:
```python
def next(self)          # Naredni mod, ciklično
def previous(self)      # Prethodni mod, ciklično
def get_mode(self)      # Dohvati trenutni mod
def get_mode_name(self) # Dohvati naziv trenutnog moda
```

## FanMode

FanMode je također *State pattern* klasa ali za definisanje modova ventilatora. Tačan intenzitet rada ventilatora nije cilj ove klase. Zapravo, cilj ove klase je da se jasno definišu mogući modovi ventilatora i omogući jasna komunikacija. Kao i za InterfaceMode, stanja se interno čuvaju kao cijeli brojevi.

Konstruktor ove klase može da primi jedan parametar - početni mod, ali je podrazumijevana vrijednost OFF. Primjer instanciranja objekta je dat ispod.

```python
fan_mode = FanMode(FanMode.AUTO)
```

Stanja koja ova klasa poznaje su:
```python
MODE_NAMES = {
    OFF: "OFF",
    SLOW: "SLOW",
    MEDIUM: "MEDIUM",
    FAST: "FAST",
    AUTO: "AUTO",
}

VALID_MODES = {
    OFF,
    SLOW,
    MEDIUM,
    FAST,
    AUTO,
}    
```

Dostupne metode su:
```python
def next(self)          # Naredni mod, ciklično
def previous(self)      # Prethodni mod, ciklično
def get_mode(self)      # Dohvati trenutni mod
def get_mode_name(self) # Dohvati naziv trenutnog moda
```

## FanSpeedController