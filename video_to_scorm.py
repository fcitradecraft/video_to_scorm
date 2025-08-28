import os
import re
import json
import argparse
import zipfile
import shutil
from pathlib import Path
from datetime import timedelta

try:
    import whisper  # Optional; only needed if auto-transcribing
except ImportError:  # pragma: no cover - dependency may be missing
    whisper = None

TEMPLATE_PATH = Path(__file__).parent / "templates" / "player_template.html"
BRANDING_PATH = Path(__file__).parent / "templates" / "branding.css"

# Name of the auto-generated quiz file
QUIZ_JSON_NAME = "quiz.json"

# ----------------------------
# PARSE SRT
# ----------------------------
def parse_srt(file_path):
    """Parse .srt into structured transcript"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\n|\Z)"
    )
    matches = pattern.findall(content)

    return [
        {
            "index": int(m[0]),
            "start": m[1],
            "end": m[2],
            "start_seconds": time_to_seconds(m[1]),
            "text": re.sub(r"\s+", " ", m[3]).strip(),
        }
        for m in matches
    ]

# ----------------------------
# CONVERT TIME
# ----------------------------
def time_to_seconds(time_str):
    h, m, s_ms = time_str.split(":")
    s, ms = s_ms.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s)

# ----------------------------
# TIMESTAMP HELPERS
# ----------------------------
def seconds_to_timestamp(seconds):
    """Convert float seconds to SRT timestamp."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int(round((seconds - total_seconds) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


# ----------------------------
# TRANSCRIBE VIDEO
# ----------------------------
def transcribe_to_srt(video_path, srt_path):
    """Transcribe ``video_path`` using Whisper and save as ``srt_path``.

    Returns the transcript structure compatible with ``parse_srt``.
    """

    if whisper is None:  # pragma: no cover - optional dependency
        raise RuntimeError("Whisper is required for auto-transcription but is not installed")

    print("🎤 No .srt provided → transcribing video with Whisper...")
    model = whisper.load_model("base")
    result = model.transcribe(str(video_path))

    transcript = []
    lines = []
    for i, seg in enumerate(result.get("segments", []), start=1):
        start = seconds_to_timestamp(seg["start"])
        end = seconds_to_timestamp(seg["end"])
        text = seg.get("text", "").strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
        transcript.append({
            "index": i,
            "start": start,
            "end": end,
            "start_seconds": int(seg["start"]),
            "text": text,
        })

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📝 Saved auto-generated subtitles: {srt_path}")

    return transcript


# ----------------------------
# GENERATE MARKDOWN TRANSCRIPT
# ----------------------------
def generate_markdown(transcript, md_path):
    """Write ``transcript`` to ``md_path`` in a simple Markdown format."""

    with open(md_path, "w", encoding="utf-8") as f:
        for entry in transcript:
            f.write(f"- [{entry['start']}] {entry['text']}\n")
    return md_path

