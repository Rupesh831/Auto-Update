from flask import Flask, jsonify, send_from_directory, abort, render_template_string, request
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = {'exe'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_latest_tracker():
    """Auto-detect latest tracker_vX.X.exe."""
    tracker_files = []
    try:
        for f in os.listdir(UPLOAD_FOLDER):
            if f.endswith('.exe') and re.match(r'tracker_v\d+\.\d+\.exe', f, re.IGNORECASE):
                version_match = re.search(r'v(\d+\.\d+)', f)
                if version_match:
                    version = float(version_match.group(1))
                    tracker_files.append((f, version))
    except:
        pass
    if tracker_files:
        return max(tracker_files, key=lambda x: x[1])
    return None, 0.0

@app.route('/', methods=['GET', 'POST'])
def index():
    filename, version = get_latest_tracker()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template_string(HTML_TEMPLATE, filename=filename or 'None', 
                                        version=version, message="No file selected", files=[])
        file = request.files['file']
        if file.filename == '':
            return render_template_string(HTML_TEMPLATE, filename=filename or 'None', 
                                        version=version, message="No file selected", files=[])
        if file and allowed_file(file.filename):
            filename_secure = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename_secure))
            return render_template_string(HTML_TEMPLATE, filename=filename_secure, 
                                        version=version, message="✅ Uploaded successfully!", 
                                        files=[f for f in os.listdir('.') if f.endswith('.exe')])
    return render_template_string(HTML_TEMPLATE, filename=filename or 'None', version=version, 
                                message="", files=[f for f in os.listdir('.') if f.endswith('.exe')])

@app.route('/version')
def version():
    filename, version_num = get_latest_tracker()
    if filename:
        return jsonify({"version": version_num, "filename": filename, "update": True})
    return jsonify({"version": 0.0, "filename": "", "update": False})

@app.route('/download')
def download():
    filename, _ = get_latest_tracker()
    if filename and os.path.exists(filename):
        return send_from_directory('.', filename, as_attachment=True)
    abort(404)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Tracker Server</title>
<style>
body{font-family:Arial;max-width:800px;margin:50px auto;padding:20px;background:#f5f5f5;}
.card{background:white;padding:30px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);}
.version{color:#2196F3;font-size:28px;font-weight:bold;}
.upload-form{margin:20px 0;}
input[type=file]{padding:10px;margin:10px 0;}
button{padding:12px 24px;background:#4CAF50;color:white;border:none;border-radius:5px;cursor:pointer;font-size:16px;}
.files{list-style:none;padding:0;}
.files li{margin:10px 0;padding:15px;background:#e3f2fd;border-radius:5px;}
a{display:inline-block;padding:10px 20px;background:#2196F3;color:white;text-decoration:none;border-radius:5px;margin:5px;}
.message{color:#4CAF50;font-weight:bold;padding:10px;background:#e8f5e8;border-radius:5px;}
</style>
</head>
<body>
<div class="card">
    <h1>🚀 Tracker Update Server</h1>
    <div class="version">Latest: {{filename}} (v{{version}})</div>
    {% if message %}<div class="message">{{message}}</div>{% endif %}
    
    <form method="post" enctype="multipart/form-data" class="upload-form">
        <input type="file" name="file" accept=".exe" required>
        <button type="submit">📤 Upload New Tracker</button>
    </form>
    
    <h3>All EXE Files:</h3>
    <ul class="files">
    {% for f in files %}
        <li>{{f}} {% if f == filename %}<span style="color:green;">✓ LATEST</span>{% endif %}</li>
    {% endfor %}
    </ul>
    
    <p><a href="/version">API: /version</a> | <a href="/download">API: /download</a></p>
</div>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
