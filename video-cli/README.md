# Stickman 2D CLI

Task 01 dựng một cảnh Stickman chỉ tay vào bảng trắng. Dòng “Ý tưởng đầu tiên” bật lên sau 1,2 giây. Video mẫu dài 5 giây và chạy hoàn toàn cục bộ.

## Cài và chạy trên Windows 10/11

Cài Python 3.12 và bản FFmpeg có cả `ffmpeg.exe`, `ffprobe.exe` và encoder `libx264`. Thêm thư mục `bin` của FFmpeg vào `PATH` rồi mở PowerShell mới. Mở PowerShell tại thư mục chứa README và chạy:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m stickman doctor
.\.venv\Scripts\python.exe -m stickman render-demo
```

## Chạy trên Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m stickman doctor
.venv/bin/python -m stickman render-demo
```

Video được xuất ra `out/demo.mp4`. Dùng `render-demo --output "đường dẫn/demo.mp4"` để đổi vị trí xuất. Lệnh dùng font Noto Sans Bold đi kèm. Có thể truyền `--font "đường dẫn/font.ttf"` sau `doctor` hoặc `render-demo` để dùng font khác. `doctor` trả mã thoát 1 khi thiếu thành phần.

Kiểm tra video bằng lệnh sau:

```text
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate,duration,nb_read_frames,pix_fmt -of json out/demo.mp4
```

Kết quả mong đợi là H.264, 1280 × 720, 30 fps, 150 khung hình trong 5 giây. Xem [phạm vi và kết quả nghiệm thu](Docs/01-cli-mvp.md).
