#! -*- coding: utf-8 -*-

import time


class HD44780LCD:
    """
    Basic implementation of Arduino's LiquidCrystal lib
    Defines functionality for a HD44780 LCD display
    """
    # LCD Commands
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80

    # Flags for display entry mode
    LCD_ENTRYRIGHT = 0x00
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00

    # Flags for display on/off and cursor control
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00

    # Flags for display/cursor shift
    LCD_DISPLAYMOVE = 0x08
    LCD_CURSORMOVE = 0x00
    LCD_MOVERIGHT = 0x04
    LCD_MOVELEFT = 0x00

    # Flags for function set
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00

    # This constant defines the time it takes for the home and clear
    # commands in the LCD - Time in microseconds
    HOME_CLEAR_EXEC = 2000
    BACKLIGHT_ON = 255
    BACKLIGHT_OFF = 0
    POSITIVE = 0
    NEGATIVE = 1

    LCD_BACKLIGHT = 0xFF
    LCD_NOBACKLIGHT = 0x00

    # LCD SEND MODES
    # Define COMMAND and DATA LCD Rs
    LCD_SEND_COMMAND = 0
    LCD_SEND_DATA = 1
    # Send only 4 bits
    LCD_SEND_FOUR_BITS = 2

    def __init__(self):
        # When the display powers up, it is configured as follows:
        # 0. LCD starts in 8 bit mode
        # 1. Display clear
        # 2. Function set:
        #    DL = 1; 8-bit interface data
        #    N = 0; 1-line display
        #    F = 0; 5x8 dot character font
        # 3. Display on/off control:
        #    D = 0; Display off
        #    C = 0; Cursor off
        #    B = 0; Blinking off
        # 4. Entry mode set:
        #    I/D = 1; Increment by 1
        #    S = 0; No shift

        self._displayfunction = bytearray((0x0,))
        self._displaycontrol = bytearray((0x0,))
        self._displaymode = bytearray((0x0,))
        self._polarity = bytearray((HD44780LCD.POSITIVE,))

    def _configure(self):
        """
        Configure LCD with common values
        """
        if not self.i2c:
            self._init_i2c()

        # Common procedure to set 4 bit interface
        self.send(0x03, HD44780LCD.LCD_SEND_FOUR_BITS)
        time.sleep_ms(5)
        # wait min 4.1ms

        self.send(0x03, HD44780LCD.LCD_SEND_FOUR_BITS)
        time.sleep_us(400)
        # wait min 100us

        self.send(0x03, HD44780LCD.LCD_SEND_FOUR_BITS)
        time.sleep_us(400)
        # wait min 100us

        # Finally, set to 4-bit interface
        self.send(0x02, HD44780LCD.LCD_SEND_FOUR_BITS)
        time.sleep_us(400)
        # wait min 100us

        # Set num lines, font size, etc.
        self.command(HD44780LCD.LCD_FUNCTIONSET | self._displayfunction[0])
        time.sleep_us(100)

        # Turn the display on with no cursor or blinking default
        self._displaycontrol[0] = (HD44780LCD.LCD_DISPLAYON |
                                   HD44780LCD.LCD_CURSORON |
                                   HD44780LCD.LCD_BLINKON)
        self.display()
        time.sleep_us(100)

        # Clear the LCD
        self.clear()
        time.sleep_us(100)

        # Initialize to default text direction (for romance languages)
        self._displaymode[0] = (HD44780LCD.LCD_ENTRYLEFT |
                                HD44780LCD.LCD_ENTRYSHIFTDECREMENT)
        # set the entry mode
        self.command(HD44780LCD.LCD_ENTRYMODESET | self._displaymode[0])
        time.sleep_us(100)

        self._setBacklightPin(self.backlight_pin)
        self.backlight()

    def send(self, value, mode):
        raise NotImplementedError("This method must be overloaded")

    def _setBacklightPin(self, value, pol):
        raise NotImplementedError("This method must be overloaded")

    def setBacklight(self, value):
        raise NotImplementedError("This method must be overloaded")

    def command(self, value):
        # General LCD commands
        # Generic methods used by the rest of the commands
        self.send(value, HD44780LCD.LCD_SEND_COMMAND)

    def write(self, value):
        self.send(value, HD44780LCD.LCD_SEND_DATA)

    def clear(self):
        # Clear display, set cursor position to zero
        self.command(HD44780LCD.LCD_CLEARDISPLAY)
        # this command is time consuming
        time.sleep_ms(HD44780LCD.HOME_CLEAR_EXEC)

    def home(self):
        # Set cursor position to zero
        self.command(HD44780LCD.LCD_RETURNHOME)
        # this command is time consuming
        time.sleep_ms(HD44780LCD.HOME_CLEAR_EXEC)

    def display(self):
        self._displaycontrol[0] |= HD44780LCD.LCD_DISPLAYON
        self.command(HD44780LCD.LCD_DISPLAYCONTROL | self._displaycontrol[0])

    def noDisplay(self):
        self._displaycontrol[0] &= ~HD44780LCD.LCD_DISPLAYON
        self.command(HD44780LCD.LCD_DISPLAYCONTROL | self._displaycontrol[0])

    def backlight(self):
        # Switch on the backlight
        self.setBacklight(255)

    def noBacklight(self):
        # Switch off the backlight
        self.setBacklight(0)

    def setCursor(self, row=0, col=0):
        row_offset = bytearray((
            0x00, 0x40, 0x14, 0x54,
        ))
        if row >= self.rows:
            row = self.rows - 1
        self.command(HD44780LCD.LCD_SETDDRAMADDR | (col + row_offset[row]))

    def cursor(self):
        self._displaycontrol[0] |= HD44780LCD.LCD_CURSORON
        self.command(HD44780LCD.LCD_DISPLAYCONTROL | self._displaycontrol[0])

    def noCursor(self):
        self._displaycontrol[0] &= ~HD44780LCD.LCD_CURSORON
        self.command(HD44780LCD.LCD_DISPLAYCONTROL | self._displaycontrol[0])

    def blink(self):
        self._displaycontrol[0] |= HD44780LCD.LCD_BLINKON
        self.command(HD44780LCD.LCD_DISPLAYCONTROL | self._displaycontrol[0])

    def noBlink(self):
        self._displaycontrol[0] &= ~HD44780LCD.LCD_BLINKON
        self.command(HD44780LCD.LCD_DISPLAYCONTROL | self._displaycontrol[0])

    def leftToRightText(self):
        """ Text that flows Left to Right """
        self._displaymode[0] |= HD44780LCD.LCD_ENTRYLEFT
        self.command(HD44780LCD.LCD_ENTRYMODESET | self._displaymode[0])

    def rightToLeftText(self):
        """ Text that flows Right to Left """
        self._displaymode[0] &= ~HD44780LCD.LCD_ENTRYLEFT
        self.command(HD44780LCD.LCD_ENTRYMODESET | self._displaymode[0])

    def moveCursorRight(self):
        """ Move cursor one space to the right """
        self.command(HD44780LCD.LCD_CURSORSHIFT | HD44780LCD.LCD_CURSORMOVE |
                     HD44780LCD.LCD_MOVERIGHT)

    def moveCursorLeft(self):
        """ Move cursor one space to the left """
        self.command(HD44780LCD.LCD_CURSORSHIFT | HD44780LCD.LCD_CURSORMOVE |
                     HD44780LCD.LCD_MOVELEFT)

    def autoscroll(self):
        """ This will 'right justify' text from the cursor """
        self._displaymode[0] |= HD44780LCD.LCD_ENTRYSHIFTINCREMENT
        self.command(HD44780LCD.LCD_ENTRYMODESET | self._displaymode[0])

    def noAutoscroll(self):
        self._displaymode[0] &= ~HD44780LCD.LCD_ENTRYSHIFTINCREMENT
        self.command(HD44780LCD.LCD_ENTRYMODESET | self._displaymode[0])

    def on(self):
        """ Switch fully ON the LCD (backlight and LCD) """
        self.display()
        self.backlight()

    def off(self):
        """ Switch fully OFF the LCD (backlight and LCD) """
        self.noBacklight()
        self.noDisplay()

    def createChar(self, location, charmap):
        # Write to CGRAM of new characters
        # Only 8 locations 0-7
        location &= 0x7

        self.command(HD44780LCD.LCD_SETCGRAMADDR | (location << 3))
        time.sleep_us(40)
        for i in range(8):
            self.write(charmap[i])
            time.sleep_us(40)
