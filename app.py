from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, abort
import threading
import os
import logging
from logging.handlers import RotatingFileHandler
import shutil


app = Flask(__name__)

# Configure logging
log_file = 'logfile.log'  # Replace with your desired log file path
file_handler = RotatingFileHandler(log_file, mode='a', maxBytes=10*1024*1024, backupCount=2)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the app's logger
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Define the upload folder path
UPLOAD_FOLDER = '/mnt/ssd'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set maximum file upload size to 10GB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB
app.logger.info("------- START UP -------")

@app.route('/', methods=['GET', 'POST'])
def index():
    req_path = request.args.get('req_path', '')
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], req_path)
    
    # Ensure the path exists
    if not os.path.exists(full_path):
        return "Not Found", 404
    
    files = []
    directories = []
    for f in os.listdir(full_path):
        full_file_path = os.path.join(full_path, f)
        if os.path.isdir(full_file_path):
            if 'lost+found' in f:
                continue
            directories.append((f, url_for('index', req_path=os.path.join(req_path, f))))
        else:
            files.append((f, url_for('download_file', filename=f, path=req_path)))
    
    show_upload = req_path != ''  # Show upload form unless at the root directory
    
    return render_template('index.html', files=files, directories=directories, current_path=req_path, show_upload=show_upload, storage_info=storage_info)

def save_file(file_data, file_path):
    try:
        with open(file_path, 'wb') as f:
            f.write(file_data)
            app.logger.info(f"Saved file {file_path}.")
    except Exception as e:
        app.logger.error(f"Error saving file {file_path}: {e}")
        
@app.route('/storage_info', methods=['GET'])
def storage_info():
    total, used, free = shutil.disk_usage("/mnt/ssd")
    return jsonify({
        'total': total,
        'used': used,
        'free': free
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    path = request.form.get('path', '')  # Get path from form data

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # Ensure the path is correctly joined with the upload folder
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
        os.makedirs(upload_path, exist_ok=True)  # Create directory if it doesn't exist
        file_path = os.path.join(upload_path, file.filename)
        
        # Read file data into memory
        file_data = file.read()
        
        # Start a thread to save the file asynchronously
        thread = threading.Thread(target=save_file, args=(file_data, file_path))
        thread.start()

        return jsonify({'success': True}), 200

@app.route('/file_list', methods=['GET'])
def file_list():
    current_path = request.args.get('path', '')  # Get the path from query params
    files = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], current_path))
    return jsonify({'files': files})

@app.route('/delete', methods=['POST'])
def delete_file():
    filename = request.form['filename']
    path = request.form['path']
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path, filename)
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
            app.logger.info(f"Deleted file {full_path}.")
        else:
            os.rmdir(full_path)
            app.logger.info(f"Deleted directory {full_path}.")
        return redirect(url_for('index', req_path=path))
    except Exception as e:
        app.logger.error(f"Error deleting file: {e}")
        return f"Error deleting file: {e}", 500

@app.route('/rename', methods=['POST'])
def rename_file():
    old_filename = request.form['filename']
    new_filename = request.form['new_filename']
    path = request.form['path']
    
    _, file_extension = os.path.splitext(old_filename)
    if not new_filename.endswith(file_extension):
        new_filename = new_filename + file_extension
    
    old_full_path = os.path.join(app.config['UPLOAD_FOLDER'], path, old_filename)
    new_full_path = os.path.join(app.config['UPLOAD_FOLDER'], path, new_filename)
    
    try:
        os.rename(old_full_path, new_full_path)
        app.logger.info(f"Renamed file from {old_full_path} to {new_full_path}")
        return redirect(url_for('index', req_path=path))
    except Exception as e:
        app.logger.error(f"Error renaming file: {e}")
        return f"Error renaming file: {e}", 500

@app.route('/download', methods=['GET'])
def download_file():
    filename = request.args.get('filename', '')
    path = request.args.get('path', '')
    
    if not filename or path is None:
        return "Invalid request", 400

    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    if not os.path.isfile(os.path.join(full_path, filename)):
        return "File not found", 404

    try:
        app.logger.info(f"Downloading file {full_path}, {filename}")
        return send_from_directory(full_path, filename, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error sending file: {e}")
        return "Error processing request", 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return "File is too large. Maximum file size is 10GB.", 413

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
