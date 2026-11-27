"""A fixed, frame-driven whiteboard scene."""

import math
from pathlib import Path
from unicodedata import normalize

import skia

WIDTH, HEIGHT = 1280, 720
FPS = 30
FRAME_COUNT = 5 * FPS
TITLE = normalize("NFC", "Ý tưởng đầu tiên")
DEFAULT_FONT = Path(__file__).with_name("assets") / "NotoSans-Bold.ttf"

INK = 0xFF18161B
TEAL = 0xFF087C74
WHITE = 0xFFFFFFFF


def load_font(path):
    if not path.is_file():
        raise ValueError(f"Không tìm thấy font: {path}. Khôi phục font kèm theo hoặc dùng --font FILE.")
    face = skia.Typeface.MakeFromFile(str(path))
    if face is None:
        raise ValueError(f"Không đọc được font {path}. Dùng --font với tệp TTF/OTF hợp lệ.")
    font = skia.Font(face, 61)
    missing = sorted({char for char, glyph in zip(TITLE, font.textToGlyphs(TITLE)) if glyph == 0})
    if missing:
        raise ValueError(f"Font thiếu ký tự {''.join(missing)}. Dùng --font với font hỗ trợ tiếng Việt.")
    return font


def paint(color):
    return skia.Paint(Color=color, AntiAlias=True)


def rounded(canvas, bounds, radius, color):
    canvas.drawRoundRect(skia.Rect.MakeLTRB(*bounds), radius, radius, paint(color))


def stroke(canvas, points, color=INK, width=13):
    path = skia.Path()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    line = paint(color)
    line.setStyle(skia.Paint.kStroke_Style)
    line.setStrokeWidth(width)
    line.setStrokeCap(skia.Paint.kRound_Cap)
    line.setStrokeJoin(skia.Paint.kRound_Join)
    canvas.drawPath(path, line)


def draw_scene(canvas, frame, title_font):
    time = frame / FPS
    canvas.clear(0xFFF5F0E7)
    canvas.drawRect(skia.Rect.MakeLTRB(0, 551, WIDTH, HEIGHT), paint(0xFFEAE2D5))
    stroke(canvas, [(0, 551), (WIDTH, 551)], 0xFFDCD2C3, 2)
    rounded(canvas, (465, 143, 1161, 513), 26, 0xFFD9D0C1)
    rounded(canvas, (453, 128, 1149, 498), 26, INK)
    rounded(canvas, (461, 136, 1141, 490), 19, WHITE)
    rounded(canvas, (726, 480, 868, 504), 8, INK)
    rounded(canvas, (748, 475, 792, 483), 4, TEAL)
    rounded(canvas, (805, 473, 846, 483), 4, 0xFFE3AB42)

    canvas.drawOval(skia.Rect.MakeLTRB(170, 544, 406, 585), paint(0xFFD6CCBC))
    bob = 5 * math.sin(time * math.tau / 2.1)
    reach = min(max((time - 0.25) / 0.85, 0), 1)
    reach = reach * reach * (3 - 2 * reach)
    shoulder = (280, 350 + bob)
    stroke(canvas, [(280, 464 + bob), (230, 523), (206, 557)])
    stroke(canvas, [(280, 464 + bob), (327, 524), (357, 557)])
    stroke(canvas, [shoulder, (228, 387 + bob), (218, 423 + bob)])
    stroke(canvas, [shoulder, (341, 384 - 51 * reach + bob),
                    (364 + 96 * reach, 412 - 102 * reach + bob)])
    stroke(canvas, [(280, 322 + bob), (280, 464 + bob)], width=17)
    rounded(canvas, (257, 326 + bob, 303, 349 + bob), 9, TEAL)

    canvas.drawCircle(280, 264 + bob, 61, paint(INK))
    canvas.drawCircle(280, 264 + bob, 52, paint(WHITE))
    if frame in (65, 66, 117, 118):
        for x in (272, 303):
            stroke(canvas, [(x - 5, 257 + bob), (x + 5, 257 + bob)], width=4)
    else:
        for x in (272, 303):
            canvas.drawCircle(x, 257 + bob, 4.5, paint(INK))
    stroke(canvas, [(278, 280 + bob), (286, 286 + bob), (297, 280 + bob)], width=4)

    if time >= 1.2:
        progress = min((time - 1.2) / 0.55, 1)
        remaining = progress - 1
        scale = 0.55 + 0.45 * (1 + 2.8 * remaining**3 + 1.8 * remaining**2)
        canvas.save()
        canvas.translate(800, 302)
        canvas.scale(scale, scale)
        rounded(canvas, (-277, -70, 277, 70), 24, 0xFFE5F5F1)
        canvas.drawString(TITLE, -title_font.measureText(TITLE) / 2, 18, title_font, paint(INK))
        canvas.restore()
        rounded(canvas, (730, 399, 870, 407), 4, TEAL)
        for start, end in [((545, 213), (530, 195)), ((1057, 213), (1073, 195))]:
            stroke(canvas, [start, end], 0xFFD89B33, 6)
