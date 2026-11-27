"""Convert a pasted script or topic into editable scene records."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

POSES = ("point", "idle")
THEMES = ("whiteboard", "mint")
MAX_SCENES = 24
MAX_LINE = 500
SCENE_SCHEMA = {
    "type": "object",
    "properties": {
        "dialogue": {"type": "string"},
        "label": {"type": "string"},
        "pose": {"type": "string", "enum": list(POSES)},
        "theme": {"type": "string", "enum": list(THEMES)},
    },
    "required": ["dialogue", "label", "pose", "theme"],
    "additionalProperties": False,
}


def validate(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_SCENES:
        raise ValueError(f"Cần từ 1 đến {MAX_SCENES} cảnh.")
    scenes = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Cảnh {index} không hợp lệ.")
        dialogue = " ".join(str(row.get("dialogue") or "").split())
        label = " ".join(str(row.get("label") or "").split())
        pose, theme = row.get("pose"), row.get("theme")
        if not dialogue or dialogue.startswith("#") or len(dialogue) > MAX_LINE or len(label) > 80:
            raise ValueError(f"Cảnh {index}: lời thoại cần 1–{MAX_LINE} ký tự, nhãn tối đa 80 ký tự.")
        if pose not in POSES or theme not in THEMES:
            raise ValueError(f"Cảnh {index}: chọn tư thế và bối cảnh hợp lệ.")
        scenes.append(dict(dialogue=dialogue, label=label, pose=pose, theme=theme))
    return scenes


def from_text(text):
    rows = [dict(dialogue=line, label=" ".join(line.split()[:4])[:80], pose="point", theme="whiteboard")
            for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return validate(rows)


def from_topic(topic, language, key, model, count):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": (
                "Write original narration for a short animated video. Use no invented statistics. "
                f"Write in {language}, exactly {count} scenes, one concise spoken sentence per scene. "
                "Keep each board label under 60 characters. Alternate poses and themes where appropriate."
            )},
            {"role": "user", "content": topic},
        ],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "stickman_story", "strict": True, "schema": {
                "type": "object",
                "properties": {"scenes": {"type": "array", "items": SCENE_SCHEMA}},
                "required": ["scenes"], "additionalProperties": False,
            },
        }},
    }
    request = Request("https://api.openai.com/v1/chat/completions", data=json.dumps(payload).encode(),
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=75) as response:
            body = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"OpenAI trả mã {error.code}. Kiểm tra API key, model và hạn mức.") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Không kết nối được OpenAI. Thử lại hoặc dán kịch bản có sẵn.") from None
    try:
        rows = json.loads(body["choices"][0]["message"]["content"])["scenes"]
        if not isinstance(rows, list) or len(rows) != count:
            raise ValueError
        return validate(rows)
    except (KeyError, IndexError, TypeError, ValueError):
        raise RuntimeError("OpenAI chưa trả đủ cảnh hợp lệ. Hãy thử lại.") from None
