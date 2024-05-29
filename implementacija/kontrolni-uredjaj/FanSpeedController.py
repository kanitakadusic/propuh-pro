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

    def __init__(self, starting_mode=OFF):
        self.VALID_MODES = {
            FanMode.OFF,
            FanMode.SLOW,
            FanMode.MEDIUM,
            FanMode.FAST,
            FanMode.AUTO,
        }

        if starting_mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid starting mode: {starting_mode}. Must be one of {FanMode.MODE_NAMES}."
            )

        self.current_mode = starting_mode
        self.length = 5

    def next(self):
        self.current_mode = (self.current_mode + 1) % self.length

    def get_mode(self):
        return self.current_mode

    def get_mode_name(self):
        return FanMode.MODE_NAMES.get(self.current_mode, "UNKNOWN")


class FanSpeedController:

    def __init__(self, target_temp, fan_mode=FanMode(FanMode.AUTO)):
        self.target_temp = target_temp
        self.fan_mode = fan_mode
        self.current_speed = 0

    def set_mode(self, new_fan_mode):
        self.fan_mode = new_fan_mode

    def get_mode(self):
        return self.fan_mode

    def set_target_temp(self, new_target_temp):
        self.target_temp = new_target_temp

    def get_speed_percent(self, current_temp):
        if self.fan_mode == FanMode.AUTO:
            return 0.0 # TODO: Osmisliti proracun za AUTO mod

        return 1 / 3 * self.fan_mode.get_mode()

    def get_speed_u16(self, current_temp):
        U16 = 2**16 - 1
        return U16 * self.get_speed_percent(current_temp)