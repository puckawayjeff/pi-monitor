# **Configuration Guide**

This guide provides a comprehensive overview of all the settings available in the `config.yaml` file. This file allows you to customize the appearance, layout, and data displayed on the monitor without modifying the Python source code.

## **Global Settings**

### `screen_timeout`

Controls the inactivity timer for the display's backlight.

-   **Value**: An integer representing the number of seconds of inactivity before the screen turns off.
-   **Default**: `60` seconds.
-   **Disable**: Set the value to `0` to disable the timeout, keeping the screen on indefinitely.

## **UI Sections**

### `colors`

Defines the color palette for the UI. You can use standard color names (e.g., `"WHITE"`) or hex codes (e.g., `"#c29b4a"`).

-   `title_background`: Background color of the top title bar.
-   `title_text`: Default text color for screen titles.
-   `content_background`: Background color for the main content area.
-   `widget_default`: Default text color for all widgets. This can be overridden by a widget's individual `color` property.
-   `nav_buttons`: Color of the left/right navigation arrows in the title bar.

### `fonts`

Defines the font styles used by the widgets. You can define multiple fonts and refer to them by name (e.g., `large`, `medium`) in your widget configurations.

The `path` property should be the filename of a `.ttf` or `.otf` font file located in the `assets/fonts/` directory.

### `screens`

This is a list of all the pages you can swipe through. Each item in the list is a screen object. There are two types of screens: **standard** and **hero**.

#### Standard Screen
A standard screen has its own `title` and a list of `widgets`.
-   `title`: The text displayed in the top title bar.
-   `widgets`: A list of dictionary objects, where each object defines a widget to be displayed on that screen.

#### Hero Screen
A hero screen displays a single, centered image. It does not have a title bar or navigation arrows. Navigation is handled by tapping the left 40% or right 40% of the screen.
-   `type`: Must be set to `"hero"`.
-   `image_path`: The filename of the image to display. The image file must be placed in the `assets/images/` directory.

---

## **Available Data Sources**

Widgets use the `data_source` property to fetch live system information. For functions that require an argument (like an interface name), the `data_source` becomes a dictionary with `name` and `args`.

| Function Name             | Argument(s)        | Returns                                                                 | Example Output                  |
| ------------------------- | ------------------ | ----------------------------------------------------------------------- | ------------------------------- |
| `get_hostname`            | None               | System's hostname.                                                      | `"pi-server"`                   |
| `get_os_info`             | None               | Pretty name of the OS distribution.                                     | `"Raspberry Pi OS Lite (64-bit)"` |
| `get_kernel_info`         | None               | Kernel version string.                                                  | `"6.1.0-rpi7-rpi-v8"`           |
| `get_system_uptime`       | None               | Human-readable system uptime.                                           | `"3d 04:22"`                    |
| `get_cpu_temperature`     | None               | CPU temperature string.                                                 | `"45.1°C"`                      |
| `get_cpu_usage`           | None               | Current CPU usage percentage.                                           | `"15.7%"`                       |
| `get_cpu_cores`           | None               | Number of logical CPU cores.                                            | `4`                             |
| `get_cpu_frequency`       | None               | Current CPU frequency.                                                  | `"1.80 GHz"`                    |
| `get_cpu_max_frequency`   | None               | Maximum configured CPU frequency.                                       | `"2.40 GHz"`                    |
| `get_ram_usage_percent`   | None               | RAM usage as a percentage.                                              | `"25.4%"`                       |
| `get_ram_usage_summary`   | None               | RAM usage as a `used/total` summary.                                    | `"1001/3944MB"`                 |
| `get_disk_usage_percent`  | `path` (optional)  | Disk usage percentage for a given path (defaults to `/`).               | `"68.2%"`                       |
| `get_disk_usage_summary`  | `path` (optional)  | Disk usage as a `used/total` summary for a given path.                  | `"19.8G/29.1G"`                 |
| `get_ip_address`          | None               | Primary IPv4 address.                                                   | `"192.168.1.10"`                |
| `get_interface_ip`        | `interface_name`   | IP address for a specific interface.                                    | `"100.101.102.103"`             |
| `get_interface_mac`       | `interface_name`   | MAC address for a specific interface.                                   | `"B8:27:EB:XX:XX:XX"`           |
| `get_interface_rx`        | `interface_name`   | Download speed for a specific interface.                                | `"1.2 MB/s"`                    |
| `get_interface_tx`        | `interface_name`   | Upload speed for a specific interface.                                  | `"128.4 KB/s"`                  |
| `get_current_time`        | None               | Current time.                                                           | `"22:10:45"`                    |

---

## **Widget Types**

The `type` property of a widget determines how it is rendered.

### `line_item`

Displays a `label` and a value on the same line.

-   **`position`**: `[x, y]` coordinates for the label's top-left corner.
-   **`label`**: The text to display.
-   **`data_source`**: A function name (string) or a dictionary (`{name: "...", args: [...]}`) that returns a single value.
-   **`data_x_offset`**: Horizontal distance (pixels) from the label's start to the data's start.
-   **`font`** (optional): Font name from the `fonts` section.
-   **`color`** (optional): A fallback color for both the label and the data.
-   **`label_color`** (optional): Specific color for the label text. Overrides `color`.
-   **`data_color`** (optional): Specific color for the data text. Overrides `color`.

### `dynamic_text`

Displays text from a `template` string, where `{data}` is replaced by the value from the `data_source`.

-   **`position`**: `[x, y]` coordinates.
-   **`template`**: A string containing `{data}` as a placeholder.
-   **`data_source`**: A function name or dictionary.
-   **`font`** (optional): Font name.
-   **`color`** (optional): Text color.

### `static_text`

Displays a value directly from a `data_source` without any label or template.

-   **`position`**: `[x, y]` coordinates.
-   **`data_source`**: A function name or dictionary.
-   **`font`** (optional): Font name.
-   **`color`** (optional): Text color.