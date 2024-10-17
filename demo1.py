import argparse
import sys
import time

import cv2
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Camera parameters
camera_id = 0
width = 800
height = 600
cap_fps = 20
flip = True

# Demo GUI parameters
blendshape_background_color = (255, 255, 255)  # White
blendshape_padding_width = 1000  # pixels
blendshape_padding_height = 500  # pixels

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

# Main loop
while cap.isOpened():
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

    # Expand the right & bottom side frame to show the blendshapes.
    current_frame = cv2.copyMakeBorder(
        current_frame,
        0,
        blendshape_padding_height,
        0,
        blendshape_padding_width,
        cv2.BORDER_CONSTANT,
        None,
        blendshape_background_color,
    )

    if DETECTION_RESULT:
        # Define parameters for the bars and text
        legend_x = (
            # current_frame.shape[1] - blendshape_padding_width + 20
            20  # Starting X-coordinate (20 as a margin)
        )
        legend_y = (
            current_frame.shape[0] - blendshape_padding_height + 20
        )  # Starting Y-coordinate
        bar_max_width = (
            blendshape_padding_width - 200
        )  # Max width of the bar with some margin
        bar_height = 15  # Height of the bar
        gap_between_bars = 8  # Gap between two bars
        text_gap = 5  # Gap between the end of the text and the start of the bar

        face_blendshapes = DETECTION_RESULT.face_blendshapes

        if face_blendshapes:
            for idx, category in enumerate(face_blendshapes[0]):
                category_name = category.category_name
                # Eyes-related blendshape only
                if category_name[:3] != "eye" and category_name[:4] != "brow":
                    continue
                score = round(category.score, 2)

                # Prepare text and get its width
                text = "{} ({:.2f})".format(category_name, score)
                (text_width, _), _ = cv2.getTextSize(
                    text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
                )

                # Display the blendshape name and score
                cv2.putText(
                    current_frame,
                    text,
                    (legend_x, legend_y + (bar_height // 2) + 5),
                    # Position adjusted for vertical centering
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,  # Font size
                    (0, 0, 0),  # Black color
                    1,
                    cv2.LINE_AA,
                )  # Thickness

                # Calculate bar width based on score
                bar_width = int(bar_max_width * score)

                # Draw the bar to the right of the text
                cv2.rectangle(
                    current_frame,
                    (legend_x + text_width + text_gap, legend_y),
                    (
                        legend_x + text_width + text_gap + bar_width,
                        legend_y + bar_height,
                    ),
                    (0, 255, 0),  # Green color
                    -1,
                )  # Filled bar

                # Update the Y-coordinate for the next bar
                legend_y += bar_height + gap_between_bars

    cv2.imshow("Demo1", current_frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
