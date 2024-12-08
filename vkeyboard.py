import colorsys
import os
import time

os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
os.environ["PYNPUT_BACKEND_MOUSE"] = "dummy"

import imgui
from pynput.keyboard import Controller


class Key:
    def __init__(self, key, display):
        self.display: str = display
        self.key = key


class Layer:
    def __init__(self, layout: list):
        directions: list = ["nw", "n", "ne", "w", "c", "e", "sw", "s", "se"]
        self.layout: dict = dict(zip(directions, layout))

    def go(self, dir: str):
        return self.layout[dir]

    def display_char(self) -> str:
        return layout["c"].display_char()


class VKeyboard:

    def __init__(self):
        self.kb: Controller = Controller()

        # fmt: off
        self.layout = Layer([
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
            Layer([
                Key("0", "0"), Key("1", "1"), Key("2", "2"),
                Key("3", "3"), Key("4", "4"), Key("5", "5"),
                Key("6", "6"), Key("7", "7"), Key("8", "8"),
            ]),
        ])
        # fmt: on

        self.layer_stack: list = []
        self.highlighted_layer: str = "c"

    def navigate(self, dir: str):
        self.layer_stack.append(dir)

    def highlight(self, dir: str):
        self.highlighted_layer = dir

    def home(self):
        self.layer_stack = []

    def get_grid_offset(self, index: int, size: int):
        return (index % 3 * size, index // 3 * size)

    def show_keyboard_v3(self):
        imgui.begin("vkeyboard_v3")
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()

        current_layer: Layer = self.layout
        for dir in self.layer_stack:
            current_layer = current_layer.go(dir)

        for idx, entity in enumerate(current_layer.layout.items()):
            x_offset, y_offset = self.get_grid_offset(idx, 160)
            imgui.set_cursor_pos((top_left_x + x_offset, top_left_y + y_offset))
            if isinstance(entity[1], Layer):
                self.widget_layer_thumbnail(
                    entity[1],
                    (
                        (255, 255, 255, 0.5)
                        if entity[0] == self.highlighted_layer
                        else (255, 255, 255, 0.1)
                    ),
                )
            if isinstance(entity[1], Key):
                self.widget_key(entity[1])
        if imgui.button("w"):
            self.navigate("w")
        if imgui.button("back"):
            self.home()
        imgui.end()

    def widget_key(self, key: Key):
        imgui.button(key.display, width=150, height=150)

    def widget_layer_thumbnail(self, layer: Layer, color: tuple):
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()
        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.button(layer.layout["c"].display, width=150, height=150)
        imgui.pop_style_color()

        imgui.push_style_color(imgui.COLOR_BUTTON, 255, 255, 255, 0.0)
        for idx, dir in enumerate(layer.layout.items()):
            if dir[0] == "c":
                continue
            x_offset, y_offset = self.get_grid_offset(idx, 50)
            imgui.set_cursor_pos((top_left_x + x_offset, top_left_y + y_offset))
            imgui.button(dir[1].display, width=50, height=50)
        imgui.pop_style_color()
