"""Command-line entry point for environment checks and the render demo."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


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


def main():
    parser = argparse.ArgumentParser(description="Stickman 2D CLI")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Kiểm tra môi trường")
    render = commands.add_parser("render-demo", help="Xuất cảnh mẫu 5 giây")
    for command in (doctor, render):
        command.add_argument("--font", type=Path, help="Đường dẫn font TTF/OTF thay thế")
    render.add_argument("--output", type=Path, default=Path("out/demo.mp4"))
    from .pipeline import add_commands

    add_commands(commands)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            args.run(args, None)
        else:
            font = check_tools(args.font)
            if args.command == "render-demo":
                from . import scene
                from .encoder import encode

                encode(args.output, scene.WIDTH, scene.HEIGHT, scene.FRAME_COUNT,
                       lambda canvas, frame: scene.draw_scene(canvas, frame, font))
                print(f"Đã xuất {args.output.resolve()}")
            elif args.command != "doctor":
                args.run(args, font)
    except (OSError, RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Đã dừng render.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
