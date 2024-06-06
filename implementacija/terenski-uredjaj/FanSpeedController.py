# Moguća stanja ventilatora
class FanMode:
    OFF = 0
    SLOW = 1
    MEDIUM = 2
    FAST = 3
    AUTO = 4

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

    def __init__(self, starting_mode=OFF):

        if starting_mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid starting mode: {starting_mode}. Must be one of {FanMode.MODE_NAMES}."
            )

        self.current_mode : int = starting_mode
        self.length = len(self.VALID_MODES)

    def next(self):
        self.current_mode = (self.current_mode + 1) % self.length

    def previous(self):
        self.current_mode = (self.current_mode - 1) % self.length

    def get_mode(self) -> int:
        return self.current_mode

    def get_mode_name(self):
        return FanMode.MODE_NAMES.get(self.current_mode, "UNKNOWN")

# Upravljanje snagom ventilatora
class FanSpeedController:

    def __init__(self, target_temp, critical_temp, current_temp, fan_mode = FanMode(FanMode.OFF)):
        self.target_temp = target_temp
        self.critical_temp = critical_temp
        self.fan_mode = fan_mode

        # Brzina odgovara stanjima ventilatora
        self.current_speed = 0

        self.current_temp = current_temp
        self.alarm = 0

        # Intervali rada za svako stanje ventilatora
        # < -0.1 -> OFF
        # [-0.1, 0.05) -> OFF/SLOW
        # [0.05, 0.2) -> SLOW
        # [0.2, 0.3) -> SLOW/NORMAL
        # [0.3, 0.5) -> NORMAL
        # [0.5, 0.6) -> NORMAL/FAST
        # >= 0.6 -> FAST
        self.working_regions = [(-0.1, 0.05), (0.05, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 0.6)] 

    # Metoda za ažuriranje trenutne brzine, poziva se nakon svake promjene podataka
    def update_current_speed(self):
        # Trenutna temperatura u odnosu na željenu i kritičnu
        range = self.critical_temp - self.target_temp
        percentage = (self.current_temp - self.target_temp) / range 

        # Ukoliko nije AUTO stanje brzina je jednaka tom stanju
        if self.fan_mode.get_mode() != FanMode.AUTO:
            self.current_speed = self.fan_mode.get_mode()

            # Ukoliko je željena temperatura veća od kritične pali se alarm
            if percentage >= 1:
                self.alarm = 1
            return
        
        if percentage < self.working_regions[0][0]:
            self.current_speed = 0 #OFF
        elif percentage >= self.working_regions[len(self.working_regions) - 1][1]:
            self.current_speed = 3 #FAST
            if percentage >= 1:
                self.alarm = 1
                return
        else:
            i = 0
            j = 1
            new_speed = 0
            for low_border, top_border in self.working_regions:
                if low_border <= percentage < top_border:
                    # Kada je i = 0 trenutna temp. se nalazi u jednom od intervala gdje su moguće dvije brzine ventilatora
                    # Ventilator u tom slučaju ostaje u brzinu u kojoj je trenutno
                    # Ukoliko nije ni u jednoj od te dvije brzine, ventilator prelazi u brzinu koja je bliža trenutnoj
                    if i == 0:
                        if self.current_speed != new_speed and self.current_speed != new_speed + 1:
                            if self.current_speed < new_speed:
                                self.current_speed = new_speed
                            else:
                                self.current_speed = new_speed + 1
                    # Za i = 1 poznata je sljedeća brzina ventilatora 
                    else:
                        self.current_speed = new_speed
                    break
                j += 1
                if j == 2:
                    new_speed += 1
                    j = 0
                i = (i + 1) % 2
        self.turn_alarm_off()

    # Setteri i getteri za atribute 
    def set_mode(self, new_fan_mode):
        self.fan_mode = new_fan_mode

        # U svakoj set metodi se ažurira brzina
        self.update_current_speed()

    def get_mode(self):
        return self.fan_mode
    
    def set_current_temp(self, new_current_temp):
        self.current_temp = new_current_temp
        self.update_current_speed()

    def set_target_temp(self, new_target_temp):
        self.target_temp = new_target_temp
        if self.target_temp <= self.critical_temp - 5:
            self.update_current_speed()

    def set_critical_temp(self, new_critical_temp):
        self.critical_temp = new_critical_temp
        self.update_current_speed()
    
    def get_alarm(self):
        return self.alarm
    
    # Brzina u postotcima
    def get_speed_percent(self):
        # 0 (OFF) -> 0%
        # 1 (SLOW) -> 50%
        # 2 (NORMAL) -> 75%
        # 3 (FAST) -> 100%
        if self.current_speed == 0:
            return 0.0
        return (self.current_speed + 1) / (len(FanMode.VALID_MODES) - 1) # Ovo mozda prepraviti

    # Za postavljanje duty cycle-a PWM izlaza
    def get_speed_u16(self):
        U16 = 2**16 - 1
        return U16 * self.get_speed_percent()
    
    # Za prikaz brzine putem LED
    def get_speed_binary(self):
        # 0 (OFF) -> 0 upaljenih LED
        # 1 (SLOW) -> 2 upaljene LED
        # 2 (NORMAL) -> 4 upaljene LED
        # 3 (FAST) -> 6 upaljenih LED
        return bin(2**(2 * self.current_speed) - 1)
    
    #Gašenje alarma
    def turn_alarm_off(self):
        self.alarm = 0

