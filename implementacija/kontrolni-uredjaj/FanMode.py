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