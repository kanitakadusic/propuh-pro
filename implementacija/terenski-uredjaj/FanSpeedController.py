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

        self.current_mode = starting_mode
        self.length = len(self.VALID_MODES)

    def next(self):
        self.current_mode = (self.current_mode + 1) % self.length

    def previous(self):
        self.current_mode = (self.current_mode - 1) % self.length

    def get_mode(self):
        return self.current_mode

    def get_mode_name(self):
        return FanMode.MODE_NAMES.get(self.current_mode, "UNKNOWN")


class FanSpeedController:

    def __init__(self, target_temp, critical_temp, fan_mode=FanMode(FanMode.AUTO)):
        self.target_temp = target_temp
        self.critical_temp = critical_temp
        self.fan_mode = fan_mode
        self.current_speed = 0

    def __update_current_speed(self):

        pass

    def set_mode(self, new_fan_mode):
        self.fan_mode = new_fan_mode
        __update_current_speed()

    def get_mode(self):
        return self.fan_mode

    def set_target_temp(self, new_target_temp):
        update_current_speed()
        self.target_temp = new_target_temp

    def set_critical_temp(self, new_critical_temp):
        update_current_speed()
        self.target_temp = new_critical_temp

    def get_speed_percent(self, current_temp):
        if self.fan_mode == FanMode.AUTO:
            diff = self.critical_temp - self.target_temp
            perc = (current_temp - self.target_temp) / diff
            if perc < 0.33:
                return 0.0
            elif perc >= 0.33 and perc < 0.66:
                return 1/3
            elif perc >= 0.66 and perc < 1:
                return 2/3
            elif    # TODO: Osmisliti proracun za AUTO mod
        # Mozda neka eksponencijalna skala
        # ili eksponencijalno do 50% opsega temperatrue
        # pa logaritamski do 90% opsega

        return self.fan_mode.get_mode() / (len(
            FanMode.VALID_MODES
        ) - 2)  # Ovo mozda prepraviti

    def get_speed_u16(self, current_temp):
        U16 = 2**16 - 1
        return U16 * self.get_speed_percent(current_temp)
