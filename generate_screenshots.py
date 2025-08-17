#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Developer tool to automatically generate screenshots for all screens
defined in config.yaml whenever the file is changed.
"""
import yaml
import time
import os
import shutil
from pathlib import Path
from PIL import ImageFont

# --- New Imports for File Watching ---
# Watchdog needs to be installed with PIP. It's not included in requirements.txt because it's only used by this dev tool.
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import project modules
from src.ui import UIDrawer
from src import system_info

# --- Setup Paths ---
root_dir = Path(__file__).parent
config_path = root_dir / "config.yaml"
screenshots_dir = root_dir / "screenshots"
font_dir = root_dir / "assets" / "fonts"

# --- Data Fetcher (from previous script) ---
def get_data(data_source):
    if not data_source: return None
    func_name = data_source if isinstance(data_source, str) else data_source.get('name')
    args = data_source.get('args', []) if isinstance(data_source, dict) else []
    func = getattr(system_info, func_name, None)
    if callable(func):
        try: return func(*args)
        except Exception as e: return "Call Error"
    return "Not Found"

# --- Main Screenshot Generation Logic ---
def generate():
    """
    Loads the config, draws all screens, and saves them as PNGs.
    """
    print("\nChange detected! Regenerating screenshots...")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        print(f"Error loading or parsing config.yaml: {e}")
        return

    fonts = {}
    for name, details in config.get('fonts', {}).items():
        font_path = font_dir / details['path']
        try:
            fonts[name] = ImageFont.truetype(str(font_path), details['size'])
        except IOError:
            fonts[name] = ImageFont.load_default()
            print(f"Font not found at {font_path}. Using default.")

    ui_drawer = UIDrawer(config, fonts, get_data)
    screens_config = config.get('screens', [])

    for i, screen_config in enumerate(screens_config):
        screen_type = screen_config.get('type', 'standard')
        if screen_type == 'hero':
            image_name = Path(screen_config.get('image_path', f'hero_{i}')).stem
            filename = f"screen_{i}_{image_name}.png"
        else:
            title = screen_config.get('title', f'screen_{i}').replace(' ', '_').lower()
            filename = f"screen_{i}_{title}.png"
        
        image = ui_drawer.draw_screen(i)
        filepath = screenshots_dir / filename
        try:
            image.save(filepath)
        except Exception as e:
            print(f"Error saving {filename}: {e}")

    print(f"Successfully generated {len(screens_config)} screenshots.")

# --- Watchdog Event Handler ---
class ConfigChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path == str(config_path.resolve()):
            generate()

# --- Main Execution ---
if __name__ == "__main__":
    generate() # Run once on startup

    event_handler = ConfigChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=str(root_dir), recursive=False)
    
    observer.start()
    print(f"\nWatching {config_path.name} for changes... Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nWatcher stopped.")
    
    observer.join()