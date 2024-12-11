import ctypes
import os
import sys
import time

# Linux Wayland workaround
# https://github.com/pygame/pygame/issues/3110#issuecomment-2089118912
os.environ["SDL_VIDEO_X11_FORCE_EGL"] = "1"

from threading import Timer

import cv2
import imgui
import mediapipe as mp
import OpenGL.GL as gl
from imgui.integrations.sdl2 import SDL2Renderer
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from sdl2 import *
from statemachine import State, StateMachine

from testwindow import show_test_window
from tracking import Tracking
from vkeyboard import DebounceMachine, VKeyboard

# Naming scheme, eg: eyeLookInLeft = Left eye, look inward (to the right)
# Your webcam might mirror the image by default, see 'flip = False' above
# The mirrored image looks more 'natural', like a mirror
# But blendshapes name will be flipped horizontally,
# eg: Left eye, look inward (to the right) -> Right eye, look inward (to the left)


# Visible blendshapes
# [Custom name, ID (see below), offset, scale]
visible_blendshapes = [
    ["Left Brow Up", 4, 0.0, 1.0],
    ["Right Brow Up", 5, 0.0, 1.0],
    ["Left Eye Blink", 9, 0.0, 1.0],
    ["Right Eye Blink", 10, 0.0, 1.0],
    ["Left Eye Up", 17, 0.0, 1.0],
    ["Right Eye Up", 18, 0.0, 1.0],
    ["Left Eye Down", 11, 0.0, 1.0],
    ["Right Eye Down", 12, 0.0, 1.0],
    ["Left Eye Left", 15, 0.0, 1.0],
    ["Right Eye Left", 14, 0.0, 1.0],
    ["Left Eye Right", 13, 0.0, 1.0],
    ["Right Eye Right", 16, 0.0, 1.0],
]

gaze_test = [
    ["Gaze X Axis", 0.0, 1.0, 1.0],
    ["Gaze Y Axis", 0.0, 1.0, 1.0],
]

# BROW_DOWN_LEFT = 1
# BROW_DOWN_RIGHT = 2
# BROW_INNER_UP = 3
# BROW_OUTER_UP_LEFT = 4
# BROW_OUTER_UP_RIGHT = 5
# EYE_BLINK_LEFT = 9
# EYE_BLINK_RIGHT = 10
# EYE_LOOK_DOWN_LEFT = 11
# EYE_LOOK_DOWN_RIGHT = 12
# EYE_LOOK_IN_LEFT = 13
# EYE_LOOK_IN_RIGHT = 14
# EYE_LOOK_OUT_LEFT = 15
# EYE_LOOK_OUT_RIGHT = 16
# EYE_LOOK_UP_LEFT = 17
# EYE_LOOK_UP_RIGHT = 18
# EYE_SQUINT_LEFT = 19
# EYE_SQUINT_RIGHT = 20
# EYE_WIDE_LEFT = 21
# EYE_WIDE_RIGHT = 22


