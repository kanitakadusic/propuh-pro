class InterfaceMode:
    CONFIGURATION = 0
    OPERATIONAL = 1

    MODE_NAMES = {
            CONFIGURATION: "CONFIGURATION",
            OPERATIONAL: "OPERATION"
        }

    def __init__(self, starting_mode = CONFIGURATION):
        self.VALID_MODES = {InterfaceMode.CONFIGURATION, InterfaceMode.OPERATIONAL}

        if starting_mode not in self.VALID_MODES:
            raise ValueError(f"Invalid starting mode: {starting_mode}. Must be one of {InterfaceMode.MODE_NAMES}.")

        self.current_mode = InterfaceMode.CONFIGURATION
        self.length = 2

    def switch(self):
        self.current_mode = (self.current_mode + 1) % self.length

    def get_current_mode(self):
        return self.current_mode
    
    def get_mode_name(self):
        return InterfaceMode.MODE_NAMES.get(self.current_mode, "UNKNOWN")