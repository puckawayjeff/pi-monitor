#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import yaml
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


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

def get_current_time():
    """Gets the current time formatted as HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")


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
        self.is_sleeping = False
        self.last_activity_time = time.time()
        
        # Load layout and fonts from config file
        self.config = self._load_config()
        self.fonts = self._load_fonts(self.config.get('fonts', {}))
        self.screens_config = self.config.get('screens', [])

    def draw_base_ui(self, draw):
        """Draws persistent UI elements for landscape mode."""
        # Left Arrow (for previous screen)
        draw.polygon([(10, LCD_HEIGHT // 2), (30, LCD_HEIGHT // 2 - 10), (30, LCD_HEIGHT // 2 + 10)], fill="white")
        # Right Arrow (for next screen)
        draw.polygon([(LCD_WIDTH - 10, LCD_HEIGHT // 2), (LCD_WIDTH - 30, LCD_HEIGHT // 2 - 10), (LCD_WIDTH - 30, LCD_HEIGHT // 2 + 10)], fill="white")

    def _load_config(self):
        """Loads the YAML configuration file."""
        config_path = Path(__file__).parent / "config.yaml"
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except (IOError, yaml.YAMLError) as e:
            print(f"Error loading or parsing config.yaml: {e}")
            return {} # Return empty config on error

    def _load_fonts(self, fonts_config):
        """Loads ImageFont objects based on the config."""
        fonts = {}
        for name, details in fonts_config.items():
            try:
                fonts[name] = ImageFont.truetype(details['path'], details['size'])
            except IOError:
                print(f"Font not found at {details['path']}. Using default for '{name}'.")
                fonts[name] = ImageFont.load_default()
        return fonts

    def _get_data(self, data_source_name):
        """Safely gets data from a named function."""
        if not data_source_name:
            return None
        func = globals().get(data_source_name)
        if callable(func):
            return func()
        print(f"Warning: Data source function '{data_source_name}' not found.")
        return "Error"

    def _draw_widget_line_item(self, draw, config):
        """Draws a 'label: value' widget."""
        value = self._get_data(config.get('data_source'))
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], config.get('label', ''), font=font, fill=config.get('color', 'WHITE'))
        data_pos = (config['position'][0] + config.get('data_x_offset', 140), config['position'][1])
        draw.text(data_pos, str(value), font=font, fill=config.get('color', 'WHITE'))

    def _draw_widget_line_item_with_sub(self, draw, config):
        """Draws a line item where the data source returns two values (main, sub)."""
        main_val, sub_val = self._get_data(config.get('data_source')) or ("N/A", "N/A")
        font = self.fonts.get(config.get('font', 'medium'))
        sub_font = self.fonts.get(config.get('sub_font', 'small'))
        draw.text(config['position'], config.get('label', ''), font=font, fill=config.get('color', 'WHITE'))
        data_pos = (config['position'][0] + config.get('data_x_offset', 140), config['position'][1])
        draw.text(data_pos, str(main_val), font=font, fill=config.get('color', 'WHITE'))
        sub_pos = (data_pos[0], data_pos[1] + config.get('sub_y_offset', 20))
        draw.text(sub_pos, f"({sub_val})", font=sub_font, fill=config.get('sub_color', 'GRAY'))

    def _draw_widget_dynamic_text(self, draw, config):
        """Draws text using a template string."""
        value = self._get_data(config.get('data_source'))
        text = config.get('template', '{data}').format(data=value)
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], text, font=font, fill=config.get('color', 'WHITE'))

    def _draw_widget_static_text(self, draw, config):
        """Draws text from a data source without a label."""
        value = self._get_data(config.get('data_source'))
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], str(value), font=font, fill=config.get('color', 'WHITE'))

    def _draw_widget_unknown(self, draw, config):
        """Handler for unknown widget types."""
        print(f"Unknown widget type: {config.get('type')}")

    def draw_current_screen(self):
        """Renders the current screen based on the loaded configuration."""
        image = Image.new("RGB", (LCD_WIDTH, LCD_HEIGHT), "BLACK")
        draw = ImageDraw.Draw(image)
        self.draw_base_ui(draw)

        if not self.screens_config:
            draw.text((10, 10), "Error: No screens in config.yaml", font=self.fonts.get('medium'), fill="RED")
            return image

        screen_config = self.screens_config[self.current_screen]

        # Draw Title
        draw.text((10, 10), screen_config.get('title', ''), font=self.fonts.get('large'), fill="CYAN")

        # Draw Widgets
        for widget_config in screen_config.get('widgets', []):
            widget_type = widget_config.get('type', 'unknown')
            draw_func_name = f"_draw_widget_{widget_type}"
            draw_func = getattr(self, draw_func_name, self._draw_widget_unknown)
            draw_func(draw, widget_config)

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
                self.current_screen = (self.current_screen - 1) % len(self.screens_config)
                print("Touched Left - Previous Screen")
                time.sleep(0.1)

            elif ui_x > RIGHT_ZONE_X_START:
                self.current_screen = (self.current_screen + 1) % len(self.screens_config)
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

                image = self.draw_current_screen()
                
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
