import colorsys
import os
import time

os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
os.environ["PYNPUT_BACKEND_MOUSE"] = "dummy"

from threading import Timer

import imgui
from pynput.keyboard import Controller
from statemachine import State, StateMachine


class Key:
    def __init__(self, key="", label: str = "", one_shot_mod: bool = False):
        self.label: str = label
        self.key = key
        self.one_shot_mod = one_shot_mod


class Layer:
    def __init__(self, layout: list):
        directions: list = ["nw", "n", "ne", "w", "c", "e", "sw", "s", "se"]
        self.layout: dict = dict(zip(directions, layout))

    def get(self, dir: str):
        return self.layout[dir]

    def can_go(self, dir: str):
        return isinstance(self.layout[dir], Layer)


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
            Key(),
            # Layer([
            #     Key("0", "0"), Key("1", "1"), Key("2", "2"),
            #     Key("3", "3"), Key("4", "4"), Key("5", "5"),
            #     Key("6", "6"), Key("7", "7"), Key("8", "8"),
            # ]),
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
        entity = self.get_current_layer().get(dir)
        if isinstance(entity, Layer):
            self.layer_stack.append(dir)
        elif isinstance(entity, Key):
            if entity.key is None:
                return
            if entity.one_shot_mod:
                self.kb.press(entity.key)
            else:
                self.kb.tap(entity.key)
            self.home()

    def highlight(self, dir: str):
        self.highlighted_layer = dir

    def home(self):
        self.layer_stack = []

    def get_grid_offset(self, index: int, size: int):
        return (index % 3 * size, index // 3 * size)

    def get_current_layer(self):
        current_layer: Layer = self.layout
        for dir in self.layer_stack:
            current_layer = current_layer.get(dir)
        return current_layer

    def show_keyboard_v3(self):
        imgui.begin("vkeyboard_v3")
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()

        current_layer: Layer = self.get_current_layer()

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
                self.widget_key(
                    entity[1],
                    (
                        (255, 255, 255, 0.5)
                        if entity[0] == self.highlighted_layer
                        else (255, 255, 255, 0.1)
                    ),
                )
        if imgui.button("w"):
            self.navigate("w")
        if imgui.button("back"):
            self.home()
        imgui.end()

    def widget_key(self, key: Key, color: tuple):
        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.button(key.label, width=150, height=150)
        imgui.pop_style_color()

    def widget_layer_thumbnail(self, layer: Layer, color: tuple):
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()
        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.button(layer.layout["c"].label, width=150, height=150)
        imgui.pop_style_color()

        imgui.push_style_color(imgui.COLOR_BUTTON, 255, 255, 255, 0.0)
        for idx, dir in enumerate(layer.layout.items()):
            if dir[0] == "c":
                continue
            x_offset, y_offset = self.get_grid_offset(idx, 50)
            imgui.set_cursor_pos((top_left_x + x_offset, top_left_y + y_offset))
            imgui.button(dir[1].label, width=50, height=50)
        imgui.pop_style_color()


class DebounceMachine(StateMachine):
    idle = State(initial=True)
    hold = State()

    press = idle.to(hold) | hold.to(hold)
    wait_finished = hold.to(idle)

    def __init__(self, vkb: VKeyboard):
        self.vkb: VKeyboard = vkb
        self.dir = None
        self.timer: Timer = None
        super(DebounceMachine, self).__init__()
        pass

    def before_press(self, dir, hold_time):
        if self.dir != dir:
            self.dir = dir
            if self.timer is not None:
                self.timer.cancel()
            self.timer = Timer(hold_time, self.wait_finished)
            self.timer.start()
            self.vkb.highlight(self.dir)
            print("holding", dir)

    def on_wait_finished(self):
        print("activate", self.dir)
        self.vkb.navigate(self.dir)
        self.dir = None
        self.timer = None
