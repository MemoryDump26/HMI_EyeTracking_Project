# Chạy trên Linux
```
# Setup venv (chỉ cần chạy khi mới clone)
python -m venv ./venv

# Kích hoạt venv khi mở terminal mới (thường thì shell sẽ hiện '(venv)' ở đầu)
source venv/bin/activate

# Chạy nếu có thêm dependency (sau khi đã mở venv)
pip install -r requirements.txt

python demo1.py
```

# Notes
## `demo1.py`
- Là file tạm cài lại, chỉ hiện dữ liệu liên quan tới mắt.
- Mặc định phân giải 800x600, 20fps, có thể chỉnh ở đầu file ("Camera parameters")
- Nếu `camera_id = 0` không tìm được webcam: https://wiki.archlinux.org/title/Webcam_setup
## `detect.py`
- Là file gốc lấy từ example mediapipe cho raspberry pi (https://github.com/google-ai-edge/mediapipe-samples/tree/main/examples/face_landmarker/raspberry_pi)
- Chạy `python detect.py --help` để hiện args