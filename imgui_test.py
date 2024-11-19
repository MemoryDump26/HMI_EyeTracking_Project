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

from testwindow import show_test_window
from tracking import Tracking
from vkeyboard import VKeyboard

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Camera parameters
camera_id = 2
width = 800
height = 600
cap_fps = 20
flip = False

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

# Global variables
DETECTION_RESULT = None

# Detector parameters
model = r"face_landmarker.task"
num_faces = 1
min_face_detection_confidence = 0.5
min_face_presence_confidence = 0.5
min_tracking_confidence = 0.5


# Detector callback
def save_result(
    result: vision.FaceLandmarkerResult,
    unused_output_image: mp.Image,
    timestamp_ms: int,
):
    # global FPS, COUNTER, START_TIME, DETECTION_RESULT
    global DETECTION_RESULT
    #
    # Calculate the FPS
    # if COUNTER % fps_avg_frame_count == 0:
    #     FPS = fps_avg_frame_count / (time.time() - START_TIME)
    # START_TIME = time.time()
    #
    DETECTION_RESULT = result
    # COUNTER += 1


# Initialize the face landmarker model
base_options = python.BaseOptions(model_asset_path=model)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.LIVE_STREAM,
    num_faces=num_faces,
    min_face_detection_confidence=min_face_detection_confidence,
    min_face_presence_confidence=min_face_presence_confidence,
    min_tracking_confidence=min_tracking_confidence,
    output_face_blendshapes=True,
    result_callback=save_result,
)
detector = vision.FaceLandmarker.create_from_options(options)


# Webcam setup
cap = cv2.VideoCapture(camera_id)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FPS, cap_fps)


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


