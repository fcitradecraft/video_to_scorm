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
