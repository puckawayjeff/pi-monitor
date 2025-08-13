# hardware/display.py
# Combined and cleaned-up drivers for the ST7789 display and CST816D touch controller.

import time
import spidev
import numpy as np
from gpiozero import DigitalOutputDevice, PWMOutputDevice, Button
import smbus
import RPi.GPIO

# --- Wrapper Class ---
# This class simplifies interaction by combining the display and touch functionalities.
class Screen:
    """A wrapper class for the ST7789 display and CST816D touch controller."""
    def __init__(self, orientation=90):
        """
        Initializes the display and touch components.
        :param orientation: The rotation of the display. 0, 90, 180, 270 degrees.
                          90 degrees is landscape with USB ports on the right.
        """
        self.display = ST7789()
        self.touch = CST816D()
        self.set_orientation(orientation)

    def set_orientation(self, degrees):
        """
        Sets the display orientation.
        Note: This is a hardware command. Touch coordinates may need to be
              transformed in the application logic based on the orientation.
        """
        # MADCTL (Memory Data Access Control) register values for orientation
        # These values may need tweaking depending on the specific display model.
        # 0x00 = Portrait
        # 0x60 = Portrait (flipped)
        # 0xA0 = Landscape (rotated 90 deg clockwise)
        # 0xC0 = Landscape (flipped)
        if degrees == 0:
            madctl_val = 0x00
        elif degrees == 90:
            madctl_val = 0x60 # Using 0x60 based on common ST7789 setups for landscape
        elif degrees == 180:
            madctl_val = 0xC0
        elif degrees == 270:
            madctl_val = 0xA0
        else:
            madctl_val = 0x00 # Default to portrait

        self.display.command(0x36)
        self.display.data(madctl_val)

    def show_image(self, image):
        """Displays a PIL image on the screen."""
        self.display.show_image(image)

    def get_touch(self):
        """Reads and returns touch data."""
        self.touch.read_touch_data()
        return self.touch.get_touch_xy()

    def set_backlight(self, level):
        """
        Sets the backlight brightness.
        :param level: An integer from 0 (off) to 100 (full brightness).
        """
        self.display.bl_DutyCycle(level)

    def clear(self):
        """Clears the display to black."""
        self.display.clear()


