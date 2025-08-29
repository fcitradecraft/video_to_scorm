# video_to_scorm

Generate a simple SCORM package from a video and accompanying subtitles.

## Features
- Creates an HTML video player packaged as a SCORM 1.2 module.
- Accepts either a local video file or an external video URL.
- If a `.srt` subtitle file is provided, a Markdown transcript is generated.
- If no `.srt` is provided for a local video, the script transcribes the video
  using [Whisper](https://github.com/openai/whisper) and saves both `.srt` and
  Markdown transcripts.
- Emits a companion `.sections` file in the output directory (named after the
  output folder) with generic section titles based on a configurable interval.
- Optional third stage generates a quiz in `quiz.json` based on the markdown
  transcript. Questions are auto-invented as multiple choice or true/false.
## Usage
### Workflow

```bash
# Stage 1 – generate transcripts and sections
python video_to_scorm.py prepare --video path/to/video.mp4 --output output_dir

# Stage 2 – create quiz.json from the markdown transcript
python video_to_scorm.py quiz --input output_dir

# Stage 3 – render HTML player and manifest (you may edit these files afterwards)
python video_to_scorm.py build --video-url URL --input output_dir --title "Lesson Title"

# Stage 4 – zip everything into a SCORM package
python video_to_scorm.py package --input output_dir --title "Lesson Title"
```

The output directory will contain the `.srt`, `.md`, `.sections`, `quiz.json`,
`index.html`, and `imsmanifest.xml` files. The `build` stage produces the HTML
player and manifest so you can edit them before running `package`, which bundles
all assets into the final `*_SCORM.zip`.

> **Preview tip:** opening the generated HTML directly from disk may be blocked
> by browser security settings. To preview locally, run `python -m http.server`
> in the output directory and visit `http://localhost:8000/index.html` in your
> browser.
