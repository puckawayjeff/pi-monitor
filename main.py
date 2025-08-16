#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import socket
import yaml
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import psutil

# --- Local Driver Imports ---
from hardware.display import st7789, cst816d

# --- Configuration ---
# Screen dimensions for LANDSCAPE orientation
LCD_WIDTH = 320
LCD_HEIGHT = 240

# Inactivity timeout (in seconds)
INACTIVITY_TIMEOUT = 60

# Initialize psutil for CPU usage calculation
psutil.cpu_percent(interval=None)

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
    # By calling with interval=None, it compares to the last time it was called.
    # The initial call at the top of the file primes it.
    try:
        usage = psutil.cpu_percent(interval=None)
        return f"{usage:.1f}%"
    except Exception as e:
        print(f"Error getting CPU usage: {e}")
        return "N/A"


def get_ram_info():
    """Gets RAM usage information."""
    try:
        mem = psutil.virtual_memory()
        usage_percent = f"{mem.percent}%"
        # psutil gives bytes, so we convert to MB for the display
        usage_mb = f"{int(mem.used / (1024**2))}/{int(mem.total / (1024**2))}MB"
        return usage_percent, usage_mb
    except Exception as e:
        print(f"Error getting RAM info: {e}")
        return "N/A", "N/A"


def get_disk_space():
    """Gets disk space information for the root directory."""
    try:
        disk = psutil.disk_usage('/')
        usage_percent = f"{disk.percent}%"
        # psutil gives bytes, so we convert to GB for the display
        usage_gb = f"{disk.used / (1024**3):.1f}G/{disk.total / (1024**3):.1f}G"
        return usage_percent, usage_gb
    except Exception as e:
        print(f"Error getting disk space: {e}")
        return "N/A", "N/A"


def get_ip_address():
    """Gets the primary IP address of the Pi."""
    try:
        interfaces = psutil.net_if_addrs()
        for interface_name, snic_list in interfaces.items():
            # Find a non-loopback interface with an IPv4 address
            if interface_name != 'lo':
                for snic in snic_list:
                    if snic.family == socket.AF_INET:
                        return snic.address
        return "Not Connected"
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "N/A"

