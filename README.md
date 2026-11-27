# Stickman Studio

Ứng dụng web tạo video Stickman 2D bằng Python, Streamlit, Skia và FFmpeg.

1. **Tạo kịch bản** từ chủ đề với OpenAI hoặc dán lời thoại, mỗi dòng một cảnh.
2. **Chỉnh cảnh** trong bảng. Có thể sửa lời thoại, chữ trên bảng, tư thế, bối cảnh và xem ảnh xem trước.
3. **Chọn giọng và khung hình.** Có tiếng Việt/Anh, 16:9 ngang hoặc 9:16 dọc, 720p/1080p, tùy chọn nhạc nền, SFX, phụ đề. Nếu có giọng thu, tải WAV/MP3/M4A lên.
4. **Render MP4**, xem video và tải MP4, SRT hoặc báo cáo QC. Kết quả được giữ trong phiên web hiện tại.

Edge TTS tạo giọng từng cảnh và dùng mốc từ để tạo phụ đề. Nếu một cảnh thiếu mốc từ, phụ đề cảnh đó dùng khoảng thời gian của toàn cảnh. Với giọng thu tải lên, mốc cảnh là ước lượng. Mỗi lượt render web hỗ trợ tối đa 3 phút.

## Deploy trên Streamlit Community Cloud

1. Mở [Streamlit Community Cloud](https://share.streamlit.io/) và kết nối tài khoản GitHub có quyền với repo.
2. Chọn **Create app**. Điền repository `nguyenthanhvu1411/stickman-2d`, branch `feat/stickman-game-and-video-demo` và main file `app.py`. Sau khi bản Studio vào `main`, có thể triển khai từ `main` để cập nhật sau mỗi lần merge.
3. Chọn Python **3.12** trong cài đặt nâng cao. Cloud đọc `requirements.txt` và cài FFmpeg từ `packages.txt`.
4. Bấm **Deploy** và dùng URL `.streamlit.app` được cấp. Push lên branch mà app đang theo dõi để Cloud nhận bản cập nhật.

API key OpenAI có thể được nhập vào ô mật khẩu trong app. Với bản riêng tự quản lý, có thể cấu hình `OPENAI_API_KEY` qua môi trường hoặc Streamlit Secrets và tùy chọn `OPENAI_MODEL`. Không ghi key vào Git. Tránh dùng key chung cho app công khai vì người truy cập có thể tạo yêu cầu tính phí. Dán kịch bản có sẵn dùng được mà không cần key OpenAI.

## Chạy trên máy

Cài Python 3.12 và FFmpeg có `ffmpeg`, `ffprobe`, `libx264` và `libass` trong PATH.
Mở CMD ở thư mục chứa `app.py` rồi chạy một dòng:

```cmd
py -3.12 -m venv .venv && .venv\Scripts\python.exe -m pip install -r requirements.txt && .venv\Scripts\python.exe -m streamlit run app.py
```

Trên Linux, chạy `python3.12 -m venv .venv`, sau đó `.venv/bin/python -m pip install -r requirements.txt` và `.venv/bin/python -m streamlit run app.py`. Mở địa chỉ localhost được in trên màn hình.

## Mã nguồn

| Thành phần | Tệp |
| --- | --- |
| Giao diện nhập chủ đề, chỉnh cảnh, xem và tải video | `app.py` |
| Kịch bản OpenAI và kiểm tra dữ liệu cảnh | `studio/script.py` |
| Edge TTS, timestamp và SRT | `studio/voice.py` |
| Kết nối giao diện với engine | `studio/project.py` |
| Vẽ Skia, dựng timeline và hậu kỳ FFmpeg | `video-cli/stickman/` |

[Hướng dẫn CLI và sửa storyboard JSON](video-cli/README.md).
