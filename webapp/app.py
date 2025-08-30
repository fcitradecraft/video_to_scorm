from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from pathlib import Path
import os
from io import StringIO
import contextlib

from video_to_scorm import (
    prepare_assets,
    prepare_quiz,
    build_html,
    package_scorm,
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
app = Flask(__name__, template_folder=str(PROJECT_ROOT / "templates"))
app.secret_key = "dev-secret-key"

UPLOAD_FOLDER = PROJECT_ROOT / "uploads"
OUTPUTS_FOLDER = PROJECT_ROOT / "outputs"
ALLOWED_EXTENSIONS = {"mp4"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_with_logs(func, *args, **kwargs):
    buf_out, buf_err = StringIO(), StringIO()
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            result = func(*args, **kwargs)
        output = buf_out.getvalue() + buf_err.getvalue()
        if result is not None:
            output += f"\n{result}"
        return output, True, result
    except Exception as e:  # pragma: no cover - runtime errors reported to user
        output = buf_out.getvalue() + buf_err.getvalue() + f"\nError: {e}"
        return output, False, e


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("video")
        if not file or file.filename == "":
            flash("No file selected.")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file type. Only MP4 is allowed.")
            return redirect(request.url)

        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        if file_length > MAX_FILE_SIZE:
            flash("File too large. Maximum size is 50 MB.")
            return redirect(request.url)

        UPLOAD_FOLDER.mkdir(exist_ok=True)
        filename = secure_filename(file.filename)
        save_path = UPLOAD_FOLDER / filename
        file.save(save_path)

        OUTPUTS_FOLDER.mkdir(exist_ok=True)
        base = Path(filename).stem
        workdir = OUTPUTS_FOLDER / base
        workdir.mkdir(parents=True, exist_ok=True)
        session["working_dir"] = str(workdir)
        session["video_path"] = str(save_path)

        # Reset pipeline state on new upload
        session.pop("prepared", None)
        session.pop("built", None)
        session.pop("last_log", None)
        session.pop("title", None)
        session.pop("zip_path", None)

        flash("File uploaded successfully.")
        return redirect(url_for("index"))
    return render_template(
        "index.html",
        logs=session.get("last_log"),
        video_uploaded="video_path" in session,
        prepared=session.get("prepared"),
        built=session.get("built"),
        title=session.get("title", "SCORM Lesson"),
        zip_path=session.get("zip_path"),
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(_):
    flash("File too large. Maximum size is 50 MB.")
    return redirect(url_for("index"))


@app.route("/prepare", methods=["POST"])
def prepare():
    video_path = session.get("video_path")
    output_dir = session.get("working_dir")
    if not video_path or not output_dir:
        flash("Upload a video first.")
        return redirect(url_for("index"))
    interval = request.form.get("interval", type=int, default=300)
    log, ok, err = run_with_logs(prepare_assets, video_path, output_dir, interval)
    session["last_log"] = log
    if ok:
        session["prepared"] = True
        flash("Preparation complete.")
    else:
        if isinstance(err, RuntimeError) and "Whisper" in str(err):
            flash("Preparation failed: Whisper dependency missing.")
        else:
            flash("Preparation failed: transcription error.")
    return redirect(url_for("index"))


@app.route("/quiz", methods=["POST"])
def quiz():
    if not session.get("prepared"):
        flash("Run prepare first.")
        return redirect(url_for("index"))
    output_dir = session.get("working_dir")
    num_questions = request.form.get("num_questions", type=int, default=5)
    log, ok, err = run_with_logs(prepare_quiz, output_dir, num_questions)
    session["last_log"] = log
    if ok:
        flash("Quiz generation complete.")
    else:
        flash(f"Quiz generation failed: {err}")
    return redirect(url_for("index"))


@app.route("/build", methods=["POST"])
def build():
    if not session.get("prepared"):
        flash("Run prepare first.")
        return redirect(url_for("index"))
    output_dir = session.get("working_dir")
    video_url = request.form.get("video_url")
    title = request.form.get("title") or "SCORM Lesson"
    log, ok, err = run_with_logs(build_html, video_url, output_dir, title)
    session["last_log"] = log
    if ok:
        session["built"] = True
        session["title"] = title
        flash("Build complete.")
    else:
        flash(f"Build failed: {err}")
    return redirect(url_for("index"))


@app.route("/package", methods=["POST"])
def package():
    if not session.get("built"):
        flash("Run build first.")
        return redirect(url_for("index"))
    output_dir = session.get("working_dir")
    title = request.form.get("title") or session.get("title") or "SCORM Lesson"
    log, ok, result = run_with_logs(package_scorm, output_dir, title)
    session["last_log"] = log
    if ok:
        session["zip_path"] = str(result)
        flash("Package created.")
    else:
        flash(f"Packaging failed: {result}")
    return redirect(url_for("index"))


@app.route("/download")
def download():
    zip_path = session.get("zip_path")
    if not zip_path:
        flash("No package available.")
        return redirect(url_for("index"))
    path = Path(zip_path)
    if not path.exists():
        flash("Package not found.")
        return redirect(url_for("index"))
    return send_from_directory(path.parent, path.name, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
