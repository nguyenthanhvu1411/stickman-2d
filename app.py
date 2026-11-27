"""Streamlit entry point for Stickman Studio."""

import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "video-cli"))

from studio.project import export, preview
from studio.script import POSES, THEMES, from_text, from_topic, validate
from studio.voice import VOICES

st.set_page_config(page_title="Stickman Studio", page_icon="🎬", layout="wide")
st.title("Stickman Studio")
st.caption("Tạo kịch bản, chỉnh cảnh và xuất video Stickman 2D.")

with st.sidebar:
    st.header("Thiết lập video")
    voice = st.selectbox("Giọng đọc", list(VOICES), format_func=VOICES.get)
    orientation = st.radio("Tỷ lệ khung", ("16:9 · Ngang", "9:16 · Dọc"))
    resolution = st.selectbox("Chất lượng", (720, 1080), format_func=lambda value: f"{value}p")
    subtitles = st.toggle("Đốt phụ đề vào video", value=True)
    effects = st.toggle("Phát hiệu ứng âm thanh", value=True)
    recording = st.file_uploader("Hoặc dùng giọng thu của bạn", type=["wav", "mp3", "m4a"])
    music = st.file_uploader("Nhạc nền", type=["wav", "mp3", "m4a"])

tab_topic, tab_script = st.tabs(["Tạo bằng AI", "Dán kịch bản"])
with tab_topic:
    with st.form("topic"):
        topic = st.text_area("Chủ đề", max_chars=2500, placeholder="Ví dụ: Vì sao nên ngủ đủ giấc?")
        left, right = st.columns(2)
        language = left.selectbox("Ngôn ngữ kịch bản", ("tiếng Việt", "English"))
        count = right.number_input("Số cảnh", 1, 12, 4)
        key = st.text_input("OpenAI API key", type="password", help="Có thể cấu hình OPENAI_API_KEY trên server.")
        model = st.text_input("Model OpenAI", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        generate = st.form_submit_button("Tạo kịch bản", type="primary")
    if generate:
        try:
            token = key.strip() or os.getenv("OPENAI_API_KEY", "").strip()
            if not topic.strip() or not token or not model.strip():
                raise ValueError("Hãy nhập chủ đề, model và OpenAI API key.")
            with st.spinner("Đang viết kịch bản…"):
                st.session_state.scenes = from_topic(topic.strip(), language, token, model.strip(), int(count))
            st.session_state.editor_version = st.session_state.get("editor_version", 0) + 1
            st.session_state.pop("files", None)
        except (ValueError, RuntimeError) as error:
            st.error(str(error))

with tab_script:
    with st.form("script"):
        raw = st.text_area("Mỗi dòng là lời thoại của một cảnh", max_chars=12000,
                           placeholder="Mọi câu chuyện bắt đầu từ một ý tưởng.\nHãy thử kể ý tưởng của bạn.")
        load = st.form_submit_button("Tạo danh sách cảnh")
    if load:
        try:
            st.session_state.scenes = from_text(raw)
            st.session_state.editor_version = st.session_state.get("editor_version", 0) + 1
            st.session_state.pop("files", None)
        except ValueError as error:
            st.error(str(error))

if "scenes" in st.session_state:
    st.header("Chỉnh cảnh")
    rows = st.data_editor(
        st.session_state.scenes, hide_index=True, num_rows="dynamic", width="stretch",
        key=f"scene-editor-{st.session_state.editor_version}",
        column_config={
            "dialogue": st.column_config.TextColumn("Lời thoại", required=True, width="large"),
            "label": st.column_config.TextColumn("Chữ trên hình"),
            "pose": st.column_config.SelectboxColumn("Tư thế", options=list(POSES), required=True, default="point"),
            "theme": st.column_config.SelectboxColumn("Bối cảnh", options=list(THEMES), required=True, default="whiteboard"),
        },
    )
    if rows:
        selected = st.selectbox("Xem trước cảnh", range(len(rows)), format_func=lambda index: f"Cảnh {index + 1}")
        try:
            st.image(preview(validate([rows[selected]])[0]), width=480)
        except (ValueError, RuntimeError) as error:
            st.warning(str(error))
    if st.button("Render MP4", type="primary"):
        st.session_state.pop("files", None)
        bar = st.progress(0, text="Đang chuẩn bị…")

        def progress(index, total):
            message = f"Đang tạo giọng cảnh {index + 1}/{total}…" if index < total else "Đang render và ghép video…"
            bar.progress(min(70, index * 70 // total), text=message)

        try:
            if not all(shutil.which(name) for name in ("ffmpeg", "ffprobe")):
                raise RuntimeError("Máy chủ cần FFmpeg và ffprobe. Xem packages.txt hoặc README.")
            if any(file and file.size > 25 * 1024 * 1024 for file in (recording, music)):
                raise ValueError("Mỗi file tải lên tối đa 25 MB.")
            with TemporaryDirectory(prefix="stickman-studio-") as directory:
                st.session_state.files = export(
                    rows, voice, recording.getvalue() if recording else None, music.getvalue() if music else None,
                    dict(resolution=resolution, portrait=orientation.startswith("9:16"),
                         no_sfx=not effects, no_subtitles=not subtitles),
                    Path(directory), progress,
                )
            bar.progress(100, text="Video đã sẵn sàng.")
        except (OSError, ValueError, RuntimeError) as error:
            bar.empty()
            st.error(str(error))

if "files" in st.session_state:
    st.subheader("Video đã xuất")
    files = st.session_state.files
    st.video(files["final.mp4"])
    left, middle, right = st.columns(3)
    left.download_button("Tải MP4", files["final.mp4"], "final.mp4", "video/mp4")
    middle.download_button("Tải SRT", files["master.srt"], "master.srt", "application/x-subrip")
    right.download_button("Tải báo cáo QC", files["qc.json"], "qc.json", "application/json")
