# CLI dựng video từ kịch bản và giọng thu

## Luồng chạy

1. `plan` đọc TXT và xác định thời lượng nguồn bằng ffprobe. Nó kiểm tra số cảnh và các mốc tuyệt đối trong storyboard phiên bản 1. Khi không có storyboard, tạo timeline dựa trên tỷ lệ độ dài lời đọc.
2. `stills` dựng ảnh từng cảnh và contact sheet bằng engine Skia đang dùng cho video.
3. `render` hoặc `resume` kết xuất từng clip theo chỉ số frame 30 fps. Mỗi clip lưu dưới hash của thiết lập render, font, mã engine và dữ liệu hình ảnh của cảnh. Audio và phụ đề được dựng lại khi xuất.
4. FFmpeg ghép clip, trộn giọng, nhạc nền nếu được cung cấp và tiếng pop theo sự kiện. Bước chuẩn hóa đo mức âm lượng trước khi điều chỉnh. Phụ đề được đốt ở lượt xuất cuối. Nếu tắt đốt, luồng hình được sao chép từ các clip.
5. Xuất MP4, SRT, timeline và báo cáo QC. Lỗi giải mã, sai codec hoặc thời lượng sẽ dừng xuất. Mức âm lượng ngoài dung sai được ghi cảnh báo.

## Phạm vi hiện tại

CLI nhận giọng thu hoặc file TTS người dùng cung cấp. Chế độ tự chia mốc là ước lượng cấp cảnh. Chế độ thủ công nhận mốc ms tuyệt đối cho từng hiệu ứng. Đặc tả storyboard v1 của CLI này hiện giới hạn ở các trường trong `examples/story.json`.
Đầu ra dùng thư mục người dùng chỉ định. Dùng các thư mục khác nhau cho các lượt render cần chạy đồng thời.

Các phần kế tiếp gồm adapter LLM/TTS, căn timestamp theo từ bằng ASR, import DOCX, và Web Local có màn hình nhập kịch bản, chỉnh storyboard, duyệt ảnh, theo dõi job và tải MP4. GitHub Pages phục vụ game và Web Local sẽ dùng máy có Python, Skia và FFmpeg để xử lý video.

## Kiểm thử

Dùng Python 3.12 trên Linux. Kiểm tra render demo, pipeline 32 giây với giọng tổng hợp dùng làm dữ liệu kiểm thử và nhạc thử, chế độ thủ công, phụ đề có dấu và tái dùng cache khi chạy lại. Windows cần xác nhận cách cài FFmpeg có libass và chạy với đường dẫn chứa dấu/khoảng trắng.
