# Task 01 — CLI render demo

## Phạm vi

Cảnh mẫu cố định chạy từ Python bằng Skia, đưa trực tiếp frame BGRA vào FFmpeg. Stickman giơ tay chỉ vào bảng trắng, sau đó chữ “Ý tưởng đầu tiên” phóng to, vượt nhẹ kích thước đích rồi ổn định. Gói có font Noto Sans Bold và giấy phép tương ứng. Video demo chỉ có hình. Nhập kịch bản, âm thanh, LLM, TTS, ASR, giao diện, EXE và SaaS thuộc các giai đoạn sau.

## Điều kiện nghiệm thu và kết quả

| Điều kiện | Kết quả trên Linux |
| --- | --- |
| `doctor` chạy và kiểm tra công cụ | Đạt với Python 3.12.14, Skia 144.1 và FFmpeg/ffprobe 7.1.5. Đã kiểm tra encoder libx264 và glyph cho toàn bộ dòng chữ. |
| Báo lỗi có hướng khắc phục | Đã thử thiếu Skia, font và FFmpeg/ffprobe. Lệnh trả mã 1 và chỉ rõ thành phần cần cài hoặc cấu hình lại. |
| `render-demo` tạo MP4 | Đạt tại `out/demo.mp4`. FFmpeg ghi ra file tạm trước khi thay file đích bằng kết quả đã xuất thành công. |
| Thông số qua ffprobe | H.264, 1280 × 720, yuv420p, 30/1 fps, 150 frame giải mã được, 5.000 giây. |
| Đọc đúng chữ và thấy hiệu ứng bật | Đã xem bốn frame 28, 40, 52 và 95, đếm từ 0. Bảng còn trống ở frame 28. Cỡ chữ thay đổi qua các frame kế tiếp và dấu tiếng Việt hiển thị đầy đủ. |

Skia trên Linux phát cảnh báo Fontconfig nhưng font kèm theo vẫn nạp được và video xuất thành công.

## Nghiệm thu còn lại trên Windows 10/11

Trên Windows, chạy lại các lệnh PowerShell trong README và lệnh ffprobe. Kiểm tra cài dependency trong môi trường sạch, phát MP4 và thử xuất vào đường dẫn có dấu tiếng Việt và khoảng trắng. Phiên làm việc này kiểm thử trên Linux.
