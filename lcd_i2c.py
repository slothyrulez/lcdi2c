#! -*- coding: utf-8 -*-

from machine import I2C

from hd44780_lcd import HD44780LCD


class LCDI2C(HD44780LCD):
    """
    Inherits from HD44780LCD which defines the LCD Display functionality
    This class controls the LCD via PCF8574T I2C 8 ports I/O multiplexer
    """
    I2C_BAUDRATE = 100000
    I2C_ADDRESS = 39
    I2C_SDA_PIN = "GP24"
    I2C_SCL_PIN = "GP23"
    LCD_ROWS = 2
    LCD_COLS = 16
    LCD_BACKLIGHT_PIN = 3
    LCD_EN_PIN = 2
    LCD_RS_PIN = 0
    LCD_RW_PIN = 1
    LCD_P4 = 4
    LCD_P5 = 5
    LCD_P6 = 6
    LCD_P7 = 7

    def __init__(self):
        super(LCDI2C, self).__init__()
        # I2C related config
        self.baudrate = LCDI2C.I2C_BAUDRATE
        self.addr = LCDI2C.I2C_ADDRESS
        self.sda = LCDI2C.I2C_SDA_PIN
        self.scl = LCDI2C.I2C_SCL_PIN

        self.rows = LCDI2C.LCD_ROWS
        self.cols = LCDI2C.LCD_COLS

        # HD44780 related config
        self.backlight_pin = LCDI2C.LCD_BACKLIGHT_PIN
        self.en = bytearray((1 << LCDI2C.LCD_EN_PIN,))
        self.rs = bytearray((1 << LCDI2C.LCD_RS_PIN,))
        self.rw = bytearray((1 << LCDI2C.LCD_RW_PIN,))
        self._data_pins = bytearray((
            1 << LCDI2C.LCD_P4,
            1 << LCDI2C.LCD_P5,
            1 << LCDI2C.LCD_P6,
            1 << LCDI2C.LCD_P7,
        ))

        # self._displayfunction = bytearray((0x0,))
        # self._displaycontrol = bytearray((0x0,))
        # self._displaymode = bytearray((0x0,))
        # self._polarity = bytearray((HD44780LCD.POSITIVE,))

        self._backlightPinMask = bytearray((0x0,))
        self._backlightStsMask = bytearray((0x0,))

        self._displayfunction[0] = (HD44780LCD.LCD_4BITMODE |
                                    HD44780LCD.LCD_5x8DOTS |
                                    HD44780LCD.LCD_2LINE)

        self.i2c = None

    def configure(self):
        self._init_i2c()
        super(LCDI2C, self)._configure()

    def _init_i2c(self):
        """
        Initializes I2C interface
        """
        self.i2c = I2C(0, I2C.MASTER, pins=(self.sda, self.scl))
        if not len(self.i2c.scan()):
            raise Exception("No I2C device found!")

    def _setBacklightPin(self, value, pol=HD44780LCD.POSITIVE):
        self._backlightPinMask[0] = 1 << value
        self._polarity = pol
        self.setBacklight(HD44780LCD.BACKLIGHT_OFF)

    def setBacklight(self, value):
        if self._backlightPinMask[0] is not 0x0:
            if (self._polarity is HD44780LCD.POSITIVE and value > 0) or (
                    self._polarity is HD44780LCD.NEGATIVE and value == 0):
                self._backlightStsMask[0] = (self._backlightPinMask[0] &
                                             HD44780LCD.LCD_BACKLIGHT)
            else:
                self._backlightStsMask[0] = (self._backlightPinMask[0] &
                                             HD44780LCD.LCD_NOBACKLIGHT)
            self.i2c.writeto(self.addr, self._backlightStsMask[0])

    def send(self, value, mode):
        """ Send to LCD """
        if mode == HD44780LCD.LCD_SEND_FOUR_BITS:
            self._write4bits((value & 0x0F), HD44780LCD.LCD_SEND_COMMAND)
        else:
            self._write4bits((value >> 4), mode)
            self._write4bits((value & 0x0F), mode)

    def _pulse_enable(self, data):
        """ Pulse enable line """
        # En HIGH
        self.i2c.writeto(self.addr, data | self.en[0])
        # En LOW
        self.i2c.writeto(self.addr, data & ~self.en[0])

    def _write4bits(self, value, mode):
        """
        Write 4 bits with the data pins
        """
        # Helper holding data to send on the data pins
        pin_map_value = bytearray((0x00,))

        for pin in range(4):
            if value & 0x1:
                pin_map_value[0] |= self._data_pins[pin]
            value = value >> 1

        if mode is HD44780LCD.LCD_SEND_DATA:
            mode = self.rs[0]

        pin_map_value[0] |= mode | self._backlightStsMask[0]
        self._pulse_enable(pin_map_value[0])
