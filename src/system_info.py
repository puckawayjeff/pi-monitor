# -*- coding:utf-8 -*-
import subprocess
import psutil
import socket
import time
import platform
from datetime import datetime, timedelta

# Initialize psutil for CPU and Network usage calculation.
psutil.cpu_percent(interval=None)
psutil.net_io_counters(pernic=True)

# --- Throughput Caching ---
_network_stats_cache = {}  # Stores {'interface': (timestamp, rx_str, tx_str)}
_THROUGHPUT_CACHE_SECONDS = 2  # How long to consider cached throughput data valid.
_THROUGHPUT_MEASUREMENT_INTERVAL = 1  # Seconds to wait to measure rate.


def _format_speed(speed_bytes_per_sec):
    """Formats speed in B/s to a human-readable string."""
    if speed_bytes_per_sec > 1024 * 1024:
        return f"{speed_bytes_per_sec / (1024*1024):.1f} MB/s"
    elif speed_bytes_per_sec > 1024:
        return f"{speed_bytes_per_sec / 1024:.1f} KB/s"
    else:
        return f"{speed_bytes_per_sec:.0f} B/s"


def _update_and_get_throughput(interface_name):
    """
    Internal function to measure and cache network throughput.
    This avoids multiple 1-second delays in a single screen render.
    """
    now = time.time()
    # If we have recent, valid data in the cache, return it
    if interface_name in _network_stats_cache:
        last_time, rx, tx = _network_stats_cache[interface_name]
        if now - last_time < _THROUGHPUT_CACHE_SECONDS:
            return rx, tx

    # Data is stale or not present, so perform a new measurement.
    try:
        last_io = psutil.net_io_counters(pernic=True)
        if interface_name not in last_io:
            return "N/A", "N/A"

        last_bytes_sent = last_io[interface_name].bytes_sent
        last_bytes_recv = last_io[interface_name].bytes_recv

        time.sleep(_THROUGHPUT_MEASUREMENT_INTERVAL)

        new_io = psutil.net_io_counters(pernic=True)
        if interface_name not in new_io:
            return "N/A", "N/A"

        rx_speed = new_io[interface_name].bytes_recv - last_bytes_recv
        tx_speed = new_io[interface_name].bytes_sent - last_bytes_sent

        rx_str = _format_speed(rx_speed)
        tx_str = _format_speed(tx_speed)

        # Store the new values in the cache
        _network_stats_cache[interface_name] = (now, rx_str, tx_str)
        return rx_str, tx_str

    except Exception as e:
        print(f"Error getting throughput for interface {interface_name}: {e}")
        return "Error", "Error"


def get_system_uptime():
    """Gets the system uptime in a human-readable format."""
    try:
        boot_time_timestamp = psutil.boot_time()
        uptime_seconds = time.time() - boot_time_timestamp
        td = timedelta(seconds=uptime_seconds)
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours:02}:{minutes:02}"
        else:
            return f"{hours:02}:{minutes:02}:{seconds:02}"
    except Exception as e:
        print(f"Error getting system uptime: {e}")
        return "N/A"


# --- GRANULAR NETWORK FUNCTIONS ---

def get_interface_ip(interface_name):
    """Gets the IP address for a specific network interface."""
    try:
        stats = psutil.net_if_stats()
        if interface_name not in stats or not stats[interface_name].isup:
            return "Down"

        addrs = psutil.net_if_addrs()
        if interface_name in addrs:
            for addr in addrs[interface_name]:
                if addr.family == socket.AF_INET:
                    return addr.address
        return "No IP"
    except Exception as e:
        print(f"Error getting IP for {interface_name}: {e}")
        return "Error"


def get_interface_mac(interface_name):
    """Gets the MAC address for a specific network interface."""
    try:
        addrs = psutil.net_if_addrs()
        if interface_name in addrs:
            for addr in addrs[interface_name]:
                if addr.family == psutil.AF_LINK:
                    return addr.address.upper()
        return "No MAC"
    except Exception as e:
        print(f"Error getting MAC for {interface_name}: {e}")
        return "Error"


