#!/usr/bin/env python3
"""
YouTube Transcript Downloader Web Application
Runs on port 8000 and allows users to download transcripts from YouTube videos
"""

from flask import Flask, render_template_string, request, jsonify
import yt_dlp
import re

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Transcript Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .content {
            padding: 30px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 12px 15px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        button {
            flex: 1;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .transcript-group {
            margin-top: 20px;
        }
        
        textarea {
            width: 100%;
            min-height: 400px;
            padding: 15px;
            font-size: 14px;
            font-family: 'Courier New', monospace;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            resize: vertical;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .message {
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        
        .message.show {
            display: block;
        }
        
        .message.error {
            background: #fee;
            color: #c33;
            border-left: 4px solid #c33;
        }
        
        .message.success {
            background: #efe;
            color: #3c3;
            border-left: 4px solid #3c3;
        }
        
        .message.info {
            background: #eef;
            color: #33c;
            border-left: 4px solid #33c;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 8px;
            font-size: 14px;
            color: #666;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .video-info {
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        
        .video-info.show {
            display: block;
        }
        
        .video-info-item {
            margin-bottom: 8px;
            line-height: 1.5;
        }
        
        .video-info-item:last-child {
            margin-bottom: 0;
        }
        
        .video-info-item strong {
            color: #667eea;
        }
        
        .video-info-item span {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📹 YouTube Transcript Downloader</h1>
            <p>Extract transcripts from any YouTube video</p>
        </div>
        
        <div class="content">
            <div id="message" class="message"></div>
            
            <div class="input-group">
                <label for="youtube-url">YouTube Video URL</label>
                <input 
                    type="text" 
                    id="youtube-url" 
                    placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                    autocomplete="off"
                >
            </div>
            
            <div class="button-group">
                <button class="btn-primary" onclick="downloadTranscript()">
                    Download Transcript
                </button>
                <button class="btn-secondary" onclick="copyToClipboard()">
                    Copy Transcript
                </button>
                <button class="btn-secondary" onclick="clearFields()">
                    Clear
                </button>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Fetching transcript...</p>
            </div>
            
            <div id="video-info" class="video-info">
                <div class="video-info-item">
                    <strong>📹 Title:</strong> <span id="video-title"></span>
                </div>
                <div class="video-info-item">
                    <strong>👤 Channel:</strong> <span id="video-channel"></span>
                </div>
            </div>
            
            <div class="transcript-group">
                <label for="transcript">Transcript</label>
                <textarea 
                    id="transcript" 
                    placeholder="Transcript will appear here..."
                    readonly
                ></textarea>
                <div id="stats" class="stats" style="display: none;">
                    <div class="stat-item">
                        <strong>Words:</strong> <span id="word-count">0</span>
                    </div>
                    <div class="stat-item">
                        <strong>Characters:</strong> <span id="char-count">0</span>
                    </div>
                    <div class="stat-item">
                        <strong>Duration:</strong> <span id="duration">0:00</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showMessage(message, type) {
            const msgDiv = document.getElementById('message');
            msgDiv.textContent = message;
            msgDiv.className = `message ${type} show`;
            setTimeout(() => {
                msgDiv.classList.remove('show');
            }, 5000);
        }
        
        function showLoading(show) {
            document.getElementById('loading').classList.toggle('show', show);
        }
        
        function updateStats(text, duration) {
            const words = text.trim().split(/\s+/).length;
            const chars = text.length;
            const minutes = Math.floor(duration / 60);
            const seconds = Math.floor(duration % 60);
            
            document.getElementById('word-count').textContent = words.toLocaleString();
            document.getElementById('char-count').textContent = chars.toLocaleString();
            document.getElementById('duration').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            document.getElementById('stats').style.display = 'flex';
        }
        
        function showVideoInfo(title, channel) {
            document.getElementById('video-title').textContent = title;
            document.getElementById('video-channel').textContent = channel;
            document.getElementById('video-info').classList.add('show');
        }
        
        function copyToClipboard() {
            const transcriptArea = document.getElementById('transcript');
            const text = transcriptArea.value;
            
            if (!text) {
                showMessage('No transcript to copy', 'error');
                return;
            }
            
            // Use modern clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(() => {
                    showMessage('Transcript copied to clipboard!', 'success');
                }).catch(err => {
                    fallbackCopy(transcriptArea);
                });
            } else {
                fallbackCopy(transcriptArea);
            }
        }
        
        function fallbackCopy(transcriptArea) {
            try {
                transcriptArea.select();
                transcriptArea.setSelectionRange(0, 99999); // For mobile
                document.execCommand('copy');
                showMessage('Transcript copied to clipboard!', 'success');
            } catch (err) {
                showMessage('Failed to copy. Please select and copy manually.', 'error');
            }
        }
        
        async function downloadTranscript() {
            const urlInput = document.getElementById('youtube-url');
            const transcriptArea = document.getElementById('transcript');
            const url = urlInput.value.trim();
            
            if (!url) {
                showMessage('Please enter a YouTube URL', 'error');
                return;
            }
            
            showLoading(true);
            transcriptArea.value = '';
            document.getElementById('stats').style.display = 'none';
            document.getElementById('video-info').classList.remove('show');
            
            try {
                const response = await fetch('/api/transcript', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    transcriptArea.value = data.transcript;
                    updateStats(data.transcript, data.duration);
                    showVideoInfo(data.title, data.channel);
                    showMessage('Transcript downloaded successfully!', 'success');
                } else {
                    showMessage(data.error || 'Failed to download transcript', 'error');
                }
            } catch (error) {
                showMessage('Network error: ' + error.message, 'error');
            } finally {
                showLoading(false);
            }
        }
        
        function clearFields() {
            document.getElementById('youtube-url').value = '';
            document.getElementById('transcript').value = '';
            document.getElementById('stats').style.display = 'none';
            document.getElementById('video-info').classList.remove('show');
            document.getElementById('message').classList.remove('show');
        }
        
        // Allow Enter key to submit
        document.getElementById('youtube-url').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                downloadTranscript();
            }
        });
    </script>
