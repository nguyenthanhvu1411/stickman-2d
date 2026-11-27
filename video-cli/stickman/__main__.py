"""Command-line entry point for environment checks and the render demo."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def check_tools(font_path):
    errors = []
    print(f"Python {sys.version.split()[0]}")
    if sys.version_info < (3, 12):
        errors.append("Cần Python 3.12 trở lên.")
    for name in ("ffmpeg", "ffprobe"):
        binary = shutil.which(name)
        if binary is None:
            errors.append(f"Thiếu {name}. Cài FFmpeg có ffmpeg và ffprobe, rồi thêm thư mục bin vào PATH.")
            continue
        try:
            result = subprocess.run([binary, "-version"], capture_output=True, check=True)
            print(result.stdout.decode("utf-8", errors="replace").splitlines()[0])
            if name == "ffmpeg":
                encoders = subprocess.run(
                    [binary, "-hide_banner", "-encoders"], capture_output=True, check=True
                )
                if b"libx264" not in encoders.stdout.split():
                    errors.append("FFmpeg thiếu encoder libx264. Cài bản FFmpeg có libx264.")
        except (OSError, subprocess.CalledProcessError, IndexError):
            errors.append(f"Không chạy được {binary}. Kiểm tra lại bản cài và PATH.")
    font = None
    try:
        import skia

        from . import scene

        print(f"skia-python {skia.__version__}")
        resolved_font = font_path if font_path is not None else scene.DEFAULT_FONT
        font = scene.load_font(resolved_font)
        print(f"Font tiếng Việt OK: {resolved_font} ({scene.TITLE})")
    except (ImportError, OSError) as error:
        errors.append(f"Không nạp được Skia: {error}. Chạy python -m pip install -r requirements.txt.")
    except (ValueError, RuntimeError) as error:
        errors.append(str(error))
    if errors:
        raise RuntimeError("\n".join(errors))
    return font


def render_demo(output, font):
    import skia

    from . import scene

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    surface = skia.Surface(scene.WIDTH, scene.HEIGHT)
    with TemporaryDirectory(prefix=".render-", dir=output.parent) as temp:
        draft = Path(temp) / "demo.mp4"
        log_path = Path(temp) / "ffmpeg.log"
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "rawvideo", "-pixel_format", "bgra",
            "-video_size", f"{scene.WIDTH}x{scene.HEIGHT}",
            "-framerate", str(scene.FPS), "-i", "pipe:0",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(draft),
        ]
        with log_path.open("wb") as log, subprocess.Popen(
            command, stdin=subprocess.PIPE, stderr=log
        ) as encoder:
            pipe_closed_early = False
            try:
                with encoder.stdin as pipe:
                    for frame in range(scene.FRAME_COUNT):
                        scene.draw_scene(surface.getCanvas(), frame, font)
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


def main():
    parser = argparse.ArgumentParser(description="Stickman 2D CLI")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Kiểm tra môi trường")
    render = commands.add_parser("render-demo", help="Xuất cảnh mẫu 5 giây")
    for command in (doctor, render):
        command.add_argument("--font", type=Path, help="Đường dẫn font TTF/OTF thay thế")
    render.add_argument("--output", type=Path, default=Path("out/demo.mp4"))
    args = parser.parse_args()
    try:
        font = check_tools(args.font)
        if args.command == "render-demo":
            render_demo(args.output, font)
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Đã dừng render.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
