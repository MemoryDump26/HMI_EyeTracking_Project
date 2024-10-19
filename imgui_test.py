import ctypes
import os
import sys
import time

# Linux Wayland workaround
# https://github.com/pygame/pygame/issues/3110#issuecomment-2089118912
os.environ["SDL_VIDEO_X11_FORCE_EGL"] = "1"

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
    ["Left Eye Up", 17, 0.0, 1.0],
    ["Right Eye Up", 18, 0.0, 1.0],
    ["Left Eye Down", 11, 0.0, 1.0],
    ["Right Eye Down", 12, 0.0, 1.0],
]

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
model = "face_landmarker.task"
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

    show_custom_window = True

    running = True
    event = SDL_Event()

    print("OpenGL version :", gl.glGetString(gl.GL_VERSION))
    print("Vendor :", gl.glGetString(gl.GL_VENDOR))
    print("GPU :", gl.glGetString(gl.GL_RENDERER))

    while running:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
                break
            impl.process_event(event)
        impl.process_inputs()

        # cv2.imshow("Demo1", current_frame)

        imgui.new_frame()

        success, current_frame = cap.read()
        if not success:
            sys.exit(
                "ERROR: Unable to read from webcam. Please verify your webcam settings."
            )

        if flip:
            current_frame = cv2.flip(current_frame, 1)

        # Convert the image from BGR to RGB as required by the TFLite model.
        rgb_image = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # Run face landmarker using the model.
        detector.detect_async(mp_image, time.time_ns() // 1_000_000)

        face_blendshapes = None
        if DETECTION_RESULT:
            # Draw landmarks.
            for face_landmarks in DETECTION_RESULT.face_landmarks:
                face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
                face_landmarks_proto.landmark.extend(
                    [
                        landmark_pb2.NormalizedLandmark(
                            x=landmark.x, y=landmark.y, z=landmark.z
                        )
                        for landmark in face_landmarks
                    ]
                )
                mp_drawing.draw_landmarks(
                    image=current_frame,
                    landmark_list=face_landmarks_proto,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_tesselation_style(),
                )
                mp_drawing.draw_landmarks(
                    image=current_frame,
                    landmark_list=face_landmarks_proto,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style(),
                )
                mp_drawing.draw_landmarks(
                    image=current_frame,
                    landmark_list=face_landmarks_proto,
                    connections=mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_iris_connections_style(),
                )
            face_blendshapes = DETECTION_RESULT.face_blendshapes

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
        # imgui.show_test_window()

        if show_custom_window:
            imgui.set_next_window_size(img_width + 100, img_height + 300)
            is_expand, show_custom_window = imgui.begin("Custom window", True)
            if is_expand:
                imgui.image(img_texture, img_width, img_height)
                if face_blendshapes:
                    for idx, category in enumerate(visible_blendshapes):
                        raw_score = face_blendshapes[0][category[1]].score
                        score = (raw_score + category[2]) * category[3]
                        score = round(score, 2)

                        imgui.progress_bar(score, (0, 0), category[0])
                        imgui.push_id(category[0])
                        imgui.same_line()
                        if imgui.button("Trim"):
                            category[2] = -1 * round(raw_score, 2)
                        imgui.same_line()
                        if imgui.button("Scale"):
                            category[3] = round(
                                1 / (raw_score + category[2]),
                                2,
                            )
                        imgui.pop_id()

                if imgui.button("Reset all offset and scale"):
                    for idx, category in enumerate(visible_blendshapes):
                        category[2] = 0.0
                        category[3] = 1.0

                imgui.text(
                    "Look at the center of the screen, and press 'Trim' to make 0.0 'the center'"
                )
                imgui.text(
                    "Look at the edge of then, and press 'Scale' to make 1.0 'the edge'"
                )
            imgui.end()

        gl.glClearColor(1.0, 1.0, 1.0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        SDL_GL_SwapWindow(window)

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
