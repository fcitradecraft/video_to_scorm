# video_to_scorm

Generate a simple SCORM package from a video and accompanying subtitles.

## Features
- Creates an HTML video player packaged as a SCORM 1.2 module.
- Accepts either a local video file or an external video URL.
- Generates a Markdown transcript alongside any supplied subtitles.
- When a local video lacks subtitles, automatically transcribes it with
  [Whisper](https://github.com/openai/whisper) and emits both `.srt` and
  Markdown transcript files.
- Emits a companion `.sections` file with generic section titles based on a
  configurable interval.

## Usage
```bash
python video_to_scorm.py --video path/to/video.mp4 --output output_dir
```

Optional arguments:
- `--subtitles path/to/subtitles.srt` – use an existing subtitle file.
- `--video-url URL` – use a remote video instead of a local file (requires subtitles).
- `--title "Lesson Title"` – override the default lesson title.
- `--interval SECONDS` – interval in seconds for auto-generated sections (default 300).

The output directory will contain the SCORM package and any generated transcripts.
