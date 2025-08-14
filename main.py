#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- Local Driver Imports ---
from hardware.display import st7789, cst816d

# --- Configuration ---
# Screen dimensions for LANDSCAPE orientation
LCD_WIDTH = 320
LCD_HEIGHT = 240

# Inactivity timeout (in seconds)
INACTIVITY_TIMEOUT = 60


# --- System Info Functions ---

def get_cpu_temperature():
    """Gets the CPU temperature."""
    try:
        temp_str = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('UTF-8')
        temp = float(temp_str.split('=')[1].split('\'')[0])
        return f"{temp:.1f}°C"
    except (FileNotFoundError, IndexError, ValueError) as e:
        print(f"Error getting CPU temp: {e}")
        return "N/A"

def get_cpu_usage():
    """Gets the CPU usage percentage."""
    try:
        cmd = "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'"
        usage = subprocess.check_output(cmd, shell=True).decode('UTF-8').strip()
        return f"{float(usage):.1f}%"
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error getting CPU usage: {e}")
        return "N/A"

def get_ram_info():
    """Gets RAM usage information."""
    try:
        cmd = "free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2 }'"
        usage_percent = subprocess.check_output(cmd, shell=True).decode('UTF-8').strip()
        cmd = "free -m | awk 'NR==2{printf \"%s/%sMB\", $3,$2}'"
        usage_mb = subprocess.check_output(cmd, shell=True).decode('UTF-8').strip()
        return usage_percent, usage_mb
    except subprocess.CalledProcessError as e:
        print(f"Error getting RAM info: {e}")
        return "N/A", "N/A"

def get_disk_space():
    """Gets disk space information for the root directory."""
    try:
        cmd = "df -h / | awk 'NR==2{printf \"%s\", $5}'"
        usage_percent = subprocess.check_output(cmd, shell=True).decode('UTF-8').strip()
        cmd = "df -h / | awk 'NR==2{printf \"%s/%s\", $3,$2}'"
        usage_gb = subprocess.check_output(cmd, shell=True).decode('UTF-8').strip()
        return usage_percent, usage_gb
    except subprocess.CalledProcessError as e:
        print(f"Error getting disk space: {e}")
        return "N/A", "N/A"
        
def get_ip_address():
    """Gets the primary IP address of the Pi."""
    try:
        cmd = "hostname -I | cut -d' ' -f1"
        ip = subprocess.check_output(cmd, shell=True).decode('UTF-8').strip()
        return ip if ip else "Not Connected"
    except subprocess.CalledProcessError as e:
        print(f"Error getting IP address: {e}")
        return "N/A"

# --- Main Application Class ---

