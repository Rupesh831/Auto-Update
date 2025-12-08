from flask import Flask, jsonify, send_from_directory, abort, render_template_string
import os
import re

app = Flask(__name__)

def get_latest_tracker():
    """Get from ENV vars or detect files."""
    # Render ENV vars (set in Render Dashboard)
    server_filename = os.environ.get('LATEST_TRACKER', '')
    server_version = float(os.environ.get('LATEST_VERSION', '0.0'))
    
    # Fallback to file detection
    if not server_filename:
        tracker_files = []
        try:
            for f in os.listdir('.'):
                if f.endswith('.exe') and re.match(r'tracker_v\d+\.\d+\.exe', f, re.IGNORECASE):
                    version_match = re.search(r'v(\d+\.\d+)', f)
                    if version_match:
                        version = float(version_match.group(1))
                        tracker_files.append((f, version))
            if tracker_files:
                latest = max(tracker_files, key=lambda x: x[1])
                return latest[0], latest[1]
        except:
            pass
    return server_filename, server_version

@app.route('/')
def index():
    filename, version = get_latest_tracker()
    files = [f for f in os.listdir('.') if f.endswith('.exe')]
    return render_template_string(HTML_TEMPLATE, filename=filename or 'None', 
                                version=version, files=files)

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
<style>body{font-family:Arial;max-width:800px;margin:50px auto;padding:20px;background:#f5f5f5;}
.card{background:white;padding:30px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);}
.version{color:#2196F3;font-size:28px;font-weight:bold;}
.files{list-style:none;padding:0;}
.files li{margin:10px 0;padding:15px;background:#e3f2fd;border-radius:5px;}
a{display:inline-block;padding:10px 20px;background:#2196F3;color:white;text-decoration:none;border-radius:5px;margin:5px;}
.env-info{background:#fff3cd;padding:15px;border-radius:5px;border-left:4px solid #ffc107;}
</style>
</head>
<body>
<div class="card">
    <h1>🚀 Tracker Update Server</h1>
    <div class="version">Latest: {{filename}} (v{{version}})</div>
    
    <div class="env-info">
        <strong>📋 Render Setup:</strong><br>
        Add ENV vars in Render Dashboard:<br>
        <code>LATEST_TRACKER=tracker_v1.5.exe</code><br>
        <code>LATEST_VERSION=1.5</code>
    </div>
    
    <h3>Available Files:</h3>
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
