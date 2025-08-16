# -*- coding:utf-8 -*-
from PIL import Image, ImageDraw
from src import constants


class UIDrawer:
    def __init__(self, config, fonts, get_data_func):
        """
        Initializes the UIDrawer.
        Args:
            config (dict): The main application configuration dictionary.
            fonts (dict): A dictionary of loaded PIL.ImageFont objects.
            get_data_func (function): The function to call to retrieve data (e.g., monitor._get_data).
        """
        self.colors = config.get('colors', {})
        self.screens_config = config.get('screens', [])
        self.fonts = fonts
        self.get_data = get_data_func

    def _draw_widget_line_item(self, draw, config):
        """Draws a 'label: value' widget."""
        default_color = self.colors.get('widget_default', 'WHITE')
        widget_color = config.get('color', default_color)
        value = self.get_data(config.get('data_source'))
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], config.get('label', ''), font=font, fill=widget_color)
        data_pos = (config['position'][0] + config.get('data_x_offset', 140), config['position'][1])
        draw.text(data_pos, str(value), font=font, fill=widget_color)

    def _draw_widget_line_item_with_sub(self, draw, config):
        """Draws a line item where the data source returns two values (main, sub)."""
        default_color = self.colors.get('widget_default', 'WHITE')
        widget_color = config.get('color', default_color)
        main_val, sub_val = self.get_data(config.get('data_source')) or ("N/A", "N/A")
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
        value = self.get_data(config.get('data_source'))
        text = config.get('template', '{data}').format(data=value)
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], text, font=font, fill=widget_color)

    def _draw_widget_static_text(self, draw, config):
        """Draws text from a data source without a label."""
        default_color = self.colors.get('widget_default', 'WHITE')
        widget_color = config.get('color', default_color)
        value = self.get_data(config.get('data_source'))
        font = self.fonts.get(config.get('font', 'medium'))
        draw.text(config['position'], str(value), font=font, fill=widget_color)

    def _draw_widget_unknown(self, draw, config):
        """Handler for unknown widget types."""
        print(f"Unknown widget type: {config.get('type')}")

    def _draw_base_ui(self, draw):
        """Draws persistent UI elements for landscape mode."""
        nav_color = self.colors.get('nav_buttons', 'WHITE')
        arrow_y_center = constants.TITLE_BAR_HEIGHT // 2
        arrow_half_height = 8
        arrow_width = 16
        left_tip_x = 10
        draw.polygon([(left_tip_x, arrow_y_center), (left_tip_x + arrow_width, arrow_y_center - arrow_half_height), (left_tip_x + arrow_width, arrow_y_center + arrow_half_height)], fill=nav_color)
        right_tip_x = constants.LCD_WIDTH - 10
        draw.polygon([(right_tip_x, arrow_y_center), (right_tip_x - arrow_width, arrow_y_center - arrow_half_height), (right_tip_x - arrow_width, arrow_y_center + arrow_half_height)], fill=nav_color)

    def draw_screen(self, current_screen_index):
        """Renders a full screen based on the loaded configuration and returns a PIL Image."""
        content_bg = self.colors.get('content_background', 'BLACK')
        title_bg = self.colors.get('title_background', 'BLACK')
        image = Image.new("RGB", (constants.LCD_WIDTH, constants.LCD_HEIGHT), content_bg)
        draw = ImageDraw.Draw(image)
        draw.rectangle([(0, 0), (constants.LCD_WIDTH, constants.TITLE_BAR_HEIGHT)], fill=title_bg)
        self._draw_base_ui(draw)

        if not self.screens_config:
            draw.text((10, 10), "Error: No screens in config.yaml", font=self.fonts.get('medium'), fill="RED")
            return image

        screen_config = self.screens_config[current_screen_index]
        default_title_color = self.colors.get('title_text', 'WHITE')
        title_color = screen_config.get('color', default_title_color)
        title_y = (constants.TITLE_BAR_HEIGHT - self.fonts.get('large').size) // 2
        draw.text((40, title_y), screen_config.get('title', ''), font=self.fonts.get('large'), fill=title_color)

        for widget_config in screen_config.get('widgets', []):
            widget_type = widget_config.get('type', 'unknown')
            draw_func_name = f"_draw_widget_{widget_type}"
            draw_func = getattr(self, draw_func_name, self._draw_widget_unknown)
            draw_func(draw, widget_config)

        return image
