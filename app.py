from flask import Flask, jsonify, send_from_directory, abort, render_template_string
import os
import re

app = Flask(__name__)

def get_latest_tracker():
    server_filename = os.environ.get('LATEST_TRACKER', '')
    server_version = float(os.environ.get('LATEST_VERSION', '0.0'))
    
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
                return max(tracker_files, key=lambda x: x[1])
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

HTML_TEMPLATE = """[SAME HTML AS BEFORE - NO CHANGE]"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
