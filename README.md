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
## Usage
```bash
python video_to_scorm.py --video path/to/video.mp4 --output output_dir
```

Optional arguments:
- `--subtitles path/to/subtitles.srt` – use an existing subtitle file.
- `--video-url URL` – use a remote video instead of a local file (requires subtitles).
- `--title "Lesson Title"` – override the default lesson title.
- `--interval SECONDS` – interval in seconds for auto-generated sections (default 300).

The output directory will contain the SCORM package plus the `.srt`, `.md`, and
`.sections` files.
