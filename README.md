# Bài tập lớn nhóm 6 lớp Tương tác người - máy (INT2041)

## Thành viên nhóm:
| Tên               | MSV      | Đóng góp | Nội dung                           |
| ----------------- | -------- | -------- | ---------------------------------- |
| Lê Trọng Bảo      | 21020608 | 40%      | Cài đặt giải pháp, thiết kế layout |
| Lưu Văn Đức Thiệu | 21020476 | 30%      | Refactor code, báo cáo, slide      |
| Trịnh Xuân Đạt    | 21021477 | 30%      | Báo cáo, slide thuyết trình        |

# Linux

## Lần đầu sử dụng
```
# Người dùng cần ở trong group "input" và "tty"
sudo usermod -a -G input $USER
sudo usermod -a -G tty $USER

# Tạo luật udev & kích hoạt
echo 'KERNEL=="uinput", MODE="0660", GROUP="input"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm trigger

# Tự động load module uinput khi khởi động
echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf
```
## Chạy ứng dụng
```
# Setup venv (chỉ cần chạy khi mới clone)
python -m venv ./venv

# Kích hoạt venv khi mở terminal mới (thường thì shell sẽ hiện '(venv)' ở đầu)
source venv/bin/activate

# Chạy nếu cần thêm dependency mới (sau khi đã mở venv)
pip install -r requirements.txt

python imgui_test.py
```

# Windows (untested)

## Lần đầu sử dụng
Tại dòng 5 file vkeyboard.py:
```
os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
```
Sửa thành:
```
os.environ["PYNPUT_BACKEND_KEYBOARD"] = "win32"
```
## Chạy ứng dụng
```
Shift + Right click trong folder -> open Powershell/Command Prompt

# Setup venv (chỉ cần chạy khi mới clone)
python -m venv ./venv

# Kích hoạt venv khi mở terminal mới (thường thì shell sẽ hiện '(venv)' ở đầu)
.\venv\bin\Activate.ps1

# Chạy nếu có thêm dependency (sau khi đã mở venv)
pip install -r requirements.txt

python imgui_test.py
```
