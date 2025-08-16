# -*- coding:utf-8 -*-
import subprocess
import psutil
import socket
from datetime import datetime

# Initialize psutil for CPU usage calculation.
# This should be called once at the start.
psutil.cpu_percent(interval=None)


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