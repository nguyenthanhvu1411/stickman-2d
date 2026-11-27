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

## Dựng video từ kịch bản và giọng thu

Dùng một bản FFmpeg có `libx264` và bộ lọc `subtitles` (libass) để đốt phụ đề.
Tạo `input.txt` UTF-8, mỗi dòng là lời đọc của một cảnh. Dòng trống và tiêu đề bắt đầu bằng `#` được bỏ qua.
Thu giọng theo đúng thứ tự và lưu thành `voice.wav` (cũng nhận MP3/M4A).
Các lệnh dưới chạy tại thư mục `video-cli` với môi trường Python đã cài thư viện.

```cmd
.venv\Scripts\python.exe -m stickman plan input.txt --voice voice.wav
.venv\Scripts\python.exe -m stickman stills input.txt --voice voice.wav
.venv\Scripts\python.exe -m stickman render input.txt --voice voice.wav
```

Trên Linux, thay `.venv\Scripts\python.exe` bằng `.venv/bin/python`.
Mở ảnh `out/contact-001.png` để duyệt cảnh và xem `out/final.mp4` sau khi render.
Video có SFX khi nhãn bật và phụ đề từ kịch bản. Thêm `--music music.mp3` để trộn và hạ nhạc nền khi có lời. Có thể dùng
`--resolution 1080`, `--no-sfx`, `--no-subtitles` và `--output out/ban-moi`.
`master.srt` vẫn được xuất riêng khi tắt đốt phụ đề.

### Chỉnh chữ, tư thế và thời gian

Khi thiếu `--story`, CLI ước lượng mốc theo số từ trong mỗi dòng và ghi `timing_source: estimated` trong `timeline.json`.
Để bám bản thu chính xác hơn, lấy [storyboard mẫu](examples/story.json) làm khung, rồi sửa:

- `end_ms` là mốc kết thúc tuyệt đối tính từ đầu bản thu. Cảnh cuối phải bằng thời lượng giọng đọc (ms).
- `event_ms` là mốc tuyệt đối bật nhãn và phát SFX. `label` là chữ trên bảng.
- `pose` nhận `point` hoặc `idle`. `theme` nhận `whiteboard` hoặc `mint`.
- Mỗi dòng lời đọc cần một cảnh. `schema_version` hiện là 1.

Thêm `--story story.json` vào lệnh `plan`, `stills` và `render` để dùng các mốc bạn chọn.
Nếu render gián đoạn, chạy lại với `resume` và các tham số cũ. Cache clip trong `shots_cache` được tái sử dụng theo nội dung cảnh.
Sau khi sửa một cảnh, chạy lại `render` với cùng thư mục đầu ra để chỉ dựng lại clip đã đổi. Xem `qc.json` để kiểm tra codec, thời lượng và mức âm lượng.
Ví dụ tiếng Việt đi kèm dùng mốc cho bản thu dài 32 giây. Khi dùng bản thu khác, chỉnh lại các mốc hoặc bỏ `--story`.

[Phạm vi CLI và phương án Web Local](Docs/02-video-pipeline.md).
