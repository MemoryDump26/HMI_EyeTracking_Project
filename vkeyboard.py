import colorsys
import os
import time

os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
os.environ["PYNPUT_BACKEND_MOUSE"] = "dummy"

import imgui
from pynput.keyboard import Controller, Key

keyboard = Controller()

text_str = ""

layout = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";"],
    ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
    [" "],
]

# Selected key color
r, g, b = colorsys.hsv_to_rgb(7.0, 0.6, 0.6)
sel_row = 0
sel_col = 0


def press_key(row: int, col: int):
    imgui.set_keyboard_focus_here(-1)
    keyboard.tap(layout[row][col])


def nav_left():
    global sel_col
    if sel_col > 0:
        sel_col -= 1


def nav_right():
    global sel_row, sel_col
    if sel_col < len(layout[sel_row]) - 1:
        sel_col += 1


def nav_up():
    global sel_row
    if sel_row > 0:
        sel_row -= 1
    pass


def nav_down():
    global sel_row, sel_col
    if sel_row < len(layout) - 1:
        sel_row += 1
    pass


def show_keyboard():
    global text_str, r, g, b, sel_row, sel_col
    imgui.begin("vkeyboard")
    changed, text_str = imgui.input_text(label="input", value=text_str)
    imgui.set_item_default_focus()
    for r_idx, row in enumerate(layout):
        for c_idx, col in enumerate(row):
            selected = False
            if r_idx == sel_row and c_idx == sel_col:
                selected = True
                imgui.push_style_color(imgui.COLOR_BUTTON, r, g, b)
            if imgui.button(col):
                press_key(r_idx, c_idx)
            if selected:
                imgui.pop_style_color(1)
            imgui.same_line()
        imgui.new_line()
    if imgui.button("Left"):
        nav_left()
    if imgui.button("Right"):
        nav_right()
    if imgui.button("Up"):
        nav_up()
    if imgui.button("Down"):
        nav_down()
    if imgui.button("Press current key"):
        press_key(sel_row, sel_col)
    imgui.end()
