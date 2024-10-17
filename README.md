# Chạy trên Linux
```
python -m venv ./venv
source venv/bin/activate
pip install -r requirements.txt
python demo1.py
```

# Notes
## `demo1.py`
- Là file tạm cài lại, chỉ hiện dữ liệu liên quan tới mắt.
- Mặc định phân giải 800x600, 20fps, có thể chỉnh ở đầu file ("Camera parameters")
- Nếu `camera_id = 0` không tìm được webcam ...
## `detect.py`
- Là file gốc lấy từ example mediapipe cho raspberry pi (https://github.com/google-ai-edge/mediapipe-samples/tree/main/examples/face_landmarker/raspberry_pi)
- Chạy `python detect.py --help` để hiện args
