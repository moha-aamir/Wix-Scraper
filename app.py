"""
Wix to Offline Converter - Web Application
A Flask-based web interface for converting Wix websites to offline files
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
import asyncio
import os
import json
import shutil
import zipfile
import threading
import queue
from datetime import datetime
from urllib.parse import urlparse
import uuid

# Import the wix scraper functions
from wixscraper import scrape_wix_site

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wix-converter-secret-key'

# Store for conversion jobs
conversion_jobs = {}
message_queues = {}

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'converted_sites')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def run_async(coro):
    """Helper to run async code in a new event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def convert_website_task(job_id, site_url, options):
    """Background task to convert a website"""
    msg_queue = message_queues.get(job_id)
    
    def progress_callback(message):
        if msg_queue:
            msg_queue.put(message)
        print(f"[{job_id}] {message}")
    
    try:
        conversion_jobs[job_id]['status'] = 'running'
        progress_callback("Starting conversion...")
        
        # Parse options
        block_primary_folder = options.get('blockPrimaryFolder', '')
        wait_time = int(options.get('wait', 3))
        recursive = options.get('recursive', False)
        dark_website = options.get('darkWebsite', False)
        force_download = options.get('forceDownload', False)
        
        # Build metatags
        metatags = {
            '/': {
                'title': options.get('title', 'Website'),
                'description': options.get('description', ''),
                'keywords': options.get('keywords', ''),
                'canonical': site_url,
                'image': options.get('image', ''),
                'author': options.get('author', '')
            }
        }
        
        # Build mapData
        mapData = {
            'latitude': options.get('mapLatitude', '0'),
            'longitude': options.get('mapLongitude', '0'),
            'zoom': options.get('mapZoom', '12'),
            'mapMarker': {
                'latitude': options.get('mapMarkerLatitude', options.get('mapLatitude', '0')),
                'longitude': options.get('mapMarkerLongitude', options.get('mapLongitude', '0')),
                'popup': options.get('mapPopup', '')
            }
        }
        
        # Create job-specific output directory
        job_output_dir = os.path.join(OUTPUT_DIR, job_id)
        if not os.path.exists(job_output_dir):
            os.makedirs(job_output_dir)
        
        # Run the scraper
        output_path = run_async(scrape_wix_site(
            site=site_url,
            blockPrimaryFolder=block_primary_folder,
            wait=wait_time,
            recursive=recursive,
            darkWebsite=dark_website,
            forceDownloadAgain=force_download,
            metatags=metatags,
            mapData=mapData,
            output_dir=job_output_dir,
            progress_callback=progress_callback
        ))
        
        # Create ZIP file
        progress_callback("Creating ZIP archive...")
        hostname = urlparse(site_url).hostname
        zip_filename = f"{hostname}_{job_id}.zip"
        zip_path = os.path.join(OUTPUT_DIR, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, job_output_dir)
                    zipf.write(file_path, arcname)
        
        conversion_jobs[job_id]['status'] = 'completed'
        conversion_jobs[job_id]['output_path'] = output_path
        conversion_jobs[job_id]['zip_path'] = zip_path
        conversion_jobs[job_id]['zip_filename'] = zip_filename
        progress_callback("Conversion completed successfully!")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        conversion_jobs[job_id]['status'] = 'failed'
        conversion_jobs[job_id]['error'] = str(e)
        if msg_queue:
            msg_queue.put(f"Error: {str(e)}")
        print(f"[{job_id}] Error: {str(e)}")
        print(f"[{job_id}] Traceback:\n{error_details}")


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    """Start a conversion job"""
    data = request.json
    site_url = data.get('url', '').strip()
    
    if not site_url:
        return jsonify({'error': 'Please provide a website URL'}), 400
    
    # Validate URL
    if not site_url.startswith('http'):
        site_url = 'https://' + site_url
    
    # Create job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Create message queue for this job
    message_queues[job_id] = queue.Queue()
    
    # Initialize job
    conversion_jobs[job_id] = {
        'id': job_id,
        'url': site_url,
        'status': 'queued',
        'created_at': datetime.now().isoformat(),
        'options': data.get('options', {})
    }
    
    # Start conversion in background thread
    thread = threading.Thread(
        target=convert_website_task,
        args=(job_id, site_url, data.get('options', {}))
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})


@app.route('/status/<job_id>')
def job_status(job_id):
    """Get status of a conversion job"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(conversion_jobs[job_id])


@app.route('/stream/<job_id>')
def stream(job_id):
    """Stream progress updates for a job"""
    def generate():
        msg_queue = message_queues.get(job_id)
        if not msg_queue:
            yield f"data: Job not found\n\n"
            return
        
        while True:
            try:
                message = msg_queue.get(timeout=30)
                yield f"data: {message}\n\n"
                
                # Check if job is complete
                if job_id in conversion_jobs:
                    status = conversion_jobs[job_id].get('status')
                    if status in ['completed', 'failed']:
                        break
            except queue.Empty:
                yield f"data: Waiting...\n\n"
                if job_id in conversion_jobs:
                    status = conversion_jobs[job_id].get('status')
                    if status in ['completed', 'failed']:
                        break
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/download/<job_id>')
def download(job_id):
    """Download converted website"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = conversion_jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Conversion not complete'}), 400
    
    zip_path = job.get('zip_path')
    if not zip_path or not os.path.exists(zip_path):
        return jsonify({'error': 'Download file not found'}), 404
    
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=job.get('zip_filename', 'website.zip')
    )


@app.route('/jobs')
def list_jobs():
    """List all conversion jobs"""
    return jsonify(list(conversion_jobs.values()))


if __name__ == '__main__':
    print("=" * 50)
    print("Wix to Offline Converter")
    print("=" * 50)
    print("Starting web server...")
    print("Open http://localhost:5000 in your browser")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
