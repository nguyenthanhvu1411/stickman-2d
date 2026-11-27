"""Synthesize each narration scene and convert Edge word boundaries to cues."""

import json
import wave

import edge_tts

from stickman.pipeline import media, timestamp

RATE = 48000
VOICES = {
    "vi-VN-HoaiMyNeural": "Tiếng Việt · Hoài My",
    "vi-VN-NamMinhNeural": "Tiếng Việt · Nam Minh",
    "en-US-JennyNeural": "English · Jenny",
    "en-US-GuyNeural": "English · Guy",
}


def scene_cues(words, start, end, fallback):
    groups = []
    current = []
    for word in words:
        text = word["text"].strip()
        lower = start + round(word["offset"] / 10000)
        upper = min(end, lower + round(word["duration"] / 10000))
        if not text or upper <= lower or lower >= end:
            continue
        if current and (len(current) >= 7 or len(" ".join(x[2] for x in current)) + len(text) > 55):
            groups.append(current)
            current = []
        current.append((lower, upper, text))
    if current:
        groups.append(current)
    if not groups:
        return [(start, end, fallback)]
    return [(group[0][0], max(word[1] for word in group), " ".join(word[2] for word in group))
            for group in groups]


def synthesize(scenes, voice, work, progress):
    samples = 0
    shots = []
    cues = []
    narration = work / "voice.wav"
    with wave.open(str(narration), "wb") as combined:
        combined.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        for index, scene in enumerate(scenes):
            progress(index, len(scenes))
            mp3, metadata, pcm = (work / f"scene{index}.{ext}" for ext in ("mp3", "jsonl", "wav"))
            try:
                edge_tts.Communicate(scene["dialogue"], voice, boundary="WordBoundary",
                                     connect_timeout=10, receive_timeout=30).save_sync(str(mp3), str(metadata))
            except Exception:
                raise RuntimeError(f"Edge TTS không tạo được giọng cho cảnh {index + 1}. "
                                   "Thử lại hoặc tải lên giọng thu.") from None
            media("ffmpeg", "-v", "error", "-nostdin", "-i", str(mp3),
                  "-af", "apad=pad_dur=0.22", "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le", str(pcm))
            start = round(samples * 1000 / RATE)
            with wave.open(str(pcm), "rb") as clip:
                count = clip.getnframes()
                combined.writeframes(clip.readframes(count))
                samples += count
            end = round(samples * 1000 / RATE)
            if end > 180000:
                raise ValueError("Web Studio hỗ trợ video tối đa 3 phút mỗi lượt.")
            words = [json.loads(line) for line in metadata.read_text(encoding="utf-8").splitlines()]
            captions = scene_cues(words, start, end, scene["dialogue"])
            cues.extend(captions)
            shots.append(dict(end_ms=end, event_ms=captions[0][0], label=scene["label"],
                              pose=scene["pose"], theme=scene["theme"]))
    srt = work / "edge.srt"
    srt.write_text("\n\n".join(f"{i}\n{timestamp(start)} --> {timestamp(end)}\n{text}"
                               for i, (start, end, text) in enumerate(cues, 1)) + "\n", encoding="utf-8")
    return narration, shots, srt
