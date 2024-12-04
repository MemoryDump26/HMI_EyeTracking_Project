import colorsys
import os
import time

os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
os.environ["PYNPUT_BACKEND_MOUSE"] = "dummy"

import imgui
from pynput.keyboard import Controller, Key


class VKeyboard:

    def __init__(self):
        self.kb = Controller()

        self.layout3d = [
            ["0_0", "0_1", "0_2", "0_3", "0", "0_4", "0_5", "0_6", "0_7"],
            ["1_0", "1_1", "1_2", "1_3", "1", "1_4", "1_5", "1_6", "1_7"],
            ["2_0", "2_1", "2_2", "2_3", "2", "2_4", "2_5", "2_6", "2_7"],
            ["3_0", "3_1", "3_2", "3_3", "3", "3_4", "3_5", "3_6", "3_7"],
            ["4_0", "4_1", "4_2", "4_3", "4", "4_4", "4_5", "4_6", "4_7"],
            ["5_0", "5_1", "5_2", "5_3", "5", "5_4", "5_5", "5_6", "5_7"],
            ["6_0", "6_1", "6_2", "6_3", "6", "6_4", "6_5", "6_6", "6_7"],
            ["7_0", "7_1", "7_2", "7_3", "7", "7_4", "7_5", "7_6", "7_7"],
            ["8_0", "8_1", "8_2", "8_3", "8", "8_4", "8_5", "8_6", "8_7"],
        ]

    def show_keyboard_v2(self):
        imgui.begin("vkeyboard_v2")
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()
        self.widget_layer_thumbnail(self.layout3d[0])
        imgui.set_cursor_pos((top_left_x + 160, top_left_y))
        self.widget_layer_thumbnail(self.layout3d[1])
        imgui.set_cursor_pos((top_left_x + 320, top_left_y))
        self.widget_layer_thumbnail(self.layout3d[2])
        imgui.set_cursor_pos((top_left_x, top_left_y + 160))
        self.widget_layer_thumbnail(self.layout3d[3])
        imgui.set_cursor_pos((top_left_x + 160, top_left_y + 160))
        self.widget_layer_thumbnail(self.layout3d[4])
        imgui.set_cursor_pos((top_left_x + 320, top_left_y + 160))
        self.widget_layer_thumbnail(self.layout3d[5])
        imgui.set_cursor_pos((top_left_x, top_left_y + 320))
        self.widget_layer_thumbnail(self.layout3d[6])
        imgui.set_cursor_pos((top_left_x + 160, top_left_y + 320))
        self.widget_layer_thumbnail(self.layout3d[7])
        imgui.set_cursor_pos((top_left_x + 320, top_left_y + 320))
        self.widget_layer_thumbnail(self.layout3d[8])
        imgui.end()

    def widget_layer_thumbnail(self, layer):
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()
        imgui.button(layer[4], width=150, height=150)

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
