from machine import Pin


class BusOut:
    def __init__(self, pin_numbers):
        self.pins = [Pin(pin, Pin.OUT) for pin in pin_numbers]
        self.current_value = 0b0

    def set_value(self, val):
        self.current_value = val
        for i, pin in enumerate(self.pins):
            pin.value((val >> i) & 1)

    def size(self):
        return len(self.pins)

    def get_value(self):
        return self.current_value

    def shift_right(self, shift_amount=1):
        self.current_value /= 2**shift_amount

        if self.current_value < 0:
            self.current_value = 0

        self.set_value(self.current_value)

    def shift_left(self, shift_amount=1):
        self.current_value *= 2**shift_amount

        self.set_value(self.current_value)
