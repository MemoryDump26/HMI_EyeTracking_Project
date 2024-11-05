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
                    imgui.push_style_color(imgui.COLOR_BUTTON, 0.5, 0.3, 0.3)
                if imgui.button(col):
                    imgui.set_keyboard_focus_here(-1)
                    self.press_key(r_idx, c_idx)
                if selected:
                    imgui.pop_style_color(1)
                imgui.same_line()
            imgui.new_line()
        if imgui.button("Left"):
            self.nav_left()
        if imgui.button("Right"):
            self.nav_right()
        if imgui.button("Up"):
            self.nav_up()
        if imgui.button("Down"):
            self.nav_down()
        if imgui.button("Press current key"):
            # self.press_key(self.sel_row, self.sel_col)
            self.press_current_key()
        imgui.end()