</body>
</html>
"""


def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/transcript', methods=['POST'])
def get_transcript():
    """API endpoint to fetch YouTube transcript"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'No URL provided'
            }), 400
        
        # Extract video ID
        video_id = extract_video_id(url)
        
        if not video_id:
            return jsonify({
                'success': False,
                'error': 'Invalid YouTube URL format'
            }), 400
        
        # Configure yt-dlp options
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        # Fetch video info and subtitles
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({
                    'success': False,
                    'error': 'Could not retrieve video information'
                }), 404
            
            # Get duration
            duration = info.get('duration', 0)
            
            # Get video metadata
            title = info.get('title', 'Unknown Title')
            channel = info.get('uploader', info.get('channel', 'Unknown Channel'))
            
            # Try to get subtitles (prefer manual over automatic)
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            # Prefer English subtitles
            subtitle_data = None
            if 'en' in subtitles:
                subtitle_data = subtitles['en']
            elif 'en' in automatic_captions:
                subtitle_data = automatic_captions['en']
            elif subtitles:
                # Use first available subtitle language
                subtitle_data = list(subtitles.values())[0]
            elif automatic_captions:
                # Use first available automatic caption
                subtitle_data = list(automatic_captions.values())[0]
            
            if not subtitle_data:
                return jsonify({
                    'success': False,
                    'error': 'No subtitles or transcripts available for this video'
                }), 404
            
            # Download the subtitle content
            subtitle_url = None
            for fmt in subtitle_data:
                if fmt.get('ext') in ['vtt', 'srv3', 'srv2', 'srv1', 'json3']:
                    subtitle_url = fmt.get('url')
                    break
            
            if not subtitle_url:
                return jsonify({
                    'success': False,
                    'error': 'Could not find downloadable subtitle format'
                }), 404
            
            # Fetch subtitle content
            import urllib.request
            with urllib.request.urlopen(subtitle_url) as response:
                subtitle_content = response.read().decode('utf-8')
            
            # Parse VTT or similar format to extract text
            transcript_text = parse_subtitle_content(subtitle_content)
            
            if not transcript_text:
                return jsonify({
                    'success': False,
                    'error': 'Could not parse subtitle content'
                }), 500
        
        return jsonify({
            'success': True,
            'transcript': transcript_text,
            'duration': duration,
            'video_id': video_id,
            'title': title,
            'channel': channel
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500


def parse_subtitle_content(content):
    """Parse VTT, SRT, or JSON subtitle format to extract plain text"""
    import json
    
    lines = []
    
    # Try to parse as JSON first (YouTube's json3 format)
    try:
        data = json.loads(content)
        
        # Handle json3 format
        if 'events' in data:
            for event in data['events']:
                if 'segs' in event:
                    for seg in event['segs']:
                        if 'utf8' in seg:
                            text = seg['utf8'].strip()
                            # Remove newline characters within segments
                            text = text.replace('\n', ' ')
                            if text:
                                lines.append(text)
        
        return ' '.join(lines)
    
    except (json.JSONDecodeError, KeyError):
        # Not JSON or different format, try VTT/SRT parsing
        pass
    
    # Parse VTT or SRT format
    for line in content.split('\n'):
        line = line.strip()
        
        # Skip empty lines, timing lines, and VTT headers
        if not line or line.startswith('WEBVTT') or '-->' in line or line.isdigit():
            continue
        
        # Remove HTML tags
        line = re.sub(r'<[^>]+>', '', line)
        
        # Skip lines that are just timestamps
        if re.match(r'^\d{2}:\d{2}:\d{2}', line):
            continue
        
        lines.append(line)
    
    return '\n'.join(lines)


if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Transcript Downloader")
    print("=" * 60)
    print(f"Server starting on http://192.168.44.11:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=False)
