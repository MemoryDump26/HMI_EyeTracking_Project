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
        self.sel_row = 0
        self.sel_col = 0
        self.text_str = ""

        self.layout = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "Enter"],
            ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
            [" ", " ", " ", " ", " ", " ", " ", " ", " ", " "],
        ]

        self.layout3d = [
            ["0_0", "0_1", "0_2", "0_3", " 0 ", "0_4", "0_5", "0_6", "0_7"],
            ["1_0", "1_1", "1_2", "1_3", "1", "1_4", "1_5", "1_6", "1_7"],
            ["2_0", "2_1", "2_2", "2_3", "2", "2_4", "2_5", "2_6", "2_7"],
            ["3_0", "3_1", "3_2", "3_3", "3", "3_4", "3_5", "3_6", "3_7"],
            ["4_0", "4_1", "4_2", "4_3", "4", "4_4", "4_5", "4_6", "4_7"],
            ["5_0", "5_1", "5_2", "5_3", "5", "5_4", "5_5", "5_6", "5_7"],
            ["6_0", "6_1", "6_2", "6_3", "6", "6_4", "6_5", "6_6", "6_7"],
            ["7_0", "7_1", "7_2", "7_3", "7", "7_4", "7_5", "7_6", "7_7"],
            ["8_0", "8_1", "8_2", "8_3", "8", "8_4", "8_5", "8_6", "8_7"],
        ]

    def press_current_key(self):
        self.press_key(self.sel_row, self.sel_col)

    def press_key(self, row: int, col: int):
        if self.layout[row][col] == "Enter":
            # lmao
            self.kb.tap(Key.enter)
        else:
            self.kb.tap(self.layout[row][col])

    def nav_left(self):
        if self.sel_col > 0:
            self.sel_col -= 1

    def nav_right(self):
        if self.sel_col < len(self.layout[self.sel_row]) - 1:
            self.sel_col += 1

    def nav_up(self):
        if self.sel_row > 0:
            self.sel_row -= 1
        current_row_length = len(self.layout[self.sel_row]) - 1
        if self.sel_col > current_row_length:
            self.sel_col = current_row_length

    def nav_down(self):
        if self.sel_row < len(self.layout) - 1:
            self.sel_row += 1
        current_row_length = len(self.layout[self.sel_row]) - 1
        if self.sel_col > current_row_length:
            self.sel_col = current_row_length

    def show_keyboard(self):
        imgui.begin("vkeyboard")
        changed, self.text_str = imgui.input_text(label="input", value=self.text_str)
        imgui.set_item_default_focus()
        for r_idx, row in enumerate(self.layout):
            for c_idx, col in enumerate(row):
                selected = False
                if r_idx == self.sel_row and c_idx == self.sel_col:
                    selected = True
                    imgui.push_style_color(imgui.COLOR_BUTTON, 0.6, 0.8, 1.0)
                if imgui.button(col):
                    imgui.set_keyboard_focus_here(-1)
                    self.press_key(r_idx, c_idx)
                if selected:
                    imgui.pop_style_color(1)
                imgui.same_line()
            imgui.new_line()
        if imgui.button("L"):
            self.nav_left()
        imgui.same_line()
        if imgui.button("R"):
            self.nav_right()
        imgui.same_line()
        if imgui.button("U"):
            self.nav_up()
        imgui.same_line()
        if imgui.button("D"):
            self.nav_down()
        imgui.same_line()
        if imgui.button("Press"):
            # self.press_key(self.sel_row, self.sel_col)
            self.press_current_key()
        imgui.end()

    def show_keyboard_v2(self):
        imgui.begin("vkeyboard_v2")
        self.widget_layer_thumbnail(self.layout3d[0])
        self.widget_layer_thumbnail(self.layout3d[1])
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

        # for i, key in enumerate(layer):
        #     imgui.button(key)
        #     if (i + 1) % 3 != 0:
        #         imgui.same_line()
