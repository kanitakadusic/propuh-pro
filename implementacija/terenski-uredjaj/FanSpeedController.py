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


class FanSpeedController:

    def __init__(self, target_temp, critical_temp, current_temp, fan_mode = FanMode(FanMode.AUTO)):
        self.target_temp = target_temp
        self.critical_temp = critical_temp
        self.fan_mode = fan_mode
        self.current_speed = 0
        self.current_temp = current_temp
        self.alarm = 0
        self.working_regions = [(-0.1, 0.05), (0.05, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 0.6)] 

    def update_current_speed(self):
        if self.fan_mode.get_mode() != FanMode.AUTO:
            self.current_speed = self.fan_mode.get_mode()
            return
        range = self.critical_temp - self.target_temp
        percentage = (self.current_temp - self.target_temp) / range 
        if percentage < self.working_regions[0][0]:
            self.current_speed = 0 #OFF
        elif percentage > self.working_regions[len(self.working_regions) - 1][1]:
            self.current_speed = 3 #FAST
            if percentage >= 1:
                #TODO turn on the alarm and send with mqtt
                self.alarm = 1
        else:
            i = 0
            j = 1
            new_speed = 0
            for low_border, top_border in self.working_regions:
                if low_border <= percentage < top_border:
                    if i == 1:
                        self.current_speed = new_speed
                    break
                j += 1
                if j == 2:
                    new_speed += 1
                    j = 0
                i = (i + 1) % 2
        print("brzina=",self.current_speed)
                
    def set_mode(self, new_fan_mode):
        self.fan_mode = new_fan_mode
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

    def get_speed_percent(self):
        return self.current_speed / (len(FanMode.VALID_MODES) - 2) # Ovo mozda prepraviti

    def get_speed_u16(self):
        U16 = 2**16 - 1
        return U16 * self.get_speed_percent()
    
    def get_speed_binary(self):
        return bin(2**(2 * self.current_speed) - 1)
    
    def get_alarm(self):
        return self.alarm
    
    def turn_alarm_off(self):
        self.alarm = 0

