import time
from threading import Timer

import cv2
import mediapipe as mp
import OpenGL.GL as gl
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from statemachine import State, StateMachine

from vkeyboard import VKeyboard


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


class Tracking:
    def __init__(self):
        # Detector parameters
        model = r"face_landmarker.task"
        num_faces = 1
        min_face_detection_confidence = 0.5
        min_face_presence_confidence = 0.5
        min_tracking_confidence = 0.5

        camera_id = 0
        width = 800
        height = 600
        cap_fps = 20
        flip = False

        def save_result(
            result: vision.FaceLandmarkerResult,
            unused_output_image: mp.Image,
            timestamp_ms: int,
        ):
            self.result = result

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
        self._detector = vision.FaceLandmarker.create_from_options(options)

        # Webcam setup
        self._cap = cv2.VideoCapture(camera_id)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, cap_fps)

        self.result = None
        self.blendshape_snapshots: dict = {}
        self.blendshape_deltas: dict[float] = {}

    def take_blendshape_snapshot(self, dir: str):
        if self.result:
            self.blendshape_snapshots[dir] = self.result.face_blendshapes[0]

    def update(self):
        success, current_frame = self._cap.read()
        if not success:
            sys.exit(
                "ERROR: Unable to read from webcam. Please verify your webcam settings."
            )

        # Convert the image from BGR to RGB as required by the TFLite model.
        rgb_image = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        self._detector.detect_async(mp_image, time.time_ns() // 1_000_000)

        face_blendshapes = None
        if self.result:
            mp_face_mesh = mp.solutions.face_mesh
            mp_drawing = mp.solutions.drawing_utils
            mp_drawing_styles = mp.solutions.drawing_styles

            # Draw landmarks.
            for face_landmarks in self.result.face_landmarks:
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
            if self.result.face_blendshapes:
                face_blendshapes = self.result.face_blendshapes[0]
                for dir, snapshot in self.blendshape_snapshots.items():
                    delta = 0
                    for idx, blendshape in enumerate(face_blendshapes):
                        delta += abs(blendshape.score - snapshot[idx].score)
                    self.blendshape_deltas[dir] = delta

        return current_frame, face_blendshapes

    def sorted_delta(self) -> dict:
        return sorted(self.blendshape_deltas.items(), key=lambda item: item[1])

    def __del__(self):
        self._cap.release()
