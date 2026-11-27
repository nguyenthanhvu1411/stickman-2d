# Stickman 2D

Repo gồm game **Stickman Rooftops** và CLI dựng video từ kịch bản và giọng thu bằng Python.

| Tính năng | Chạy ở đâu | Điểm bắt đầu |
| --- | --- | --- |
| Chơi game Stickman Rooftops | Trình duyệt qua GitHub Pages | [Chơi trên web](#chơi-trên-web) |
| Tạo video từ kịch bản và giọng thu | Windows hoặc Linux | [Hướng dẫn CLI video](video-cli/README.md) |

## Chơi trên web

Trong repo, mở **Settings → Pages** và chọn **GitHub Actions** ở mục **Source**.
Sau khi merge Pull Request vào `main`, xem lượt chạy **Build and deploy game** trong tab **Actions**.
Khi deploy thành công, mở URL ở **Settings → Pages**. Người chơi chỉ cần trình duyệt, không cần clone repo hay cài Python.

Game dùng bàn phím. **A/D** hoặc **←/→** để di chuyển, **Space** để nhảy, **R** để chơi lại.
Nhặt đủ bốn đồng xu rồi tới cửa **EXIT**.

## Cài và chạy game khi phát triển

Từ thư mục gốc repo, với Python 3.12:

```sh
python -m pip install -r game/requirements.txt
python game/main.py
```

Chạy `python -m pygbag game` để thử game trong trình duyệt cục bộ. Dùng URL do Pygbag in ra.
Lệnh `python -m pygbag --build game` tạo bản tĩnh trong `game/build/web`.

## Tạo và chỉnh video Stickman

Trong **Code → Download ZIP**, tải và giải nén repo. Mở CMD từ thư mục `video-cli`.
Cài Python và FFmpeg theo [hướng dẫn CLI video](video-cli/README.md).
Trên CMD, có thể chạy cả quy trình bằng một dòng:

```cmd
py -3.12 -m venv .venv && .venv\Scripts\python.exe -m pip install -r requirements.txt && .venv\Scripts\python.exe -m stickman doctor && .venv\Scripts\python.exe -m stickman render-demo
```

Nếu `py --list` chỉ hiện Python 3.13, bạn có thể thử đổi `-3.12` thành `-3.13`. Bản CLI đã kiểm thử với 3.12 trên Linux.

File kết quả là `out/demo.mp4` bên trong `video-cli`. Mở file bằng `start "" "out\demo.mp4"`.
Để chỉnh video mẫu, sửa biến `TITLE` hoặc hàm `draw_scene` trong
[`video-cli/stickman/scene.py`](video-cli/stickman/scene.py), sau đó chạy lại `render-demo`.
Có thể đổi file đích bằng `render-demo --output out/canh-moi.mp4`.
Để dựng video nhiều cảnh, dùng các lệnh `plan`, `stills`, `render` và `resume` theo [hướng dẫn CLI video](video-cli/README.md#dựng-video-từ-kịch-bản-và-giọng-thu). Phần render/chỉnh video chạy cục bộ.
GitHub Pages phục vụ bản game Pygbag.

## Cập nhật qua Pull Request

Push mã lên nhánh tính năng rồi mở Pull Request vào `main`. Workflow kiểm tra bản build
trên PR và deploy khi thay đổi được merge. Đợi lượt deploy thành công rồi tải lại trang game.