class ServerMonitor:
    def __init__(self):
        # Initialize display and touch drivers
        self.disp = st7789()
        self.touch = cst816d()
        self.disp.clear()

        # Set the display to landscape mode (90-degree clockwise rotation)
        # This is the hardware command for orientation
        self.disp.command(0x36) # MADCTL
        # Correct value for 90-degree rotation without mirroring
        self.disp.data(0x00)    # MY, MV, BGR=0 -> Landscape, no mirroring

        # Application state
        self.current_screen = 0
        self.screens = [self.draw_screen_1, self.draw_screen_2]
        self.is_sleeping = False
        self.last_activity_time = time.time()
        
        # Load fonts
        try:
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except IOError:
            print("Default fonts not found, using fallback.")
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            
    def draw_base_ui(self, draw):
        """Draws persistent UI elements for landscape mode."""
        # Left Arrow (for previous screen)
        draw.polygon([(10, LCD_HEIGHT // 2), (30, LCD_HEIGHT // 2 - 10), (30, LCD_HEIGHT // 2 + 10)], fill="white")
        # Right Arrow (for next screen)
        draw.polygon([(LCD_WIDTH - 10, LCD_HEIGHT // 2), (LCD_WIDTH - 30, LCD_HEIGHT // 2 - 10), (LCD_WIDTH - 30, LCD_HEIGHT // 2 + 10)], fill="white")


    def draw_screen_1(self):
        """Draws the main overview screen (CPU, RAM)."""
        image = Image.new("RGB", (LCD_WIDTH, LCD_HEIGHT), "BLACK")
        draw = ImageDraw.Draw(image)
        self.draw_base_ui(draw)

        # Title
        draw.text((10, 10), "System Overview", font=self.font_large, fill="CYAN")
        
        # CPU Info
        draw.text((40, 50), "CPU Temp:", font=self.font_medium, fill="WHITE")
        draw.text((180, 50), get_cpu_temperature(), font=self.font_medium, fill="YELLOW")
        
        draw.text((40, 80), "CPU Usage:", font=self.font_medium, fill="WHITE")
        draw.text((180, 80), get_cpu_usage(), font=self.font_medium, fill="YELLOW")

        # RAM Info
        ram_percent, ram_mb = get_ram_info()
        draw.text((40, 110), "RAM Usage:", font=self.font_medium, fill="WHITE")
        draw.text((180, 110), ram_percent, font=self.font_medium, fill="YELLOW")
        draw.text((180, 130), f"({ram_mb})", font=self.font_small, fill="GRAY")
        
        # IP and Time
        now = datetime.now().strftime("%H:%M:%S")
        draw.text((10, 210), f"IP: {get_ip_address()}", font=self.font_medium, fill="LIGHTGREEN")
        draw.text((LCD_WIDTH - 90, 210), now, font=self.font_medium, fill="WHITE")

        return image

    def draw_screen_2(self):
        """Draws the storage and network screen."""
        image = Image.new("RGB", (LCD_WIDTH, LCD_HEIGHT), "BLACK")
        draw = ImageDraw.Draw(image)
        self.draw_base_ui(draw)

        # Title
        draw.text((10, 10), "Storage & Network", font=self.font_large, fill="CYAN")

        # Disk Info
        disk_percent, disk_gb = get_disk_space()
        draw.text((40, 60), "Disk Usage:", font=self.font_medium, fill="WHITE")
        draw.text((180, 60), disk_percent, font=self.font_medium, fill="YELLOW")
        draw.text((180, 80), f"({disk_gb})", font=self.font_small, fill="GRAY")

        # IP Address
        draw.text((40, 120), "IP Address:", font=self.font_medium, fill="WHITE")
        draw.text((40, 150), get_ip_address(), font=self.font_medium, fill="LIGHTGREEN")
        
        # Time
        now = datetime.now().strftime("%H:%M:%S")
        draw.text((LCD_WIDTH - 90, 210), now, font=self.font_medium, fill="WHITE")

        return image

    def handle_input(self):
        """Handles touch input for navigation and wake-up."""
        self.touch.read_touch_data()
        point_count, coordinates = self.touch.get_touch_xy()

        if point_count > 0:
            if self.is_sleeping:
                self.wake_up()
                time.sleep(0.1)
                return

            self.last_activity_time = time.time()
            
            touch_x = coordinates[0]['x']
            touch_y = coordinates[0]['y']
            
            # Correct transformation for a 90-degree clockwise hardware rotation (MADCTL = 0xA0)
            ui_x = touch_y
            ui_y = touch_x

            # Greatly expanded touch zones to cover left and right thirds of the screen
            LEFT_ZONE_X_END = LCD_WIDTH // 3
            RIGHT_ZONE_X_START = LCD_WIDTH - (LCD_WIDTH // 3)

            if ui_x < LEFT_ZONE_X_END:
                self.current_screen = (self.current_screen - 1) % len(self.screens)
                print("Touched Left - Previous Screen")
                time.sleep(0.1)

            elif ui_x > RIGHT_ZONE_X_START:
                self.current_screen = (self.current_screen + 1) % len(self.screens)
                print("Touched Right - Next Screen")
                time.sleep(0.1)

    def sleep_display(self):
        """Turn off the backlight to save power."""
        if not self.is_sleeping:
            print("Going to sleep...")
            self.is_sleeping = True
            self.disp.bl_DutyCycle(0)

    def wake_up(self):
        """Turn the backlight on."""
        if self.is_sleeping:
            print("Waking up...")
            self.is_sleeping = False
            self.disp.bl_DutyCycle(100)
            self.last_activity_time = time.time()

    def run(self):
        """Main application loop."""
        print("Starting Server Monitor...")
        try:
            while True:
                self.handle_input()

                if self.is_sleeping:
                    time.sleep(0.1)
                    continue

                if time.time() - self.last_activity_time > INACTIVITY_TIMEOUT:
                    self.sleep_display()
                    continue

                draw_function = self.screens[self.current_screen]
                image = draw_function()
                
                # We no longer rotate in software. The hardware command handles it.
                self.disp.show_image(image)
                time.sleep(0.1) 

        except KeyboardInterrupt:
            print("\nExiting.")
        finally:
            self.disp.bl_DutyCycle(100)
            print("Cleanup complete.")


if __name__ == '__main__':
    monitor = ServerMonitor()
    monitor.run()

