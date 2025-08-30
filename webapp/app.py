from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
app = Flask(__name__, template_folder=str(PROJECT_ROOT / "templates"))
app.secret_key = "dev-secret-key"

UPLOAD_FOLDER = PROJECT_ROOT / "uploads"
ALLOWED_EXTENSIONS = {"mp4"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
        flash("File uploaded successfully.")
        return redirect(url_for("index"))
    return render_template("index.html")


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(_):
    flash("File too large. Maximum size is 50 MB.")
    return redirect(url_for("index"))


if __name__ == "__main__":
=======
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    """Render landing page with forms/buttons."""
    return render_template('index.html')


@app.route('/prepare', methods=['GET', 'POST'])
def prepare():
    """Endpoint for preparing content."""
    return 'Prepare endpoint'


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    """Endpoint for quiz generation."""
    return 'Quiz endpoint'


@app.route('/build', methods=['GET', 'POST'])
def build():
    """Endpoint for building SCORM package."""
    return 'Build endpoint'


@app.route('/package', methods=['GET', 'POST'])
def package():
    """Endpoint for packaging the final output."""
    return 'Package endpoint'


if __name__ == '__main__':
    app.run(debug=True)