def main():
    window, gl_context = impl_pysdl2_init()
    imgui.create_context()
    impl = SDL2Renderer(window)

    io = imgui.get_io()
    custom_font = io.fonts.add_font_from_file_ttf("NotoSansMono-Regular.ttf", 32)
    keyboard_font = io.fonts.add_font_from_file_ttf("NotoSansMono-Black.ttf", 64)
    impl.refresh_font_texture()

    print("OpenGL version :", gl.glGetString(gl.GL_VERSION))
    print("Vendor :", gl.glGetString(gl.GL_VENDOR))
    print("GPU :", gl.glGetString(gl.GL_RENDERER))

    event = SDL_Event()
    tracking = Tracking()
    vkb = VKeyboard()
    debounce = DebounceMachine(vkb)
    debounce._graph().write_png("./fsm.png")
    show_custom_window = True
    running = True
    input_enabled = False

    while running:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
                break
            impl.process_event(event)
        impl.process_inputs()

        imgui.new_frame()
        imgui.push_font(custom_font)

        current_frame, face_blendshapes = tracking.update()
        img_texture, img_width, img_height = image_to_texture(current_frame)

        show_test_window()

        viewport = imgui.get_main_viewport()
        imgui.set_next_window_position(viewport.pos[0], viewport.pos[1])
        imgui.set_next_window_size(viewport.size[0], viewport.size[1])

        imgui.push_font(keyboard_font)
        vkb.show_keyboard_v3()
        imgui.pop_font()

        if show_custom_window:
            # imgui.set_next_window_size(img_width + 100, img_height + 500)
            is_expand, show_custom_window = imgui.begin("Config")
            if is_expand:
                imgui.image(img_texture, img_width / 2, img_height / 2)
                if face_blendshapes:
                    for idx, category in enumerate(visible_blendshapes):
                        raw_score = face_blendshapes[category[1]].score
                        score = (raw_score + category[2]) * category[3]
                        score = round(score, 2)
                        imgui.progress_bar(score, (0, 0), category[0])

                    directions = ["nw", "n", "ne", "w", "c", "e", "sw", "s", "se"]

                    for idx, dir in enumerate(directions):
                        if imgui.button(dir):
                            tracking.take_blendshape_snapshot(dir)
                        if (idx + 1) % 3 != 0:
                            imgui.same_line()

                    if imgui.button("reset"):
                        tracking.take_blendshape_snapshot("reset")

                    deltas = tracking.sorted_delta()
                    for d in deltas:
                        imgui.slider_float(
                            d[0] + "_delta",
                            -1 * d[1],
                            -10,
                            0,
                        )

                    if len(deltas):
                        debounce.press(deltas[0][0], 1)

            imgui.end()

        gl.glClearColor(1.0, 1.0, 1.0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.pop_font()
        imgui.render()
        impl.render(imgui.get_draw_data())
        SDL_GL_SwapWindow(window)
        # killed my memory lol
        img_texture = None

    # cap.release()
    cv2.destroyAllWindows()

    impl.shutdown()
    SDL_GL_DeleteContext(gl_context)
    SDL_DestroyWindow(window)
    SDL_Quit()


def image_to_texture(IMG):
    img_gl = cv2.cvtColor(IMG, cv2.COLOR_BGR2RGB)  # convert color
    height, width = img_gl.shape[:2]  # get shape

    texture = gl.glGenTextures(1)

    gl.glActiveTexture(gl.GL_TEXTURE0)

    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)

    gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,
        0,
        gl.GL_RGB,
        width,
        height,
        0,
        gl.GL_RGB,
        gl.GL_UNSIGNED_BYTE,
        img_gl,
    )

    return texture, width, height


def impl_pysdl2_init():
    width, height = 1280, 720
    window_name = "minimal ImGui/SDL2 example"

    if SDL_Init(SDL_INIT_EVERYTHING) < 0:
        print(
            "Error: SDL could not initialize! SDL Error: "
            + SDL_GetError().decode("utf-8")
        )
        sys.exit(1)

    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24)
    SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)
    SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
    SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 8)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 4)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE)

    SDL_SetHint(SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1")
    SDL_SetHint(SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")

    window = SDL_CreateWindow(
        window_name.encode("utf-8"),
        SDL_WINDOWPOS_CENTERED,
        SDL_WINDOWPOS_CENTERED,
        width,
        height,
        SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE,
    )

    if window is None:
        print(
            "Error: Window could not be created! SDL Error: "
            + SDL_GetError().decode("utf-8")
        )
        sys.exit(1)

    gl_context = SDL_GL_CreateContext(window)
    if gl_context is None:
        print(
            "Error: Cannot create OpenGL Context! SDL Error: "
            + SDL_GetError().decode("utf-8")
        )
        sys.exit(1)

    SDL_GL_MakeCurrent(window, gl_context)
    if SDL_GL_SetSwapInterval(1) < 0:
        print(
            "Warning: Unable to set VSync! SDL Error: " + SDL_GetError().decode("utf-8")
        )
        sys.exit(1)

    return window, gl_context


if __name__ == "__main__":
    main()
