#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import spidev
import numpy as np
from gpiozero import DigitalOutputDevice, PWMOutputDevice, Button
import smbus2 as smbus

# ST7789T3 (display) config -- waveshare default pin assignments
RST_PIN  = 27
DC_PIN   = 25
BL_PIN   = 18

# CST816D (touch) config -- waveshare default pin assignments
TP_INT   = 4
TP_RST   = 17

class st7789():
    def __init__(self):
        self.np=np
        self.width  = 240
        self.height = 320

        self.GPIO_RST_PIN = DigitalOutputDevice(RST_PIN,active_high = True,initial_value =True)
        self.GPIO_DC_PIN  = DigitalOutputDevice(DC_PIN,active_high = True,initial_value =True)
        self.GPIO_BL_PIN  = PWMOutputDevice(BL_PIN,frequency = 1000) # PWM frequency （backlight）
        self.bl_DutyCycle(100)

        # Initialize SPI
        self.SPI = spidev.SpiDev(0,0)
        self.SPI.max_speed_hz = 40000000
        self.SPI.mode = 0b00

        self.lcd_init()
        
    # Set PWM duty cycle
    def bl_DutyCycle(self, duty):                   
        self.GPIO_BL_PIN.value = duty / 100

    def digital_write(self, Pin, value):
        if value:
            Pin.on()
        else:
            Pin.off()

    def spi_writebyte(self, data):
        if self.SPI!=None :
            self.SPI.writebytes(data)

    def command(self, cmd):
        self.digital_write(self.GPIO_DC_PIN, False)
        self.spi_writebyte([cmd])

    def data(self, val):
        self.digital_write(self.GPIO_DC_PIN, True)
        self.spi_writebyte([val])

    def reset(self):
        # Reset the display
        self.digital_write(self.GPIO_RST_PIN,True)
        time.sleep(0.01)
        self.digital_write(self.GPIO_RST_PIN,False)
        time.sleep(0.01)
        self.digital_write(self.GPIO_RST_PIN,True)
        time.sleep(0.01)

    def dre_rectangle(self, Xstart, Ystart, Xend, Yend, color):
        color_high = (color >> 8) & 0xFF
        color_low = color & 0xFF

        self.set_windows( Xstart, Ystart, Xend, Yend)
        for a in range (Xstart, Xend+1):
            for b in range (Ystart , Yend + 1):
                self.data(color_high)
                self.data(color_low)

    def lcd_init(self):

        # Hardware reset of the display controller.
        self.reset()

        # Command: SLPOUT (0x11) - Sleep Out
        # This command turns off the sleep mode of the LCD module, enabling the
        # DC/DC converter, internal oscillator, and panel scanning.
        self.command(0x11)
        # A delay of 120ms is required after SLPOUT to allow supply voltages
        # and clock circuits to stabilize before sending new commands.
        time.sleep(0.12)

        # Command: MADCTL (0x36) - Memory Data Access Control
        # Defines the read/write scanning direction of the frame memory.
        self.command(0x36)
        # Data: 0x00
        # Sets the default memory access and display order:
        # - Page Address Order: Top to Bottom
        # - Column Address Order: Left to Right
        # - Page/Column Order: Normal Mode
        # - Line Address Order: LCD Refresh Top to Bottom
        # - RGB/BGR Order: RGB
        # - Display Data Latch Order: LCD Refresh Left to Right
        self.data(0x00)

        # Command: COLMOD (0x3A) - Interface Pixel Format
        # Defines the format of RGB data transferred from the MCU.
        self.command(0x3A)
        # Data: 0x05
        # Sets the pixel format to 16-bit/pixel (RGB 5-6-5), which corresponds
        # to 65K colors.
        self.data(0x05)

        # Command: CSCON (0xF0) - Command Set Control (Manufacturer Specific)
        # This command is used to enable or disable access to extended command sets.
        self.command(0xF0)
        # Data: 0xC3
        # Enables Command Set 2.
        self.data(0xC3)

        # Command: CSCON (0xF0) - Command Set Control (Manufacturer Specific)
        # This command is used to enable or disable access to extended command sets.
        self.command(0xF0)
        # Data: 0x96
        # Enables Command Set 3.
        self.data(0x96)

        # Command: INVCTR (0xB4) - Inversion Control
        # Controls the display's pixel inversion setting to prevent image sticking.
        self.command(0xB4)
        # Data: 0x01
        # Sets the inversion to "dot inversion" in normal mode.
        self.data(0x01)

        # Command: GCTRL (0xB7) - Gate Control
        # Sets the voltage levels for the gate drivers (VGH and VGL).
        self.command(0xB7)
        # Data: 0xC6
        # Configures VGH to 13.65V and VGL to -11.38V.
        self.data(0xC6)

        # Command: LCMCTRL (0xC0) - LCM Control
        # Controls various XOR settings for memory and display behavior.
        self.command(0xC0)
        # Data: 0x80
        # Enables the XOR MY setting, which may reverse the Page Address Order.
        self.data(0x80)
        # Data: 0x45
        # This second parameter is a vendor-specific setting for the LCM.
        self.data(0x45)

        # Command: IDSET (0xC1) - ID Code Setting
        # Sets the ID1, ID2, and ID3 values of the display module.
        self.command(0xC1)
        # Data: 0x13
        # Sets the ID1 parameter to 0x13.
        self.data(0x13)

        # Command: VDVVRHEN (0xC2) - VDV and VRH Command Enable
        # Enables setting VDV and VRH register values via commands.
        self.command(0xC2)
        # Data: 0xA7
        # This is a vendor-specific parameter to configure VDV and VRH.
        self.data(0xA7)

        # Command: VCMOFSET (0xC5) - VCOMS Offset Set
        # Adjusts the VCOMS offset voltage.
        self.command(0xC5)
        # Data: 0x0A
        # Sets the VCOMS OFFSET to -0.05V.
        self.data(0x0A)

        # Command: PWCTRL2 (0xE8) - Power Control 2
        # Controls timing and clock settings for the power circuits.
        self.command(0xE8)
        # These 8 bytes are extended parameters for fine-tuning power control.
        self.data(0x40)
        self.data(0x8A)
        self.data(0x00)
        self.data(0x00)
        self.data(0x29)
        self.data(0x19)
        self.data(0xA5)
        self.data(0x33)

        # Command: PVGAMCTRL (0xE0) - Positive Voltage Gamma Control
        # Sets the positive voltage gamma correction values for grayscale levels.
        self.command(0xE0)
        # The following 14 bytes configure the positive gamma curve.
        self.data(0xD0)
        self.data(0x08)
        self.data(0x0F)
        self.data(0x06)
        self.data(0x06)
        self.data(0x33)
        self.data(0x30)
        self.data(0x33)
        self.data(0x47)
        self.data(0x17)
        self.data(0x13)
        self.data(0x13)
        self.data(0x2B)
        self.data(0x31)

        # Command: NVGAMCTRL (0xE1) - Negative Voltage Gamma Control
        # Sets the negative voltage gamma correction values.
        self.command(0xE1)
        # The following 14 bytes configure the negative gamma curve.
        self.data(0xD0)
        self.data(0x0A)
        self.data(0x11)
        self.data(0x0B)
        self.data(0x09)
        self.data(0x07)
        self.data(0x2F)
        self.data(0x33)
        self.data(0x47)
        self.data(0x38)
        self.data(0x15)
        self.data(0x16)
        self.data(0x2C)
        self.data(0x32)

        # Command: CSCON (0xF0) - Command Set Control (Manufacturer Specific)
        # This command is used to enable or disable access to extended command sets.
        self.command(0xF0)
        # Data: 0x3C
        # Disables Command Set 3.
        self.data(0x3C)

        # Command: CSCON (0xF0) - Command Set Control (Manufacturer Specific)
        # This command is used to enable or disable access to extended command sets.
        self.command(0xF0)
        # Data: 0x69
        # Disables Command Set 2.
        self.data(0x69)

        # Command: INVON (0x21) - Display Inversion On
        # Enables the display inversion mode.
        self.command(0x21)

        # Command: SLPOUT (0x11) - Sleep Out
        # This is a redundant Sleep Out command, likely to ensure the display
        # remains active before the final Display On command.
        self.command(0x11)
        # A 100ms delay for stabilization.
        time.sleep(0.1)

        # Command: DISPON (0x29) - Display On
        # Turns the display on, enabling output from the frame memory.
        self.command(0x29)

    def set_windows(self, Xstart, Ystart, Xend, Yend, horizontal = 0):
        # set the X coordinates
        self.command(0x2A)
        self.data(Xstart>>8)       #Set the horizontal starting point to the high octet
        self.data(Xstart & 0xff)   #Set the horizontal starting point to the low octet
        self.data(Xend>>8)         #Set the horizontal end to the high octet
        self.data((Xend) & 0xff)   #Set the horizontal end to the low octet
        # set the Y coordinates
        self.command(0x2B)
        self.data(Ystart>>8)
        self.data((Ystart & 0xff))
        self.data(Yend>>8)
        self.data((Yend) & 0xff)
        self.command(0x2C)

    def show_image_windows(self, Xstart, Ystart, Xend, Yend, Image):
        # Set buffer to value of PIL image
        # Write display buffer to physical display
        imwidth, imheight = Image.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError('Image must be same dimensions as display \
                ({0}x{1}).' .format(self.width, self.height))
        img = self.np.asarray(Image)
        pix = self.np.zeros((imheight,imwidth , 2), dtype = self.np.uint8)
        # RGB888 >> RGB565
        pix[...,[0]] = self.np.add(self.np.bitwise_and(img[...,[0]],0xF8),self.np.right_shift(img[...,[1]],5))
        pix[...,[1]] = self.np.add(self.np.bitwise_and(self.np.left_shift(img[...,[1]],3),0xE0), self.np.right_shift(img[...,[2]],3))
        pix = pix.flatten().tolist()

        if Xstart > Xend:
            data = Xstart
            Xstart = Xend
            Xend = data

        if Ystart > Yend:
            data = Ystart
            Ystart = Yend
            Yend = data

        if Xend < self.width - 1:
            Xend = Xend + 1

        if Yend < self.width - 1:
            Yend = Yend + 1

        self.set_windows( Xstart, Ystart, Xend, Yend)
        self.digital_write(self.GPIO_DC_PIN,True)

        for i in range (Ystart,Yend):
            Addr = ((Xstart) + (i * 240)) * 2
            self.spi_writebyte(pix[Addr : Addr+((Xend-Xstart+1)*2)])

    def show_image(self, Image):
        """Converts a PIL image to the display's format and writes it to the framebuffer."""
        imwidth, imheight = Image.size

        # This project exclusively uses landscape mode.
        if not (imwidth == self.height and imheight == self.width):
             raise ValueError(f'Image must be {self.height}x{self.width} for landscape mode.')

        # Set the Memory Data Access Control (MADCTL) for 90-degree clockwise rotation
        self.command(0x36)
        self.data(0x38)
        # MADCTL Bits for 0x38 (00111000):
        #   MY (Row Addr Order)  = 0 -> Top to Bottom
        #   MX (Col Addr Order)  = 0 -> Left to Right
        #   MV (Row/Col Exchg)   = 1 -> Invert X/Y
        #   ML (Line Addr Order) = 1 -> Top to Bottom
        #   BGR (Color Order)    = 1 -> BGR
        #   MH (H-Refresh Order) = 0 -> Left to Right
        # This combination correctly rotates the native portrait display to landscape.

        # Convert the 24-bit RGB PIL image to the 16-bit RGB565 format
        img = self.np.asarray(Image)
        pix = self.np.zeros((imheight, imwidth, 2), dtype=self.np.uint8)
        pix[..., 0] = self.np.add(self.np.bitwise_and(img[..., 0], 0xF8), self.np.right_shift(img[..., 1], 5))
        pix[..., 1] = self.np.add(self.np.bitwise_and(self.np.left_shift(img[..., 1], 3), 0xE0), self.np.right_shift(img[..., 2], 3))
        pix = pix.flatten().tolist()

        # Set the drawing window to the full screen
        self.set_windows(0, 0, self.height - 1, self.width - 1)
        self.digital_write(self.GPIO_DC_PIN, True)

        # Write the pixel data to the display in chunks
        for i in range(0, len(pix), 4096):
            self.spi_writebyte(pix[i: i+4096])

    def clear(self):
        # Clear contents of image buffer
        _buffer = [0xff] * (self.width*self.height*2)
        self.set_windows(0, 0, self.width, self.height)
        self.digital_write(self.GPIO_DC_PIN,True)
        for i in range(0, len(_buffer), 4096):
            self.spi_writebyte(_buffer[i: i+4096])

