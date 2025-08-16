# -*- coding:utf-8 -*-
import time
import yaml
import sys
import select
from datetime import datetime
from PIL import ImageFont
from pathlib import Path

# --- Local Driver Imports ---
from hardware.display import st7789, cst816d
# --- App Module Imports ---
from src import system_info
from src.ui import UIDrawer
from src import constants


class ServerMonitor:
    def __init__(self):
        # Initialize display and touch drivers
        self.disp = st7789()
        self.touch = cst816d()
        self.disp.clear()

        # Application state
        self.current_screen = 0
        self.is_sleeping = False
        self.last_activity_time = time.time()

        # Load layout and fonts from config file
        self.config = self._load_config()
        self.inactivity_timeout = self.config.get('screen_timeout', 60)
        self.fonts = self._load_fonts(self.config.get('fonts', {}))
        self.screens_config = self.config.get('screens', [])

        # Create the UI Drawer instance
        self.ui_drawer = UIDrawer(self.config, self.fonts, self._get_data)

    def _load_config(self):
        """Loads the YAML configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except (IOError, yaml.YAMLError) as e:
            print(f"Error loading or parsing config.yaml: {e}")
            return {}  # Return empty config on error

    def _load_fonts(self, fonts_config):
        """Loads ImageFont objects based on the config."""
        fonts = {}
        font_dir = Path(__file__).parent.parent / "assets" / "fonts"
        for name, details in fonts_config.items():
            font_path = font_dir / details['path']
            try:
                # Pillow expects the path as a string
                fonts[name] = ImageFont.truetype(str(font_path), details['size'])
            except IOError:
                print(f"Font not found at {font_path}. Using default for '{name}'.")
                fonts[name] = ImageFont.load_default()
        return fonts

    def _get_data(self, data_source):
        """
        Safely gets data from a named function in the system_info module.
        Supports passing arguments from the config.
        """
        if not data_source:
            return None

        func_name = None
        args = []

        if isinstance(data_source, str):
            func_name = data_source
        elif isinstance(data_source, dict):
            func_name = data_source.get('name')
            args = data_source.get('args', [])

        if not func_name:
            print(f"Warning: Invalid data_source format in config: {data_source}")
            return "Error"

        func = getattr(system_info, func_name, None)
        if callable(func):
            try:
                return func(*args)  # Pass arguments to the function
            except Exception as e:
                print(f"Error calling {func_name} with args {args}: {e}")
                return "Call Error"

        print(f"Warning: Data source function '{func_name}' not found in system_info.py.")
        return "Error"

    def take_screenshot(self):
        """Saves the current screen content to a file."""
        print("Taking screenshot...")
        image = self.ui_drawer.draw_screen(self.current_screen)
        screenshots_dir = Path(__file__).parent.parent / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = screenshots_dir / filename
        try:
            image.save(filepath)
            print(f"Screenshot saved to {filepath}")
        except Exception as e:
            print(f"Error saving screenshot: {e}")

    def _check_for_keyboard_input(self):
        """Checks for and handles keyboard input without blocking the main loop."""
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            command = sys.stdin.readline().strip().lower()
            if command == 's':
                self.take_screenshot()

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
            # "touch_x" is unused because we're only concerned with the horizontal value of the touch
            # touch_x = coordinates[0]['x']
            touch_y = coordinates[0]['y']
            ui_x = touch_y
            # "ui_y" is unused because we're only concerned with the horizontal value of the touch
            # ui_y = constants.LCD_HEIGHT - 1 - touch_x
            LEFT_ZONE_X_END = constants.LCD_WIDTH // 3
            RIGHT_ZONE_X_START = constants.LCD_WIDTH - (constants.LCD_WIDTH // 3)

            if ui_x < LEFT_ZONE_X_END:
                self.current_screen = (self.current_screen - 1) % len(self.screens_config)
                time.sleep(0.1)
            elif ui_x > RIGHT_ZONE_X_START:
                self.current_screen = (self.current_screen + 1) % len(self.screens_config)
                time.sleep(0.1)

    def sleep_display(self):
        """Turn off the backlight to save power."""
        if not self.is_sleeping:
            self.is_sleeping = True
            self.disp.bl_DutyCycle(0)

    def wake_up(self):
        """Turn the backlight on."""
        if self.is_sleeping:
            self.is_sleeping = False
            self.disp.bl_DutyCycle(100)
            self.last_activity_time = time.time()

    def run(self):
        """Main application loop."""
        print("Starting Server Monitor...")
        print("Press 's' and then Enter in this terminal to take a screenshot.")
        try:
            while True:
                self._check_for_keyboard_input()
                self.handle_input()

                if self.is_sleeping:
                    time.sleep(0.1)
                    continue

                if self.inactivity_timeout > 0 and \
                   time.time() - self.last_activity_time > self.inactivity_timeout:
                    self.sleep_display()
                    continue

                image = self.ui_drawer.draw_screen(self.current_screen)
                self.disp.show_image(image)
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nExiting.")
        finally:
            self.disp.bl_DutyCycle(100)
            print("Cleanup complete.")
