"""Prepare a project and pass it to the shared CLI renderer."""

import json
from argparse import Namespace
from pathlib import Path

import skia

from stickman.pipeline import make_timeline, render
from stickman.scene import DEFAULT_FONT, draw_scene, load_font

from .script import validate
from .voice import synthesize


def preview(scene):
    font = load_font(DEFAULT_FONT)
    surface = skia.Surface(640, 360)
    canvas = surface.getCanvas()
    canvas.scale(0.5, 0.5)
    draw_scene(canvas, 70, font, scene["label"], 0, scene["pose"], scene["theme"])
    return bytes(surface.makeImageSnapshot().encodeToData(skia.kPNG, 100))


def save_audio(data, work, stem):
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        suffix = ".wav"
    elif data.startswith(b"ID3") or (len(data) > 2 and data[0] == 255 and data[1] & 224 == 224):
        suffix = ".mp3"
    elif data[4:8] == b"ftyp":
        suffix = ".m4a"
    else:
        raise ValueError("Tệp âm thanh cần đúng định dạng WAV, MP3 hoặc M4A.")
    path = work / (stem + suffix)
    path.write_bytes(data)
    return path


def export(rows, voice, recording, music, options, work, progress):
    scenes = validate(rows)
    script = work / "input.txt"
    script.write_text("\n".join(row["dialogue"] for row in scenes), encoding="utf-8")
    story = None
    srt = None
    if recording:
        voice_path = save_audio(recording, work, "recording")
    else:
        voice_path, shots, srt = synthesize(scenes, voice, work, progress)
        story = work / "story.json"
        story.write_text(json.dumps({"schema_version": 1, "shots": shots}, ensure_ascii=False), encoding="utf-8")
    music_path = save_audio(music, work, "music") if music else None
    args = Namespace(script=script, voice=voice_path, story=story, srt=srt,
                     output=work / "out", font=None, music=music_path, **options)
    timeline = make_timeline(args)
    if timeline["audio_ms"] > 180000:
        raise ValueError("Web Studio hỗ trợ video tối đa 3 phút mỗi lượt.")
    if srt:
        args.timing_source = "edge_tts"
    if recording:
        story = work / "story.json"
        shots = [dict(end_ms=shot["end_ms"], event_ms=shot["event_ms"],
                      **{key: row[key] for key in ("label", "pose", "theme")})
                 for shot, row in zip(timeline["shots"], scenes)]
        story.write_text(json.dumps({"schema_version": 1, "shots": shots}, ensure_ascii=False), encoding="utf-8")
        # Keep the estimated alignment provenance while preserving edited scene options.
        args.story = story
        args.timing_source = "estimated"
    progress(len(scenes), len(scenes))
    render(args, load_font(DEFAULT_FONT))
    return {name: (args.output / name).read_bytes() for name in ("final.mp4", "master.srt", "qc.json")}
