class InterfaceMode:
    TARGET_TEMP_CONFIG = 0
    CRITICAL_TEMP_CONFIG = 1
    FAN_CONFIG = 2
    OPERATIONAL = 3

    MODE_NAMES = {
        TARGET_TEMP_CONFIG: "TARGET_TEMP_CONFIG",
        CRITICAL_TEMP_CONFIG: "CRITICAL_TEMP_CONFIG",
        FAN_CONFIG: "FAN_CONFIG",
        OPERATIONAL: "OPERATION",
    }

    VALID_MODES = {
        TARGET_TEMP_CONFIG,
        CRITICAL_TEMP_CONFIG,
        FAN_CONFIG,
        OPERATIONAL,
    }

    def __init__(self, starting_mode=TARGET_TEMP_CONFIG):

        if starting_mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid starting mode: {starting_mode}. Must be one of {InterfaceMode.MODE_NAMES}."
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
        return InterfaceMode.MODE_NAMES.get(self.current_mode, "UNKNOWN")