def get_current_time():
    """Gets the current time formatted as HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")


class ServerMonitor:
    TITLE_BAR_HEIGHT = 40 # A fixed height for the title bar

    def __init__(self):
        # Initialize display and touch drivers
        self.disp = st7789()
        self.touch = cst816d()
        self.disp.clear()
        
        # Set an initial display orientation. This will be updated by show_image()
        # during the first render to apply the correct landscape rotation.
        self.disp.command(0x36) # MADCTL
        self.disp.data(0x00)    # Default portrait mode

        # Application state
        self.current_screen = 0
        self.is_sleeping = False
        self.last_activity_time = time.time()
        
        # Load layout and fonts from config file
        self.config = self._load_config()
        self.colors = self.config.get('colors', {})
        self.fonts = self._load_fonts(self.config.get('fonts', {}))
        self.screens_config = self.config.get('screens', [])

    def draw_base_ui(self, draw):
        """Draws persistent UI elements for landscape mode."""
        nav_color = self.colors.get('nav_buttons', 'WHITE')

        # Arrows are now smaller and in the title bar
        arrow_y_center = self.TITLE_BAR_HEIGHT // 2
        arrow_half_height = 8 # Approx 20% smaller than original 10
        arrow_width = 16      # Approx 20% smaller than original 20

        # Left Arrow
        left_tip_x = 10
        draw.polygon([
            (left_tip_x, arrow_y_center),
            (left_tip_x + arrow_width, arrow_y_center - arrow_half_height),
            (left_tip_x + arrow_width, arrow_y_center + arrow_half_height)
        ], fill=nav_color)

        # Right Arrow
        right_tip_x = LCD_WIDTH - 10
        draw.polygon([
            (right_tip_x, arrow_y_center),
            (right_tip_x - arrow_width, arrow_y_center - arrow_half_height),
            (right_tip_x - arrow_width, arrow_y_center + arrow_half_height)
        ], fill=nav_color)

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
        font_dir = Path(__file__).parent / "assets" / "fonts"
        for name, details in fonts_config.items():
            font_path = font_dir / details['path']
            try:
                # Pillow expects the path as a string
                fonts[name] = ImageFont.truetype(str(font_path), details['size'])
            except IOError:
                print(f"Font not found at {font_path}. Using default for '{name}'.")
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
        default_color = self.colors.get('widget_default', 'WHITE')
        widget_color = config.get('color', default_color)
        value = self._get_data(config.get('data_source'))
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], config.get('label', ''), font=font, fill=widget_color)
        data_pos = (config['position'][0] + config.get('data_x_offset', 140), config['position'][1])
        draw.text(data_pos, str(value), font=font, fill=widget_color)

    def _draw_widget_line_item_with_sub(self, draw, config):
        """Draws a line item where the data source returns two values (main, sub)."""
        default_color = self.colors.get('widget_default', 'WHITE')
        widget_color = config.get('color', default_color)
        main_val, sub_val = self._get_data(config.get('data_source')) or ("N/A", "N/A")
        font = self.fonts.get(config.get('font', 'medium'))
        sub_font = self.fonts.get(config.get('sub_font', 'small'))
        draw.text(config['position'], config.get('label', ''), font=font, fill=widget_color)
        data_pos = (config['position'][0] + config.get('data_x_offset', 140), config['position'][1])
        draw.text(data_pos, str(main_val), font=font, fill=widget_color)
        sub_pos = (data_pos[0], data_pos[1] + config.get('sub_y_offset', 20))
        draw.text(sub_pos, f"({sub_val})", font=sub_font, fill=config.get('sub_color', 'GRAY'))

    def _draw_widget_dynamic_text(self, draw, config):
        """Draws text using a template string."""
        default_color = self.colors.get('widget_default', 'WHITE')
        widget_color = config.get('color', default_color)
        value = self._get_data(config.get('data_source'))
        text = config.get('template', '{data}').format(data=value)
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], text, font=font, fill=widget_color)

    def _draw_widget_static_text(self, draw, config):
        """Draws text from a data source without a label."""
        default_color = self.colors.get('widget_default', 'WHITE')
        widget_color = config.get('color', default_color)
        value = self._get_data(config.get('data_source'))
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], str(value), font=font, fill=widget_color)

    def _draw_widget_unknown(self, draw, config):
        """Handler for unknown widget types."""
        print(f"Unknown widget type: {config.get('type')}")

    def draw_current_screen(self):
        """Renders the current screen based on the loaded configuration."""
        # Get background colors from config with sane fallbacks
        content_bg = self.colors.get('content_background', 'BLACK')
        title_bg = self.colors.get('title_background', 'BLACK')

        # Create image with the main content background color
        image = Image.new("RGB", (LCD_WIDTH, LCD_HEIGHT), content_bg)
        draw = ImageDraw.Draw(image)

        # Draw the title bar background
        draw.rectangle([(0, 0), (LCD_WIDTH, self.TITLE_BAR_HEIGHT)], fill=title_bg)

        # Now draw the persistent UI elements on top of the new background
        self.draw_base_ui(draw)

        if not self.screens_config:
            draw.text((10, 10), "Error: No screens in config.yaml", font=self.fonts.get('medium'), fill="RED")
            return image

        screen_config = self.screens_config[self.current_screen]

        # Draw Title
        default_title_color = self.colors.get('title_text', 'WHITE')
        title_color = screen_config.get('color', default_title_color)
        # Offset title to make room for the left arrow and center it vertically.
        title_y = (self.TITLE_BAR_HEIGHT - self.fonts.get('large').size) // 2
        draw.text((40, title_y), screen_config.get('title', ''), font=self.fonts.get('large'), fill=title_color)

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
            
            # The touch controller reports coordinates based on the display's native
            # portrait orientation (240x320). We must transform these to match the
            # 320x240 landscape view, which is rotated 90-degrees clockwise.
            # New X = Old Y
            # New Y = Old_Max_X - Old_X
            ui_x = touch_y
            ui_y = LCD_HEIGHT - 1 - touch_x

            # Touch zones for navigation cover the left and right thirds of the screen.
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