def get_interface_rx(interface_name):
    """Gets the current download speed for an interface."""
    rx, _ = _update_and_get_throughput(interface_name)
    return rx


def get_interface_tx(interface_name):
    """Gets the current upload speed for an interface."""
    _, tx = _update_and_get_throughput(interface_name)
    return tx

# --- NEW SYSTEM & CPU FUNCTIONS ---


def get_hostname():
    """Gets the system's hostname."""
    try:
        return socket.gethostname()
    except Exception as e:
        print(f"Error getting hostname: {e}")
        return "N/A"


def get_os_info():
    """Gets the OS distribution information from /etc/os-release."""
    try:
        with open('/etc/os-release') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    return line.split('=')[1].strip().strip('"')
        # Fallback if PRETTY_NAME is not found
        return f"{platform.system()} {platform.release()}"
    except FileNotFoundError:
        return f"{platform.system()} {platform.release()}"  # For non-Linux or systems without os-release
    except Exception as e:
        print(f"Error getting OS info: {e}")
        return "N/A"


def get_kernel_info():
    """Gets the kernel version."""
    try:
        return platform.release()
    except Exception as e:
        print(f"Error getting kernel info: {e}")
        return "N/A"


def get_cpu_cores():
    """Gets the number of logical CPU cores."""
    try:
        return psutil.cpu_count(logical=True)
    except Exception as e:
        print(f"Error getting CPU cores: {e}")
        return "N/A"


def get_cpu_frequency():
    """Gets the current CPU frequency."""
    try:
        freq = psutil.cpu_freq()
        if freq:
            # Show in GHz if over 1000 MHz for readability
            if freq.current > 1000:
                return f"{freq.current/1000:.2f} GHz"
            return f"{freq.current:.0f} MHz"
        return "N/A"
    except Exception as e:
        print(f"Error getting CPU frequency: {e}")
        return "N/A"


def get_cpu_max_frequency():
    """Gets the maximum configured CPU frequency."""
    try:
        freq = psutil.cpu_freq()
        if freq:
            # Show in GHz if over 1000 MHz for readability
            if freq.max > 1000:
                return f"{freq.max/1000:.2f} GHz"
            return f"{freq.max:.0f} MHz"
        return "N/A"
    except Exception as e:
        print(f"Error getting max CPU frequency: {e}")
        return "N/A"


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


# --- REFACTORED RAM & DISK FUNCTIONS ---

def get_ram_usage_percent():
    """Gets RAM usage as a percentage string."""
    try:
        mem = psutil.virtual_memory()
        return f"{mem.percent}%"
    except Exception as e:
        print(f"Error getting RAM percentage: {e}")
        return "N/A"


def get_ram_total():
    """Gets total system RAM as a string in MB."""
    try:
        mem = psutil.virtual_memory()
        return f"{int(mem.total / (1024**2))}MB"
    except Exception as e:
        print(f"Error getting total RAM: {e}")
        return "N/A"

def get_ram_usage_summary():
    """Gets RAM usage as a 'used/total' string in MB."""
    try:
        mem = psutil.virtual_memory()
        return f"{int(mem.used / (1024**2))}/{int(mem.total / (1024**2))}MB"
    except Exception as e:
        print(f"Error getting RAM summary: {e}")
        return "N/A"


def get_disk_usage_percent(path='/'):
    """Gets disk usage as a percentage string for a given path."""
    try:
        disk = psutil.disk_usage(path)
        return f"{disk.percent}%"
    except Exception as e:
        print(f"Error getting disk percentage for {path}: {e}")
        return "N/A"


def get_disk_usage_summary(path='/'):
    """Gets disk usage as a 'used/total' string in GB for a given path."""
    try:
        disk = psutil.disk_usage(path)
        return f"{disk.used / (1024**3):.1f}G/{disk.total / (1024**3):.1f}G"
    except Exception as e:
        print(f"Error getting disk summary for {path}: {e}")
        return "N/A"


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