class cst816d():
    def __init__(self):
        # Initialize I2C
        self.I2C = smbus.SMBus(1)
        # Initialize GPIO pins using gpiozero
        self.GPIO_TP_RST = DigitalOutputDevice(TP_RST)
        self.GPIO_TP_INT = Button(TP_INT)
        self.coordinates = [{"x": 0, "y": 0} for _ in range(2)]
        self.point_count = 0
        self.touch_rst()

    # Reset
    def touch_rst(self):
        self.GPIO_TP_RST.off()
        time.sleep(0.001)
        self.GPIO_TP_RST.on()
        time.sleep(0.05)

    def read_bytes(self, reg_addr, length):
        # send register address and read multiple bytes
        data = self.I2C.read_i2c_block_data(0x15, reg_addr, length)
        return data

    def read_touch_data(self):
        TOUCH_NUM_REG = 0x02
        TOUCH_XY_REG = 0x03

        buf = self.read_bytes(TOUCH_NUM_REG, 1)

        if buf and buf[0] != 0:
            self.point_count = buf[0]
            buf = self.read_bytes(TOUCH_XY_REG, 6 * self.point_count)
            for i in range(2):
                self.coordinates[i]["x"] = 0
                self.coordinates[i]["y"] = 0

            if buf:
                for i in range(self.point_count):
                    self.coordinates[i]["x"] = ((buf[(i * 6) + 0] & 0x0f) << 8) + buf[(i * 6) + 1]
                    self.coordinates[i]["y"] = ((buf[(i * 6) + 2] & 0x0f) << 8) + buf[(i * 6) + 3]

    def get_touch_xy(self):
        point = self.point_count
        # reset count to zero
        self.point_count = 0

        if point != 0:
            # return touch status and coordinates
            return point, self.coordinates
        else:
            # return and empty coordinates list
            return 0 , []