def main():
    window, gl_context = impl_pysdl2_init()
    imgui.create_context()
    impl = SDL2Renderer(window)

    io = imgui.get_io()
    custom_font = io.fonts.add_font_from_file_ttf("NotoSansMono-Regular.ttf", 24)
    keyboard_font = io.fonts.add_font_from_file_ttf("NotoSansMono-Regular.ttf", 128)
    impl.refresh_font_texture()

    show_custom_window = True

    running = True
    event = SDL_Event()

    print("OpenGL version :", gl.glGetString(gl.GL_VERSION))
    print("Vendor :", gl.glGetString(gl.GL_VENDOR))
    print("GPU :", gl.glGetString(gl.GL_RENDERER))

    tracking = Tracking()
    vkb = VKeyboard()
    vkb_move_timer = None
    vkb_commit_timer = None
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

        # success, current_frame = cap.read()
        # if not success:
        #     sys.exit(
        #         "ERROR: Unable to read from webcam. Please verify your webcam settings."
        #     )
        #
        # if flip:
        #     current_frame = cv2.flip(current_frame, 1)
        #
        # # Convert the image from BGR to RGB as required by the TFLite model.
        # rgb_image = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
        # mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        #
        # # Run face landmarker using the model.
        # detector.detect_async(mp_image, time.time_ns() // 1_000_000)

        current_frame, face_blendshapes = tracking.update()

        # face_blendshapes = None
        # if detection_result:
        #     # Draw landmarks.
        #     for face_landmarks in detection_result.face_landmarks:
        #         face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        #         face_landmarks_proto.landmark.extend(
        #             [
        #                 landmark_pb2.NormalizedLandmark(
        #                     x=landmark.x, y=landmark.y, z=landmark.z
        #                 )
        #                 for landmark in face_landmarks
        #             ]
        #         )
        #         mp_drawing.draw_landmarks(
        #             image=current_frame,
        #             landmark_list=face_landmarks_proto,
        #             connections=mp_face_mesh.FACEMESH_TESSELATION,
        #             landmark_drawing_spec=None,
        #             connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_tesselation_style(),
        #         )
        #         mp_drawing.draw_landmarks(
        #             image=current_frame,
        #             landmark_list=face_landmarks_proto,
        #             connections=mp_face_mesh.FACEMESH_CONTOURS,
        #             landmark_drawing_spec=None,
        #             connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style(),
        #         )
        #         mp_drawing.draw_landmarks(
        #             image=current_frame,
        #             landmark_list=face_landmarks_proto,
        #             connections=mp_face_mesh.FACEMESH_IRISES,
        #             landmark_drawing_spec=None,
        #             connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_iris_connections_style(),
        #         )
        #     face_blendshapes = detection_result.face_blendshapes

        img_texture, img_width, img_height = image_to_texture(current_frame)

        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):

                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", "Cmd+Q", False, True
                )

                if clicked_quit:
                    sys.exit(0)

                imgui.end_menu()
            imgui.end_main_menu_bar()

        show_test_window()
        imgui.push_font(keyboard_font)
        vkb.show_keyboard()
        imgui.pop_font()

        if show_custom_window:
            # imgui.set_next_window_size(img_width + 100, img_height + 500)
            is_expand, show_custom_window = imgui.begin("Custom window", True)
            if is_expand:
                imgui.image(img_texture, img_width / 2, img_height / 2)
                if face_blendshapes:
                    for idx, category in enumerate(visible_blendshapes):
                        raw_score = face_blendshapes[0][category[1]].score
                        score = (raw_score + category[2]) * category[3]
                        score = round(score, 2)
                        imgui.progress_bar(score, (0, 0), category[0])

                    # Calculate gaze?
                    gaze_x_axis_raw_score = (
                        face_blendshapes[0][13].score
                        + face_blendshapes[0][16].score
                        - face_blendshapes[0][14].score
                        - face_blendshapes[0][15].score
                    )

                    gaze_x_axis_score = gaze_x_axis_raw_score + gaze_test[0][1]
                    gaze_x_axis_score *= (
                        gaze_test[0][2] if (gaze_x_axis_score < 0) else gaze_test[0][3]
                    )
                    gaze_x_axis_score = round(gaze_x_axis_score, 2)

                    gaze_y_axis_raw_score = (
                        face_blendshapes[0][17].score
                        + face_blendshapes[0][18].score
                        - face_blendshapes[0][11].score
                        - face_blendshapes[0][12].score
                    )

                    gaze_y_axis_score = gaze_y_axis_raw_score + gaze_test[1][1]
                    gaze_y_axis_score *= (
                        gaze_test[1][2] if (gaze_y_axis_score < 0) else gaze_test[1][3]
                    )
                    gaze_y_axis_score = round(gaze_y_axis_score, 2)

                    brow_left_up_score = face_blendshapes[0][4].score
                    brow_right_up_score = face_blendshapes[0][5].score
                    # gaze_test[0][1]: offset ("center" the reading)
                    # gaze_test[0][2]: scale "down" (set where you're looking as 'maximum downward')
                    # gaze_test[0][3]: scale "up"

                    # Really, really ugly code here
                    def go_up():
                        nonlocal vkb, vkb_move_timer
                        vkb.nav_up()
                        vkb_move_timer = None

                    def go_down():
                        nonlocal vkb, vkb_move_timer
                        vkb.nav_down()
                        vkb_move_timer = None

                    def go_left():
                        nonlocal vkb, vkb_move_timer
                        vkb.nav_left()
                        vkb_move_timer = None

                    def go_right():
                        nonlocal vkb, vkb_move_timer
                        vkb.nav_right()
                        vkb_move_timer = None

                    def press_current_key():
                        nonlocal vkb, vkb_commit_timer
                        vkb.press_current_key()
                        vkb_commit_timer = None

                    hold_time = 1
                    commit_time = 1

                    # Even more ugly code lol
                    if input_enabled:
                        if vkb_move_timer is None:
                            if gaze_y_axis_score > 1.5:
                                vkb_move_timer = Timer(hold_time, go_up)
                                vkb_move_timer.start()
                            elif gaze_y_axis_score < -1.5:
                                vkb_move_timer = Timer(hold_time, go_down)
                                vkb_move_timer.start()
                            elif gaze_x_axis_score > 1.5:
                                vkb_move_timer = Timer(hold_time, go_right)
                                vkb_move_timer.start()
                            elif gaze_x_axis_score < -1.5:
                                vkb_move_timer = Timer(hold_time, go_left)
                                vkb_move_timer.start()
                        else:
                            if (
                                abs(gaze_y_axis_score) < 1.5
                                and abs(gaze_x_axis_score) < 1.5
                            ):
                                vkb_move_timer.cancel()
                                vkb_move_timer = None

                        if vkb_commit_timer is None:
                            if brow_left_up_score > 0.4 or brow_right_up_score > 0.4:
                                vkb_commit_timer = Timer(commit_time, press_current_key)
                                vkb_commit_timer.start()
                        else:
                            if brow_left_up_score < 0.4 and brow_right_up_score < 0.4:
                                vkb_commit_timer.cancel()
                                vkb_commit_timer = None

                    def trim(raw_score: float):
                        return -1 * round(raw_score, 2)

                    def scale(raw_score: float, offset: float):
                        return abs(round(2 / (raw_score + offset), 2))

                    imgui.slider_float(gaze_test[0][0], gaze_x_axis_score, -2, 2)
                    if imgui.button("Center##X"):
                        gaze_test[0][1] = trim(gaze_x_axis_raw_score)
                    imgui.same_line()
                    if imgui.button("Min##X"):
                        gaze_test[0][2] = scale(gaze_x_axis_raw_score, gaze_test[0][1])
                    imgui.same_line()
                    if imgui.button("Max##X"):
                        gaze_test[0][3] = scale(gaze_x_axis_raw_score, gaze_test[0][1])

                    imgui.slider_float(gaze_test[1][0], gaze_y_axis_score, -2, 2)
                    if imgui.button("Center##Y"):
                        gaze_test[1][1] = trim(gaze_y_axis_raw_score)
                    imgui.same_line()
                    if imgui.button("Min##Y"):
                        gaze_test[1][2] = scale(gaze_y_axis_raw_score, gaze_test[1][1])
                    imgui.same_line()
                    if imgui.button("Max##Y"):
                        gaze_test[1][3] = scale(gaze_y_axis_raw_score, gaze_test[1][1])

                _, input_enabled = imgui.checkbox("Input enabled", input_enabled)

                if imgui.button("Reset all offset and scale"):
                    for idx, category in enumerate(visible_blendshapes):
                        category[2] = 0.0
                        category[3] = 1.0
                    for idx, gaze_dir in enumerate(gaze_test):
                        gaze_dir[1] = 0.0
                        gaze_dir[2] = 1.0
                        gaze_dir[3] = 1.0

                # imgui.text(
                #     "Look at the center of the screen, and press 'Trim' to make 0.0 'the center'"
                # )
                # imgui.text(
                #     "Look at the edge of then, and press 'Scale' to make 1.0 'the edge'"
                # )
            imgui.end()

        gl.glClearColor(1.0, 1.0, 1.0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.pop_font()
        imgui.render()
        impl.render(imgui.get_draw_data())
        SDL_GL_SwapWindow(window)
        # killed my memory lol
        img_texture = None

    cap.release()
    cv2.destroyAllWindows()

    impl.shutdown()
    SDL_GL_DeleteContext(gl_context)
    SDL_DestroyWindow(window)
    SDL_Quit()


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