# ----------------------------
# LOAD CUSTOM SECTIONS
# ----------------------------
def load_sections(sections_path, transcript):
    """Load .sections file if it exists"""
    sections = []
    if not sections_path.exists():
        return None

    print(f"📄 Found custom .sections file: {sections_path.name}")

    with open(sections_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                ts, title = line.split("=", 1)
                ts = ts.strip()
                title = title.strip()
                start_seconds = time_to_seconds(ts)

                # Skip timestamps beyond transcript length
                if start_seconds > transcript[-1]["start_seconds"]:
                    print(f"⚠️ Skipping {ts} ({title}) → beyond transcript length")
                    continue

                sections.append({
                    "start": ts,
                    "start_seconds": start_seconds,
                    "title": title
                })

    # Ensure sorted order
    sections.sort(key=lambda x: x["start_seconds"])
    print(f"✅ Loaded {len(sections)} custom sections.")
    return sections

# ----------------------------
# GENERATE SECTIONS AUTOMATICALLY
# ----------------------------
def auto_generate_sections(transcript, interval):
    """Fallback: auto-generate sections based on interval"""
    sections = []
    last_time = 0
    for entry in transcript:
        if entry["start_seconds"] >= last_time:
            sections.append({
                "start": entry["start"],
                "start_seconds": entry["start_seconds"],
                "title": f"Section {len(sections) + 1}"
            })
            last_time += interval
    print(f"ℹ️ No .sections file found → auto-generated {len(sections)} sections.")
    return sections


# ----------------------------
# SAVE SECTIONS
# ----------------------------
def save_sections(sections, sections_path):
    """Persist ``sections`` to ``sections_path``."""

    with open(sections_path, "w", encoding="utf-8") as f:
        for sec in sections:
            f.write(f"{sec['start']} = {sec['title']}\n")
    print(f"📝 Saved auto-generated sections: {sections_path}")

# ----------------------------
# GENERATE HTML PLAYER
# ----------------------------
def generate_player_html(transcript, sections, title, output_dir, video_src, is_url):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    video_value = str(video_src) if is_url else video_src.name

    output_text = template
    output_text = output_text.replace("{{TRANSCRIPT_JSON}}", json.dumps(transcript))
    output_text = output_text.replace("{{SECTIONS_JSON}}", json.dumps(sections))
    output_text = output_text.replace("{{TITLE}}", title)
    output_text = output_text.replace("{{VIDEO}}", video_value)

    if not is_url:
        shutil.copy(video_src, output_dir / video_src.name)

    # Ensure branding stylesheet is available in the output folder
    shutil.copy(BRANDING_PATH, output_dir / BRANDING_PATH.name)

    output_html = output_dir / "index.html"
    with open(output_html, "w", encoding="utf-8") as out:
        out.write(output_text)
    return output_html


# ----------------------------
# QUIZ GENERATION
# ----------------------------
def generate_quiz_json(md_path, output_dir, limit=5):
    """Create a quiz JSON file from ``md_path`` transcript.

    The quiz contains a mixture of multiple choice and true/false questions
    derived from the transcript text. The resulting JSON file is saved in
    ``output_dir`` with the name defined by ``QUIZ_JSON_NAME``.
    """

    with open(md_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip().startswith("-")]

    questions = []
    for line in lines[:limit]:
        # Extract the text after the timestamp portion
        if "]" in line:
            text = line.split("]", 1)[1].strip()
        else:
            text = line[1:].strip()

        words = text.split()
        if len(words) > 5:
            # Multiple choice: blank out the third word
            idx = min(2, len(words) - 1)
            answer = words[idx]
            prompt_words = words.copy()
            prompt_words[idx] = "____"
            prompt = "Fill in the blank: " + " ".join(prompt_words)
            distractors = [w for w in words if w.lower() != answer.lower()]
            options = [answer]
            for d in distractors[:3]:
                if d not in options:
                    options.append(d)
            question = {
                "type": "multiple_choice",
                "prompt": prompt,
                "options": options,
                "answer": answer,
            }
        else:
            # True/False question
            question = {
                "type": "true_false",
                "prompt": f"True or False: {text}",
                "answer": True,
            }
        questions.append(question)

    quiz_data = {"questions": questions}
    quiz_path = output_dir / QUIZ_JSON_NAME
    with open(quiz_path, "w", encoding="utf-8") as f:
        json.dump(quiz_data, f, indent=2)
    return quiz_path

# ----------------------------
# GENERATE SCORM MANIFEST
# ----------------------------
def generate_manifest(title, output_dir, quiz_json=None):
    quiz_items = ""
    quiz_resources = ""
    if quiz_json:
        quiz_items = (
            "      <item identifier=\"QUIZ1\" identifierref=\"RESQ1\">\n"
            "        <title>Quiz</title>\n"
            "      </item>\n"
        )
        quiz_resources = (
            f"    <resource identifier=\"RESQ1\" type=\"webcontent\" adlcp:scormtype=\"asset\" href=\"{QUIZ_JSON_NAME}\">\n"
            f"      <file href=\"{QUIZ_JSON_NAME}\" />\n"
            "    </resource>\n"
        )

    manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{title.replace(' ', '_').upper()}_SCORM" version="1.0"
 xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
 xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2
 imscp_rootv1p1p2.xsd
 http://www.adlnet.org/xsd/adlcp_rootv1p2
 adlcp_rootv1p2.xsd">

  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="ORG1">
    <organization identifier="ORG1">
      <title>{title}</title>
      <item identifier="ITEM1" identifierref="RES1">
        <title>{title}</title>
      </item>
{quiz_items}    </organization>
  </organizations>
  <resources>
    <resource identifier="RES1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html" />
      <file href="{BRANDING_PATH.name}" />
    </resource>
{quiz_resources}  </resources>
</manifest>"""
    manifest_path = output_dir / "imsmanifest.xml"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest)
    return manifest_path

# ----------------------------
# CREATE SCORM PACKAGE
# ----------------------------
def create_scorm_package(output_dir, title):
    zip_path = output_dir / f"{title.replace(' ', '_')}_SCORM.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".zip"):
                    continue
                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(output_dir)
                zipf.write(abs_path, rel_path)
    return zip_path

# ----------------------------
# PREPARE AND PACKAGE HELPERS
# ----------------------------
def prepare_assets(video, output, interval=300, subtitles=None):
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    video_src = Path(video)

    if subtitles:
        srt_src = Path(subtitles)
        transcript = parse_srt(srt_src)
        srt_path = output_dir / srt_src.name
        if srt_src.resolve() != srt_path.resolve():
            shutil.copy(srt_src, srt_path)
    else:
        srt_path = output_dir / f"{video_src.stem}.srt"
        transcript = transcribe_to_srt(video_src, srt_path)

    md_path = srt_path.with_suffix(".md")
    generate_markdown(transcript, md_path)
    print(f"📄 Markdown transcript: {md_path}")

    sections = auto_generate_sections(transcript, interval)
    final_sections_path = output_dir / f"{output_dir.name}.sections"
    save_sections(sections, final_sections_path)
    print(f"📄 Sections file: {final_sections_path}")

    print("✅ Preparation complete. You may edit the Markdown file to add quiz questions before packaging.")


def prepare_quiz(input_dir, num_questions=5):
    """Generate ``quiz.json`` from the Markdown transcript in ``input_dir``."""

    output_dir = Path(input_dir)
    md_files = list(output_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError("No markdown transcript found in input directory")

    md_path = md_files[0]
    quiz_path = generate_quiz_json(md_path, output_dir, num_questions)
    print(f"📄 Quiz file: {quiz_path}")
    print("✅ Quiz generation complete. Proceed to the package stage to include it in the SCORM zip.")


def package_scorm(video_url, input_dir, title="SCORM Lesson"):
    output_dir = Path(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Locate necessary files
    srt_files = list(output_dir.glob("*.srt"))
    if not srt_files:
        raise FileNotFoundError("No .srt file found in input directory")
    srt_path = srt_files[0]
    transcript = parse_srt(srt_path)

    md_path = srt_path.with_suffix(".md")
    sections_path = output_dir / f"{output_dir.name}.sections"

    sections = load_sections(sections_path, transcript)
    if not sections:
        sections = auto_generate_sections(transcript, 300)
        save_sections(sections, sections_path)

    quiz_json = None
    quiz_path = output_dir / QUIZ_JSON_NAME
    if quiz_path.exists():
        quiz_json = quiz_path

    html_file = generate_player_html(transcript, sections, title, output_dir, video_url, True)
    manifest_file = generate_manifest(title, output_dir, quiz_json)
    zip_file = create_scorm_package(output_dir, title)

    print(f"\n✅ Generated SCORM player: {html_file}")
    print(f"✅ SCORM manifest: {manifest_file}")
    print(f"✅ SCORM package: {zip_file}")
    if quiz_json:
        print(f"ℹ️ Included quiz file: {quiz_json}")
    else:
        print("⚠️ No quiz.json found. Run the 'quiz' stage to generate one if desired.")

# ----------------------------
# MAIN ENTRYPOINT
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate SCORM lesson")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prep = subparsers.add_parser(
        "prepare", help="Generate subtitles, markdown, and sections from a local video"
    )
    prep.add_argument("--video", required=True, help="Path to local video file")
    prep.add_argument("--output", required=True, help="Output folder")
    prep.add_argument("--subtitles", help="Path to existing .srt file")
    prep.add_argument(
        "--interval", type=int, default=300, help="Auto-section interval in seconds"
    )
    quiz_cmd = subparsers.add_parser(
        "quiz", help="Generate quiz.json from the markdown transcript"
    )
    quiz_cmd.add_argument("--input", required=True, help="Folder with prepared assets")
    quiz_cmd.add_argument(
        "--num-questions", type=int, default=5, help="Number of questions to generate"
    )

    pack = subparsers.add_parser(
        "package", help="Create SCORM package using prepared assets and a video URL"
    )
    pack.add_argument("--video-url", required=True, help="External video URL")
    pack.add_argument("--input", required=True, help="Folder containing prepared assets")
    pack.add_argument("--title", default="SCORM Lesson", help="Lesson title")

    args = parser.parse_args()

    if args.command == "prepare":
        prepare_assets(args.video, args.output, args.interval, args.subtitles)
    elif args.command == "quiz":
        prepare_quiz(args.input, args.num_questions)
    elif args.command == "package":
        package_scorm(args.video_url, args.input, args.title)


if __name__ == "__main__":
    main()
