import colorsys
import os
import time

os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
os.environ["PYNPUT_BACKEND_MOUSE"] = "dummy"

from threading import Timer

import imgui
from pynput.keyboard import Controller, Key
from statemachine import State, StateMachine


class K:
    def __init__(self, key="", label: str = "", mod: bool = False):
        self.label: str = label
        self.key = key
        self.mod = mod


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
            K(),
            Layer([
                K(Key.ctrl, "Ctl", True),      K(Key.backspace, "BS"),     K(Key.esc,"Esc"),
                K(Key.shift, "Sft", True),    K(" ", "Spc"),            K(Key.cmd, "Cmd", True),
                K(Key.alt, "Alt", True),        K(Key.enter, "Rtn"),      K(Key.tab, "Tab"),
            ]),
            K(),
            Layer([
                K("1", "1"), K("2", "2"), K("3", "3"),
                K("f", "f"), K("o", "o"), K("b", "b"),
                K("y", "y"), K("u", "u"), K("l", "l"),
            ]),
            K(),
            Layer([
                K(",", ",<"), K(".>", "."), K("/?", "/"),
                K(";", ";:"), K("i", "i"), K("'", "'\""),
                K("j", "j"), K("m", "m"), K("g", "g"),
            ]),
            Layer([
                K("4", "4"), K("5", "5"), K("6", "6"),
                K()        , K("t", "t"), K("z", "z"),
                K("h", "h"), K("s", "s"), K("w", "w"),
            ]),
            Layer([
                K("7", "7"), K("8", "8"), K("9", "9"),
                K("x", "x"), K("e", "e"), K(),
                K("k", "k"), K("r", "r"), K("v", "v"),
            ]),
            Layer([
                K("0", "0"), K("-", "-_"), K("=", "=+"),
                K("q", "q"), K("a", "a"), K("p", "p"),
                K("c", "c"), K("d", "d"), K("n", "n"),
            ]),
        ])
        # fmt: on

        self.layer_stack: list = []
        self.highlighted_layer: str = "c"

    def navigate(self, dir: str):
        if dir == "reset":
            self.clear_modifiers()
            self.home()
            return
        entity = self.get_current_layer().get(dir)
        if isinstance(entity, Layer):
            self.layer_stack.append(dir)
        elif isinstance(entity, K):
            if entity.key == "":
                return
            if entity.mod:
                # self.kb.press(entity.key)
                pass
            else:
                # with self.kb.modifiers:
                self.kb.tap(entity.key)
                self.clear_modifiers()
            self.home()

    def highlight(self, dir: str):
        self.highlighted_layer = dir

    def home(self):
        self.layer_stack = []

    def clear_modifiers(self):
        self.kb.release(Key.ctrl)
        self.kb.release(Key.shift)
        self.kb.release(Key.alt)
        self.kb.release(Key.cmd)

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
        size: int = 300

        for idx, entity in enumerate(current_layer.layout.items()):
            x_offset, y_offset = self.get_grid_offset(idx, size + 10)
            imgui.set_cursor_pos((top_left_x + x_offset, top_left_y + y_offset))
            if isinstance(entity[1], Layer):
                self.widget_layer_thumbnail(
                    entity[1],
                    (
                        (255, 255, 255, 0.5)
                        if entity[0] == self.highlighted_layer
                        else (255, 255, 255, 0.1)
                    ),
                    size,
                )
            if isinstance(entity[1], K):
                self.widget_key(
                    entity[1],
                    (
                        (255, 255, 255, 0.5)
                        if entity[0] == self.highlighted_layer
                        else (255, 255, 255, 0.1)
                    ),
                    size,
                )
        if imgui.button("w"):
            self.navigate("w")
        if imgui.button("back"):
            self.home()
        imgui.end()

    def widget_key(self, key: K, color: tuple, size: int):
        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.button(key.label, width=size, height=size)
        imgui.pop_style_color()

    def widget_layer_thumbnail(self, layer: Layer, color: tuple, size: int):
        top_left_x = imgui.get_cursor_pos_x()
        top_left_y = imgui.get_cursor_pos_y()
        imgui.push_style_color(imgui.COLOR_BUTTON, *color)
        imgui.button(layer.layout["c"].label, width=size, height=size)
        imgui.pop_style_color()

        inner_size: int = size // 3

        imgui.push_style_color(imgui.COLOR_BUTTON, 255, 255, 255, 0.0)
        for idx, dir in enumerate(layer.layout.items()):
            if dir[0] == "c":
                continue
            x_offset, y_offset = self.get_grid_offset(idx, inner_size)
            imgui.set_cursor_pos((top_left_x + x_offset, top_left_y + y_offset))
            imgui.button(dir[1].label, width=inner_size, height=inner_size)
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
