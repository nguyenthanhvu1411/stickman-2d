"""Stream Skia frames to FFmpeg and publish a complete clip."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


def encode(output, width, height, frame_count, draw):
    import skia

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    surface = skia.Surface(width, height)
    with TemporaryDirectory(prefix=".render-", dir=output.parent) as temp:
        draft = Path(temp) / "demo.mp4"
        log_path = Path(temp) / "ffmpeg.log"
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "rawvideo", "-pixel_format", "bgra",
            "-video_size", f"{width}x{height}",
            "-framerate", "30", "-i", "pipe:0",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(draft),
        ]
        with log_path.open("wb") as log, subprocess.Popen(
            command, stdin=subprocess.PIPE, stderr=log
        ) as encoder:
            pipe_closed_early = False
            try:
                with encoder.stdin as pipe:
                    for frame in range(frame_count):
                        draw(surface.getCanvas(), frame)
                        image = surface.makeImageSnapshot()
                        pixels = image.toarray(colorType=skia.ColorType.kBGRA_8888_ColorType)
                        pipe.write(memoryview(pixels).cast("B"))
            except BrokenPipeError:
                pipe_closed_early = True
            except BaseException:
                encoder.terminate()
                raise
            if encoder.wait() or pipe_closed_early:
                details = log_path.read_text(encoding="utf-8", errors="replace").strip()
                raise RuntimeError(f"FFmpeg xuất video thất bại (mã {encoder.returncode}). {details}")
        draft.replace(output)
    print(f"Đã xuất {output}")
