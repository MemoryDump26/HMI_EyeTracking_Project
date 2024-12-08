import colorsys
import os
import time

os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
os.environ["PYNPUT_BACKEND_MOUSE"] = "dummy"

import imgui
from pynput.keyboard import Controller, Key


class VKeyboard:

    def __init__(self):
        self.kb: Controller = Controller()

        # fmt: off
        self.layout3d: dict = {
            "nw"    : ["0_0", "0_1", "0_2", "0_3", "0", "0_4", "0_5", "0_6", "0_7"],
            "n"     : ["1_0", "1_1", "1_2", "1_3", "1", "1_4", "1_5", "1_6", "1_7"],
            "ne"    : ["2_0", "2_1", "2_2", "2_3", "2", "2_4", "2_5", "2_6", "2_7"],
            "w"     : ["3_0", "3_1", "3_2", "3_3", "3", "3_4", "3_5", "3_6", "3_7"],
            "c"     : ["4_0", "4_1", "4_2", "4_3", "4", "4_4", "4_5", "4_6", "4_7"],
            "e"     : ["5_0", "5_1", "5_2", "5_3", "5", "5_4", "5_5", "5_6", "5_7"],
            "sw"    : ["6_0", "6_1", "6_2", "6_3", "6", "6_4", "6_5", "6_6", "6_7"],
            "s"     : ["7_0", "7_1", "7_2", "7_3", "7", "7_4", "7_5", "7_6", "7_7"],
            "se"    : ["8_0", "8_1", "8_2", "8_3", "8", "8_4", "8_5", "8_6", "8_7"],
        }
        self.layer_color: dict[list] = {
            "nw"    : [0, 0, 0, 0],
            "n"     : [0, 0, 0, 0],
            "ne"    : [0, 0, 0, 0],
            "w"     : [0, 0, 0, 0],
            "c"     : [0, 0, 0, 0],
            "e"     : [0, 0, 0, 0],
            "sw"    : [0, 0, 0, 0],
            "s"     : [0, 0, 0, 0],
            "se"    : [0, 0, 0, 0],
        }
        # fmt: on
        self.layer: str = None
        self.highlighted_layer: str = "c"

    def navigate(self, dir: str):
        if self.layer is None:
            self.layer = dir

    def highlight(self, dir: str):
        self.highlighted_layer = dir

    def home(self):
        self.layer = None

    def get_grid_offset(self, index: int):
        return (index % 3 * 160, index // 3 * 160)

    def show_keyboard_v2(self) -> tuple:
        imgui.begin("vkeyboard_v2")
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()

        if self.layer is None:
            for idx, layer in enumerate(self.layout3d.items()):
                x_offset, y_offset = self.get_grid_offset(idx)
                imgui.set_cursor_pos((top_left_x + x_offset, top_left_y + y_offset))
                self.widget_layer_thumbnail(
                    layer[1],
                    (
                        (255, 255, 255, 0.5)
                        if layer[0] == self.highlighted_layer
                        else (255, 255, 255, 0.1)
                    ),
                )
        else:
            for idx, key in enumerate(self.layout3d[self.layer]):
                x_offset, y_offset = self.get_grid_offset(idx)
                imgui.set_cursor_pos((top_left_x + x_offset, top_left_y + y_offset))
                self.widget_key(key)

        if imgui.button("w"):
            self.navigate("w")
        if imgui.button("back"):
            self.home()
        imgui.end()

    def widget_key(self, key):
        imgui.button(key, width=150, height=150)

    def widget_layer_thumbnail(self, layer: list, color: tuple):
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()
        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.button(layer[4], width=150, height=150)
        imgui.pop_style_color()

        imgui.push_style_color(imgui.COLOR_BUTTON, 255, 255, 255, 0.0)
        imgui.set_cursor_pos((top_left_x, top_left_y))
        imgui.button(layer[0], width=50, height=50)
        imgui.set_cursor_pos((top_left_x + 50, top_left_y))
        imgui.button(layer[1], width=50, height=50)
        imgui.set_cursor_pos((top_left_x + 100, top_left_y))
        imgui.button(layer[2], width=50, height=50)
        imgui.set_cursor_pos((top_left_x, top_left_y + 50))
        imgui.button(layer[3], width=50, height=50)
        imgui.set_cursor_pos((top_left_x + 100, top_left_y + 50))
        imgui.button(layer[5], width=50, height=50)
        imgui.set_cursor_pos((top_left_x, top_left_y + 100))
        imgui.button(layer[6], width=50, height=50)
        imgui.set_cursor_pos((top_left_x + 50, top_left_y + 100))
        imgui.button(layer[7], width=50, height=50)
        imgui.set_cursor_pos((top_left_x + 100, top_left_y + 100))
        imgui.button(layer[8], width=50, height=50)
        imgui.pop_style_color()
