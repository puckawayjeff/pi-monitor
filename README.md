# **Pi-Monitor: A UniFi-Inspired System Monitor**

A responsive, touchscreen system monitor for headless Raspberry Pi servers, designed to provide at-a-glance status information with an aesthetic inspired by Ubiquiti UniFi hardware.

![A photo of the running monitor in its 1U rack enclosure](./assets/monitor-in-rack.jpg)

## **Overview**

This project provides a clean, simple, and extensible monitoring interface for a Raspberry Pi. The inspiration comes from the small touchscreens found on certain UniFi gateways and switches, which offer convenient access to core system metrics.

The goal is to create a polished hardware and software experience for headless servers. Housed in a custom 1U rack-mountable enclosure and powered over Ethernet, a Pi running this software becomes a self-contained, single-cable appliance with its own status and control display.

This is ideal for home labs, small businesses, or anyone who wants to add a professional touch to their Raspberry Pi projects.

## **Hardware Requirements**

While the software is designed to be adaptable, it has been developed and tested with the following components:

* **Raspberry Pi:** Developed for a Pi 5, tested on a Pi 3\. Should be compatible with any Pi model that has the standard 40-pin GPIO header.  
* **Display:** [Waveshare 2inch Capacitive Touch LCD](https://www.waveshare.com/wiki/2inch_Capacitive_Touch_LCD) (320x240 resolution and usually quite affordable)  
* **Power/Storage (Optional but Recommended):** [Waveshare PoE M.2 HAT+ (B)](https://www.google.com/search?q=https://www.waveshare.com/wiki/PoE_M.2_HAT%2B_\(B\)). This hat is an excellent choice as it provides Power over Ethernet (PoE), an NVMe slot for fast storage, and still passes through all the necessary GPIO pins for the display.

## **Features**

### **Current Features**

* Multi-page, swipeable interface.  
* Real-time display of key system metrics:  
  * CPU Temperature & Usage  
  * RAM Usage  
  * Disk Space Usage  
  * IP Address  
* Automatic screen sleep after a period of inactivity, with wake-on-touch.

### **Planned Features**

* **3D Printed Enclosure:** Release of STL files for a 1U rack-mountable enclosure that houses the Pi and display.  
* **External Event Triggers:** The display will activate and show persistent alerts for critical events (e.g., a NUT warning that a monitored UPS is on battery).  
* **Enhanced Interactivity:**  
  * Safe Reboot & Shutdown buttons.  
  * User-configurable buttons to execute custom shell scripts (e.g., `docker restart <container>`).  
* **Customization:**  
  * Ability to display a custom logo.  
  * Option to set a logo as a desaturated wallpaper behind the data.  
* **Early Boot Display:** Investigate the possibility of initializing the display as early as possible in the boot process to show boot logs or status.  
* **Display Sync:** A "far future" goal to allow multiple pi-monitor units in a rack to have their screens activated and navigated simultaneously.

## **Installation Guide**

These instructions assume you are starting with a fresh installation of Raspberry Pi OS **Lite (64-bit)**.

### **1\. Initial OS Setup & Updates**

First, ensure your system is up to date.

```bash
sudo apt update && sudo apt upgrade -y
```

### **2\. Install Core Dependencies**

We need `git` to clone the repository and the `python3` packages for creating our isolated Python environment and enabling headers. 

We use the `gpiozero` Python library. This performs best with `lgpio`, which depends on `libgpiod2`.

```bash
sudo apt install -y git python3 python3-dev python3-venv libgpiod2
```

### **3\. Enable Hardware Interfaces**

The display uses SPI and the touch controller uses I2C. Enable them using the Raspberry Pi configuration tool.

```bash
sudo raspi-config
```

Navigate to 3 Interface Options and enable I2C and SPI.

After this, reboot the Pi to ensure all changes take effect.

```bash
sudo reboot
```

### **5\. Clone and Set Up the Project**

Once the Pi has rebooted, log back in and run the following commands.

```bash
# Clone the repository from GitHub  
git clone https://github.com/puckawayjeff/pi-monitor.git

# Navigate into the project directory  
cd pi-monitor

# Create a Python virtual environment  
python3 -m venv venv

# Activate the virtual environment  
source venv/bin/activate

# Install the required Python packages  
pip install -r requirements.txt
```

**Note:** To leave the virtual environment at any time, simply type `deactivate`. Remember to re-run `source venv/bin/activate` before running the app again.

## **Running the Application**

With your virtual environment active, run the main script:

```bash
python3 main.py
```

The monitor should initialize and display the first screen. To stop the application, press `Ctrl+C`.


## **Contributing**

TBD. Not currently open to contributors or even expecting any interest at this point.

## **License**

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License - see the LICENSE.md file for details.