# --- Display Driver (ST7789) ---
# Your original st7789.py code, now as a class within this file.
class ST7789:
    def __init__(self):
        # Pin Definitions
        RST_PIN = 27
        DC_PIN = 25
        BL_PIN = 18
        
        # SPI Configuration
        SPI_Freq = 40000000
        BL_Freq = 1000

        self.width = 240
        self.height = 320
        
        self.GPIO_RST_PIN = DigitalOutputDevice(RST_PIN, active_high=True, initial_value=True)
        self.GPIO_DC_PIN = DigitalOutputDevice(DC_PIN, active_high=True, initial_value=True)
        self.GPIO_BL_PIN = PWMOutputDevice(BL_PIN, frequency=BL_Freq)
        self.bl_DutyCycle(100)
        
        # Initialize SPI
        self.SPI = spidev.SpiDev(0, 0)
        self.SPI.max_speed_hz = SPI_Freq
        self.SPI.mode = 0b00
        
        self.lcd_init()

    def bl_DutyCycle(self, duty):
        self.GPIO_BL_PIN.value = duty / 100.0

    def digital_write(self, pin, value):
        if value:
            pin.on()
        else:
            pin.off()
            
    def spi_writebyte(self, data):
        if self.SPI is not None:
            self.SPI.writebytes(data)
    
    def command(self, cmd):
        self.digital_write(self.GPIO_DC_PIN, False)
        self.spi_writebyte([cmd])
        
    def data(self, val):
        self.digital_write(self.GPIO_DC_PIN, True)
        self.spi_writebyte([val])
        
    def reset(self):
        self.digital_write(self.GPIO_RST_PIN, True)
        time.sleep(0.01)
        self.digital_write(self.GPIO_RST_PIN, False)
        time.sleep(0.01)
        self.digital_write(self.GPIO_RST_PIN, True)
        time.sleep(0.01)
    
    def lcd_init(self):
        self.reset()
        self.command(0x11)
        time.sleep(0.12)

        self.command(0x36) # Memory Data Access Control
        self.data(0x00)    # Default value

        self.command(0x3A)
        self.data(0x05)

        self.command(0xB2) # Porch Setting
        self.data(0x0C)
        self.data(0x0C)
        self.data(0x00)
        self.data(0x33)
        self.data(0x33)

        self.command(0xB7) # Gate Control
        self.data(0x35)

        self.command(0xBB) # VCOM Setting
        self.data(0x19)

        self.command(0xC0) # LCM Control
        self.data(0x2C)

        self.command(0xC2) # VDV and VRH Command Enable
        self.data(0x01)
        self.data(0xFF)

        self.command(0xC3) # VRH Set
        self.data(0x12)

        self.command(0xC4) # VDV Set
        self.data(0x20)

        self.command(0xC6) # Frame Rate Control in Normal Mode
        self.data(0x0F)

        self.command(0xD0) # Power Control 1
        self.data(0xA4)
        self.data(0xA1)

        self.command(0xE0) # Positive Voltage Gamma Control
        self.data(0xD0)
        self.data(0x04)
        self.data(0x0D)
        self.data(0x11)
        self.data(0x13)
        self.data(0x2B)
        self.data(0x3F)
        self.data(0x54)
        self.data(0x4C)
        self.data(0x18)
        self.data(0x0D)
        self.data(0x0B)
        self.data(0x1F)
        self.data(0x23)

        self.command(0xE1) # Negative Voltage Gamma Control
        self.data(0xD0)
        self.data(0x04)
        self.data(0x0C)
        self.data(0x11)
        self.data(0x13)
        self.data(0x2C)
        self.data(0x3F)
        self.data(0x44)
        self.data(0x51)
        self.data(0x2F)
        self.data(0x1F)
        self.data(0x1F)
        self.data(0x20)
        self.data(0x23)

        self.command(0x21) # Display Inversion On
        self.command(0x11) # Sleep Out
        time.sleep(0.12)
        self.command(0x29) # Display On

    def set_windows(self, x_start, y_start, x_end, y_end):
        self.command(0x2A) # Column Address Set
        self.data(x_start >> 8)
        self.data(x_start & 0xFF)
        self.data(x_end >> 8)
        self.data(x_end & 0xFF)

        self.command(0x2B) # Row Address Set
        self.data(y_start >> 8)
        self.data(y_start & 0xFF)
        self.data(y_end >> 8)
        self.data(y_end & 0xFF)
        
        self.command(0x2C) # Memory Write

    def show_image(self, image):
        # The physical display resolution
        disp_width = 240
        disp_height = 240 # For the 1.28-inch round display

        # Set the drawing window to the full screen
        self.set_windows(0, 0, disp_width - 1, disp_height - 1)

        # Convert PIL image to 565 format
        pixel_bytes = self.image_to_data(image)
        
        self.digital_write(self.GPIO_DC_PIN, True)
        # Write data in chunks
        for i in range(0, len(pixel_bytes), 4096):
            self.spi_writebyte(pixel_bytes[i:i+4096])

    def image_to_data(self, image):
        """Converts a PIL Image to a list of bytes in RGB565 format."""
        # Ensure image is in RGB mode
        image_rgb = image.convert("RGB")
        # Convert to numpy array
        img_array = np.array(image_rgb, dtype=np.uint8)
        
        # Apply the RGB888 to RGB565 conversion
        r = (img_array[:, :, 0] & 0xF8).astype(np.uint16)
        g = (img_array[:, :, 1] & 0xFC).astype(np.uint16)
        b = (img_array[:, :, 2] & 0xF8).astype(np.uint16)
        
        rgb565 = (r << 8) | (g << 3) | (b >> 3)
        
        # Return as a list of bytes (big-endian)
        return rgb565.tobytes('C')

    def clear(self):
        """Clear contents of image buffer to black."""
        # Create a black buffer
        black_buffer = [0x00] * (self.width * self.height * 2)
        self.set_windows(0, 0, self.width - 1, self.height - 1)
        self.digital_write(self.GPIO_DC_PIN, True)
        # Write data in chunks
        for i in range(0, len(black_buffer), 4096):
            self.spi_writebyte(black_buffer[i:i+4096])


# --- Touch Driver (CST816D) ---
# Your original cst816d.py code, now as a class within this file.
class CST816D:
    def __init__(self):
        # I2C and GPIO Pin Definitions
        CST816D_ADDRESS = 0x15
        TP_INT_PIN = 4
        TP_RST_PIN = 17
        
        self.i2c = smbus.SMBus(1)
        
        # Using RPi.GPIO for reset pin to match original logic
        self.GPIO = RPi.GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)
        self.GPIO.setup(TP_RST_PIN, self.GPIO.OUT)
        
        # Using gpiozero for interrupt pin
        self.int_pin = Button(TP_INT_PIN, pull_up=True)
        
        self.coordinates = [{"x": 0, "y": 0}]
        self.point_count = 0
        
        self.reset_touch()

    def reset_touch(self):
        self.GPIO.output(17, 0)
        time.sleep(0.01)
        self.GPIO.output(17, 1)
        time.sleep(0.05)
        
    def read_bytes(self, reg_addr, length):
        try:
            return self.i2c.read_i2c_block_data(0x15, reg_addr, length)
        except IOError as e:
            print(f"I2C Error: {e}")
            return None
    
    def read_touch_data(self):
        # Only read data if an interrupt (touch) has occurred
        if self.int_pin.is_pressed:
            buf = self.read_bytes(0x02, 1) # Read number of touch points
            
            if buf and buf[0] > 0:
                self.point_count = buf[0]
                # Read X and Y coordinates for the first touch point
                touch_data = self.read_bytes(0x03, 4)
                if touch_data:
                    x = ((touch_data[0] & 0x0F) << 8) | touch_data[1]
                    y = ((touch_data[2] & 0x0F) << 8) | touch_data[3]
                    # The display is 240x240, cap the values
                    self.coordinates[0]["x"] = min(x, 239)
                    self.coordinates[0]["y"] = min(y, 239)
            else:
                self.point_count = 0
        else:
            self.point_count = 0

    def get_touch_xy(self):
        point = self.point_count
        # Reset point count after reading
        self.point_count = 0
        if point > 0:
            return point, self.coordinates
        else:
            return 0, []
