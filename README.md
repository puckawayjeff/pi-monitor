# **Pi-Monitor: A UniFi-Inspired System Monitor**

A responsive, touchscreen system monitor for headless Raspberry Pi servers, designed to provide at-a-glance status information with an aesthetic inspired by Ubiquiti UniFi hardware.

![A photo of the running monitor in its 1U rack enclosure](https://www.puckaway.org/pi-monitor/monitor-in-rack.jpg)

## **Overview**

This project provides a clean, simple, and extensible monitoring interface for a Raspberry Pi. The inspiration comes from the small touchscreens found on certain UniFi gateways and switches, which offer convenient access to core system metrics.

![A screenshot of a Pi-Monitor screen populated with widgets](https://www.puckaway.org/pi-monitor/screenshot-main.png)

The goal is to create a polished hardware and software experience for headless servers. Housed in a custom 1U rack-mountable enclosure and powered over Ethernet, a Pi running this software becomes a self-contained, single-cable appliance with its own status and control display.

This is ideal for home labs, small businesses, or anyone who wants to add a professional touch to their Raspberry Pi projects.

## **Features**

### **Current Features**

*   Multi-page, swipeable interface.
*   Customizable screen types, including standard info widgets and full-screen "hero" images.
*   Real-time display of key system metrics:
    *   Hostname, OS Version, and Kernel Version
    *   System Uptime
    *   CPU Temperature, Usage, Core Count, and Frequency (Current & Max)
    *   RAM Usage
    *   Disk Space Usage
    *   Network Interface Details (IP, MAC, Live Throughput)
    *   Primary IP Address
*   Automatic screen sleep after a period of inactivity, with wake-on-touch.
*   Screenshot capability via terminal command.

### **Planned Features**

* **3D Printed Enclosure:** Release of STL files for a 1U rack-mountable enclosure that houses the Pi and display.  
* **External Event Triggers:** The display will activate and show persistent alerts for critical events (e.g., a NUT warning that a monitored UPS is on battery).  
* **Enhanced Interactivity:**  
  * Safe Reboot & Shutdown buttons.  
  * User-configurable buttons to execute custom shell scripts (e.g., `docker restart <container>`).  
* **Customization:**  
  * Option to set a hero image as a desaturated wallpaper behind the data.  
* **Early Boot Display:** Investigate the possibility of initializing the display as early as possible in the boot process to show boot logs or status.  
* **Display Sync:** A "far future" goal to allow multiple pi-monitor units in a rack to have their screens activated and navigated simultaneously.

## **Hardware Requirements**

While the software is designed to be adaptable, it has been developed and tested with the following components:

* **Raspberry Pi:** Developed for a Pi 5, tested on a Pi 3\. Should be compatible with any Pi model that has the standard 40-pin GPIO header.  
* **Display:** [Waveshare 2inch Capacitive Touch LCD](https://www.waveshare.com/wiki/2inch_Capacitive_Touch_LCD) (320x240 resolution and usually quite affordable)  
* **Power/Storage (Optional but Recommended):** [Waveshare PoE M.2 HAT+ (B)](https://www.google.com/search?q=https://www.waveshare.com/wiki/PoE_M.2_HAT%2B_\(B\)). This hat is an excellent choice as it provides Power over Ethernet (PoE), an NVMe slot for fast storage, and still passes through all the necessary GPIO pins for the display.

## **Installation**

The installer script downloads the latest release, sets up dependencies, and configures the application to run as a system service.

### **Prerequisites**
Before running the installer, ensure the SPI interface is enabled on your Raspberry Pi:
```bash
sudo raspi-config
```
Navigate to `Interface Options` -> `SPI` and select `<Yes>`.

### **Recommended Method (Safe)**
This method downloads the installer script first, allowing you to inspect it before running it with `sudo`.

```bash
wget https://raw.githubusercontent.com/puckawayjeff/pi-monitor/main/install.sh
chmod +x install.sh
sudo ./install.sh
```

### **One-Liner Method (Convenient)**
This method downloads and runs the installer in a single command.

```bash
wget -O - https://raw.githubusercontent.com/puckawayjeff/pi-monitor/main/install.sh | sudo bash
```

The installer will:
*   Install required system packages.
*   Download the latest release from GitHub to `/opt/pi-monitor`.
*   Create a Python virtual environment.
*   Install Python dependencies.
*   Set up and start a `systemd` service to run the monitor on boot.

After installation, the monitor will start automatically. The main configuration file can be found at `/opt/pi-monitor/config.yaml`.

### **Managing the Service**

-   **Check Status:** `sudo systemctl status pi-monitor.service`
-   **View Logs:** `sudo journalctl -u pi-monitor.service -f`
-   **Restart:** `sudo systemctl restart pi-monitor.service`

### **Uninstallation**
To completely remove the application and service from your system, run the uninstaller script from the project directory:
```bash
chmod +x uninstall.sh
sudo ./uninstall.sh
```

## **Manual Installation (for Developers)**

If you prefer to manage the environment yourself for development purposes:
1.  Clone the repository.
2.  Create and activate a Python virtual environment.
3.  Install dependencies: `pip install -r requirements.txt`
4.  Run the application: `python main.py`

## **Configuration (`config.yaml`)**

The layout, content, colors, and fonts of the monitor are controlled by the `config.yaml` file. This allows you to easily customize what information is displayed without modifying the Python source code.

For a complete guide on all configuration options, widget types, and the full list of available data source functions, please see the detailed **[Configuration Guide](./docs/CONFIGURATION.md)**.

## **Developer Tools**

### **Automatic Screenshot Generation**

The project includes a helpful script, `generate_screenshots.py`, for developers working on custom layouts. This tool automatically generates a full set of screenshots for every screen defined in your `config.yaml`.

It watches for changes to `config.yaml` and regenerates the images whenever the file is saved. 

**Usage:**

1.  Install the `watchdog` library (it is not included in `requirements.txt` as it's a dev-only tool):
    ```bash
    pip install watchdog
    ```
2.  Run the script from the project's root directory:
    ```bash
    python generate_screenshots.py
    ```

Screenshots will be saved in the `screenshots` directory.

## **Contributing**

TBD. Not expecting any interest at this point, honestly. Surprise me!

## **License**

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License - see the LICENSE.md file for details.
