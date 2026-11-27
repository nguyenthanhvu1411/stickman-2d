"""Build and render a local narration-driven storyboard."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import textwrap
import unicodedata
from pathlib import Path
from tempfile import TemporaryDirectory

FPS = 30


def media(*command, cwd=None):
    result = subprocess.run(command, cwd=cwd, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"{command[0]} thất bại: {result.stderr.strip()}")
    return result.stdout


def probe(path):
    return json.loads(media("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)))


def frame_at(ms):
    return (ms * FPS + 500) // 1000


def script_lines(path):
    raw = unicodedata.normalize("NFC", path.read_text(encoding="utf-8-sig"))
    return [line.strip() for line in raw.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def make_timeline(args):
    audio = probe(args.voice)
    if not any(stream["codec_type"] == "audio" for stream in audio["streams"]):
        raise ValueError("File giọng đọc cần có track âm thanh.")
    try:
        duration = round(float(audio["format"]["duration"]) * 1000)
    except (KeyError, ValueError, OverflowError) as error:
        raise ValueError("Không xác định được thời lượng file giọng đọc.") from error
    lines = script_lines(args.script)
    if not lines:
        raise ValueError("Kịch bản cần ít nhất một dòng lời đọc.")
    if args.story:
        data = json.loads(args.story.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ValueError("story.json cần schema_version = 1.")
        shots = data.get("shots")
        source = getattr(args, "timing_source", "manual")
    else:
        lengths = [max(1, len(line.split())) for line in lines]
        total = sum(lengths)
        elapsed = 0
        shots = []
        for index, (line, length) in enumerate(zip(lines, lengths)):
            end = round((elapsed + length) * duration / total)
            start = round(elapsed * duration / total)
            elapsed += length
            shots.append(dict(end_ms=end, label=" ".join(line.split()[:5]),
                              event_ms=start + min(400, (end - start) // 2),
                              pose="point" if index % 2 == 0 else "idle",
                              theme="whiteboard" if index % 2 == 0 else "mint"))
        source = "estimated"
        print("Cảnh báo: mốc tự chia theo số từ. Dùng --story để nhập mốc đã căn.")
    if not isinstance(shots, list) or len(shots) != len(lines):
        raise ValueError("story.json cần đúng một cảnh cho mỗi dòng lời đọc.")
    timeline = []
    start = 0
    for index, (shot, line) in enumerate(zip(shots, lines), start=1):
        if not isinstance(shot, dict):
            raise ValueError(f"Cảnh {index} phải là object.")
        end = shot.get("end_ms")
        if type(end) is not int or end > duration or frame_at(end) - frame_at(start) < 6:
            raise ValueError(f"Cảnh {index}: end_ms phải tăng, không vượt giọng đọc và có ít nhất 6 frame.")
        label = shot.get("label", "")
        pose = shot.get("pose", "point")
        theme = shot.get("theme", "whiteboard")
        event = shot.get("event_ms", start)
        if not isinstance(label, str) or pose not in ("point", "idle") or theme not in ("whiteboard", "mint"):
            raise ValueError(f"Cảnh {index}: label, pose hoặc theme không hợp lệ.")
        if type(event) is not int or not start <= event < end:
            raise ValueError(f"Cảnh {index}: event_ms phải nằm trong cảnh.")
        if end - start > 10000:
            print(f"Cảnh báo: cảnh {index} dài hơn 10 giây.")
        timeline.append(dict(id=f"s{index:03}", start_ms=start, end_ms=end, text=line,
                             label=unicodedata.normalize("NFC", label), pose=pose, theme=theme, event_ms=event))
        start = end
    if start != duration:
        raise ValueError(f"Cảnh cuối phải kết thúc cùng giọng đọc ({duration} ms).")
    return dict(schema_version=1, timing_source=source, audio_ms=duration, shots=timeline)


def timestamp(ms):
    seconds, fraction = divmod(ms, 1000)
    minutes, second = divmod(seconds, 60)
    hour, minute = divmod(minutes, 60)
    return f"{hour:02}:{minute:02}:{second:02},{fraction:03}"


def subtitles(shots):
    cues = []
    for shot in shots:
        lines = textwrap.wrap(shot["text"], width=42)
        groups = [lines[i:i + 2] for i in range(0, len(lines), 2)]
        start, end = shot["start_ms"], shot["end_ms"]
        for i, group in enumerate(groups):
            lo = start + (end - start) * i // len(groups)
            hi = start + (end - start) * (i + 1) // len(groups)
            if hi <= lo:
                raise ValueError(f"{shot['id']}: phụ đề quá dài so với cảnh.")
            cues.append(f"{len(cues)+1}\n{timestamp(lo)} --> {timestamp(hi)}\n" + "\n".join(group))
    return "\n\n".join(cues) + "\n"


def draw_frame(canvas, shot, local_frame, font, scale, offset_y=0):
    from .scene import draw_scene

    canvas.save()
    canvas.translate(0, offset_y)
    canvas.scale(scale, scale)
    trigger = (frame_at(shot["event_ms"]) - frame_at(shot["start_ms"])) / FPS
    draw_scene(canvas, local_frame, font, shot["label"], trigger, shot["pose"], shot["theme"])
    canvas.restore()


def run_plan(args, font):
    timeline = make_timeline(args)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.command == "stills":
        import skia

        thumbnails = []

        for shot in timeline["shots"]:
            missing = sorted({char for char in shot["label"]
                              if char not in "\r\n\t" and font.unicharToGlyph(ord(char)) == 0})
            if missing:
                raise ValueError(f"{shot['id']}: font thiếu ký tự {''.join(missing)}.")
            surface = skia.Surface(640, 360)
            last_frame = frame_at(shot["end_ms"]) - frame_at(shot["start_ms"]) - 1
            frame = min(last_frame, frame_at(shot["event_ms"]) - frame_at(shot["start_ms"]) + FPS)
            draw_frame(surface.getCanvas(), shot, frame, font, 0.5)
            thumbnail = surface.makeImageSnapshot()
            thumbnail.save(str(args.output / f"{shot['id']}.png"), skia.kPNG)
            thumbnails.append(thumbnail)
            if len(thumbnails) == 12 or shot is timeline["shots"][-1]:
                page = (int(shot["id"][1:]) - 1) // 12 + 1
                sheet = skia.Surface(960, 180 * ((len(thumbnails) + 2) // 3))
                canvas = sheet.getCanvas()
                canvas.clear(skia.ColorWHITE)
                canvas.scale(0.5, 0.5)
                for index, image in enumerate(thumbnails):
                    canvas.drawImage(image, (index % 3) * 640, (index // 3) * 360)
                sheet.makeImageSnapshot().save(str(args.output / f"contact-{page:03}.png"), skia.kPNG)
                thumbnails.clear()
    (args.output / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã lập timeline {len(timeline['shots'])} cảnh: {args.output.resolve()}")


def render(args, font):
    from . import scene
    from .encoder import encode

    timeline = make_timeline(args)
    shots = timeline["shots"]
    width, height = (1280, 720) if args.resolution == 720 else (1920, 1080)
    if getattr(args, "portrait", False):
        width, height = height, width
    scale = width / scene.WIDTH
    offset_y = (height - scene.HEIGHT * scale) / 2
    args.output.mkdir(parents=True, exist_ok=True)
    cache = args.output / "shots_cache"
    cache.mkdir(exist_ok=True)
    font_path = args.font or scene.DEFAULT_FONT
    engine = (font_path.read_bytes() + Path(scene.__file__).read_bytes()
              + Path(__file__).read_bytes() + Path(encode.__code__.co_filename).read_bytes())
    prefix = hashlib.sha256(engine).hexdigest()
    clips = []
    for shot in shots:
        count = frame_at(shot["end_ms"]) - frame_at(shot["start_ms"])
        relative_event = frame_at(shot["event_ms"]) - frame_at(shot["start_ms"])
        payload = (prefix, width, height, count, relative_event, shot["label"], shot["pose"], shot["theme"])
        key = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
        clip = (cache / f"{key}.mp4").resolve()
        cached = False
        if clip.exists():
            try:
                streams = probe(clip)["streams"]
                if not streams or streams[0].get("nb_frames") != str(count):
                    raise ValueError
                cached = True
            except (RuntimeError, ValueError):
                pass
        if not cached:
            missing = sorted({char for char in shot["label"] if font.unicharToGlyph(ord(char)) == 0})
            if missing:
                raise ValueError(f"{shot['id']}: font thiếu ký tự {''.join(missing)}.")
            print(f"Render {shot['id']}")
            encode(clip, width, height, count,
                   lambda canvas, frame: draw_frame(canvas, shot, frame, font, scale, offset_y))
        else:
            print(f"Dùng cache {shot['id']}")
        clips.append(clip)
    finish(args, timeline, clips, font_path)


def normalize_audio(work):
    target = "loudnorm=I=-14:TP=-1.5:LRA=11"
    base = ["ffmpeg", "-nostdin", "-hide_banner", "-i", "mix.wav"]
    result = subprocess.run([*base, "-af", target + ":print_format=json", "-f", "null", "-"],
                            cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"Không đo được âm lượng: {result.stderr.strip()}")
    match = re.search(r"\{[^{}]+\}", result.stderr)
    if not match:
        raise RuntimeError("FFmpeg không trả dữ liệu đo loudnorm.")
    measured = json.loads(match[0])
    if measured["input_i"] == "-inf":
        return "mix.wav"
    settings = (f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
                f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
                f":offset={measured['target_offset']}:linear=true")
    media(*base, "-af", target + settings, "-ar", "48000", "-c:a", "pcm_f32le", "normalized.wav", cwd=work)
    return "normalized.wav"


def finish(args, timeline, clips, font_path):
    output = args.output.resolve()
    if any(path and path.resolve() == output / "final.mp4" for path in (args.voice, args.music)):
        raise ValueError("Giọng đọc/nhạc nền không được trùng đường dẫn final.mp4.")
    total = frame_at(timeline["shots"][-1]["end_ms"]) / FPS
    with TemporaryDirectory(prefix=".final-", dir=output) as directory:
        work = Path(directory)
        for index, clip in enumerate(clips):
            # Relative ASCII names keep FFmpeg's concat syntax portable.
            target = work / f"scene{index}.mp4"
            try:
                os.link(clip, target)
            except OSError:
                shutil.copyfile(clip, target)
        (work / "clips.txt").write_text("".join(f"file scene{i}.mp4\n" for i in range(len(clips))), encoding="ascii")
        provided_srt = getattr(args, "srt", None)
        if provided_srt:
            shutil.copyfile(provided_srt, work / "master.srt")
        else:
            (work / "master.srt").write_text(subtitles(timeline["shots"]), encoding="utf-8")
        command = ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-f", "concat", "-safe", "1",
                   "-i", "clips.txt", "-i", str(args.voice.resolve())]
        if args.music:
            command += ["-stream_loop", "-1", "-i", str(args.music.resolve())]
        graph = ["[1:a]aresample=48000,aformat=channel_layouts=stereo,apad[voice]"]
        tracks = ["[voice]"]
        if args.music:
            graph += ["[voice]asplit[dialogue][key]",
                      "[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.16[bed]",
                      "[bed][key]sidechaincompress=threshold=0.025:ratio=8:attack=15:release=250[music]"]
            tracks = ["[dialogue]", "[music]"]
        if not args.no_sfx:
            events = {frame_at(shot["event_ms"]) * 1600 for shot in timeline["shots"] if shot["label"]}
            # One finite source avoids opening a stream per scene.
            import array
            import math
            import wave

            with wave.open(str(work / "sfx.wav"), "wb") as sound:
                sound.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
                cursor = 0
                pop = array.array("h", (round(3900 * math.sin(math.tau * 740 * i / 48000)
                                                * math.sin(math.pi * i / 3600) ** 2)
                                        for i in range(3600)))
                for sample in sorted(events):
                    if sample >= cursor:
                        sound.writeframes(bytes((sample - cursor) * 2))
                        sound.writeframes(pop.tobytes())
                        cursor = sample + len(pop)
                sound.writeframes(bytes(max(1, round(total * 48000) - cursor) * 2))
            command += ["-i", "sfx.wav"]
            graph += [f"[{3 if args.music else 2}:a]aformat=channel_layouts=stereo[sfx]"]
            tracks.append("[sfx]")
        graph.append("".join(tracks) + f"amix=inputs={len(tracks)}:normalize=0,atrim=duration={total}[audio]")
        media(*command, "-filter_complex", ";".join(graph), "-map", "[audio]",
              "-c:a", "pcm_f32le", "mix.wav", cwd=work)
        normalized = normalize_audio(work)
        command = ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-f", "concat", "-safe", "1",
                   "-i", "clips.txt", "-i", normalized, "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac",
                   "-t", str(total), "-movflags", "+faststart"]
        if args.no_subtitles:
            command += ["-c:v", "copy"]
        else:
            shutil.copyfile(font_path, work / "captions.ttf")
            command += ["-vf", "subtitles=master.srt:fontsdir=.:force_style='FontName=Noto Sans,FontSize=20'",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p"]
        media(*command, "final.mp4", cwd=work)
        manifest = probe(work / "final.mp4")
        video, audio = ({s["codec_type"]: s for s in manifest["streams"]}.get(kind) for kind in ("video", "audio"))
        if (not video or video["codec_name"] != "h264" or video["r_frame_rate"] != "30/1"
                or abs(float(video["duration"]) - total) > 1 / FPS
                or not audio or audio["codec_name"] != "aac"):
            raise RuntimeError("Video không đạt kiểm tra codec, tốc độ khung hình hoặc thời lượng.")
        decode = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-v", "info", "-xerror",
                                 "-i", "final.mp4", "-af", "ebur128=peak=true", "-f", "null", "-"],
                                cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if decode.returncode:
            raise RuntimeError("FFmpeg không giải mã được video đầu ra.")
        summary = decode.stderr.rsplit("Summary:", 1)[-1].strip()
        loudness = re.search(r"\bI:\s*(-?[\d.]+) LUFS", summary)
        peak = re.search(r"\bPeak:\s*(-?[\d.]+) dBFS", summary)
        warnings = []
        if not loudness or abs(float(loudness[1]) + 14) > 1:
            warnings.append("Âm lượng đầu ra ngoài khoảng -14 ±1 LUFS.")
        if not peak or float(peak[1]) > -1:
            warnings.append("True peak chưa xác nhận đạt ≤ -1 dBTP.")
        for warning in warnings:
            print(f"Cảnh báo: {warning}")
        report = dict(duration_s=total, width=video["width"], height=video["height"],
                      fps=FPS, audio_measurement=summary, warnings=warnings, timing_source=timeline["timing_source"])
        (work / "qc.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (work / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
        for name in ("master.srt", "timeline.json", "qc.json", "final.mp4"):
            (work / name).replace(output / name)
    print(f"Đã xuất {output / 'final.mp4'}")


def add_commands(commands):
    for name, action in (("plan", run_plan), ("stills", run_plan),
                         ("render", render), ("resume", render)):
        parser = commands.add_parser(name)
        parser.set_defaults(run=action)
        parser.add_argument("script", type=Path, help="TXT UTF-8, mỗi cảnh một dòng lời đọc")
        parser.add_argument("--voice", required=True, type=Path)
        parser.add_argument("--story", type=Path)
        parser.add_argument("--output", default=Path("out"), type=Path)
        if name != "plan":
            parser.add_argument("--font", type=Path)
        if name in ("render", "resume"):
            parser.add_argument("--resolution", choices=(720, 1080), type=int, default=720)
            parser.add_argument("--portrait", action="store_true")
            parser.add_argument("--music", type=Path)
            parser.add_argument("--no-sfx", action="store_true")
            parser.add_argument("--no-subtitles", action="store_true")
