#!/usr/bin/env python3
"""
YouTube Transcript Downloader Web Application with OpenAI Integration
Runs on port 8000 and allows users to download transcripts from YouTube videos
and analyze them with OpenAI
"""

from flask import Flask, render_template_string, request, jsonify
import yt_dlp
import re
import os
import json
from pathlib import Path
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Saved prompts file path
PROMPTS_FILE = Path('/opt/youtube-transcript/saved_prompts.json')

# Default prompts
DEFAULT_PROMPTS = [
    {
        "id": 1,
        "name": "Summarize Key Points",
        "prompt": "Summarize the key points of this video in 3-5 bullet points."
    },
    {
        "id": 2,
        "name": "Extract Main Topics",
        "prompt": "List the main topics and subtopics discussed in this video."
    },
    {
        "id": 3,
        "name": "Create Study Notes",
        "prompt": "Create comprehensive study notes from this video transcript, organizing the information by topic."
    },
    {
        "id": 4,
        "name": "Extract Statistics",
        "prompt": "Extract all statistics, data points, and numerical information mentioned in this video."
    },
    {
        "id": 5,
        "name": "LinkedIn Post",
        "prompt": "Write an engaging LinkedIn post about this video that highlights the key insights."
    }
]

def load_prompts():
    """Load saved prompts from file or create default prompts"""
    if not PROMPTS_FILE.exists():
        save_prompts(DEFAULT_PROMPTS)
        return DEFAULT_PROMPTS
    
    try:
        with open(PROMPTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading prompts: {e}")
        return DEFAULT_PROMPTS

def save_prompts(prompts):
    """Save prompts to file"""
    try:
        with open(PROMPTS_FILE, 'w') as f:
            json.dump(prompts, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving prompts: {e}")
        return False

def get_next_prompt_id(prompts):
    """Get next available prompt ID"""
    if not prompts:
        return 1
    return max(p['id'] for p in prompts) + 1

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
            max-width: 1200px;
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
        
        input[type="text"], textarea {
            width: 100%;
            padding: 12px 15px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            transition: border-color 0.3s;
            font-family: inherit;
        }
        
        input[type="text"]:focus, textarea:focus {
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
        
        .btn-primary:hover:not(:disabled) {
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
        
        .btn-ai {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        
        .btn-ai:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(16, 185, 129, 0.4);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .transcript-group {
            margin-top: 20px;
        }
        
        textarea {
            min-height: 300px;
            font-size: 14px;
            font-family: 'Courier New', monospace;
            resize: vertical;
        }
        
        textarea.readonly {
            background-color: #f9f9f9;
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
        
        .toggle-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: 0.4s;
            border-radius: 24px;
        }
        
        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: 0.4s;
            border-radius: 50%;
        }
        
        input:checked + .toggle-slider {
            background-color: #667eea;
        }
        
        input:checked + .toggle-slider:before {
            transform: translateX(26px);
        }
        
        .toggle-label {
            font-weight: 600;
            color: #333;
            cursor: pointer;
            user-select: none;
        }
        
        .prompt-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
            align-items: center;
        }
        
        .prompt-selector select {
            flex: 1;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
        }
        
        .prompt-selector select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn-icon {
            padding: 10px 15px;
            font-size: 16px;
            background: #f0f0f0;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-icon:hover {
            background: #e0e0e0;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background-color: white;
            padding: 30px;
            border-radius: 15px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-header h2 {
            margin: 0;
            color: #667eea;
        }
        
        .close-btn {
            font-size: 28px;
            font-weight: bold;
            color: #aaa;
            cursor: pointer;
            border: none;
            background: none;
            padding: 0;
            line-height: 1;
        }
        
        .close-btn:hover {
            color: #000;
        }
        
        .modal-body {
            margin-bottom: 20px;
        }
        
        .modal-body label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        
        .modal-body input[type="text"],
        .modal-body textarea {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .modal-footer {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .btn-modal {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-modal-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-modal-secondary {
            background: #f0f0f0;
            color: #333;
        }
        
        .btn-modal:hover {
            transform: translateY(-2px);
        }
        
        .prompt-list {
            max-height: 400px;
            overflow-y: auto;
            margin: 20px 0;
        }
        
        .prompt-item {
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: start;
        }
        
        .prompt-item-content {
            flex: 1;
        }
        
        .prompt-item-name {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .prompt-item-text {
            color: #666;
            font-size: 14px;
        }
        
        .prompt-item-actions {
            display: flex;
            gap: 5px;
        }
        
        .btn-small {
            padding: 5px 10px;
            font-size: 12px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            background: #f0f0f0;
        }
        
        .btn-small:hover {
            background: #e0e0e0;
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
        
        .ai-section {
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid #e0e0e0;
        }
        
        .ai-section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        
        @media (max-width: 768px) {
            .two-column {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📹 YouTube Transcript Downloader</h1>
            <p>Extract transcripts from any YouTube video and analyze with AI</p>
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
            
            <div class="toggle-container">
                <label class="toggle-switch">
                    <input type="checkbox" id="timestamp-toggle">
                    <span class="toggle-slider"></span>
                </label>
                <label for="timestamp-toggle" class="toggle-label">
                    ⏱️ Include Timestamps
                </label>
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
                <p id="loading-text">Fetching transcript...</p>
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
                    class="readonly"
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
            
            <div class="ai-section">
                <h2>🤖 AI Analysis</h2>
                
                <div class="input-group">
                    <label for="prompt-selector">Saved Prompts</label>
                    <div class="prompt-selector">
                        <select id="prompt-selector" onchange="loadSelectedPrompt()">
                            <option value="">-- Select a saved prompt --</option>
                        </select>
                        <button class="btn-icon" onclick="openManagePromptsModal()" title="Manage Prompts">
                            ⚙️
                        </button>
                    </div>
                </div>
                
                <div class="input-group">
                    <label for="ai-prompt">Prompt for OpenAI</label>
                    <textarea 
                        id="ai-prompt" 
                        placeholder="Ask OpenAI to analyze the transcript... e.g., 'Summarize the key points' or 'What are the main takeaways?'"
                        rows="4"
                    ></textarea>
                </div>
                
                <div class="button-group">
                    <button class="btn-ai" id="analyze-btn" onclick="analyzeWithAI()" disabled>
                        🚀 Analyze with OpenAI
                    </button>
                    <button class="btn-secondary" onclick="copyAIResponse()">
                        Copy AI Response
                    </button>
                </div>
                
                <div class="input-group">
                    <label for="ai-response">AI Response</label>
                    <textarea 
                        id="ai-response" 
                        class="readonly"
                        placeholder="AI response will appear here..."
                        readonly
                        rows="15"
                    ></textarea>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Manage Prompts Modal -->
    <div id="manage-prompts-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Manage Prompts</h2>
                <button class="close-btn" onclick="closeManagePromptsModal()">&times;</button>
            </div>
            <div class="modal-body">
                <button class="btn-modal btn-modal-primary" onclick="openCreatePromptModal()" style="width: 100%; margin-bottom: 15px;">
                    ➕ Create New Prompt
                </button>
                <div id="prompt-list" class="prompt-list">
                    <!-- Prompts will be loaded here -->
                </div>
            </div>
        </div>
    </div>
    
    <!-- Create/Edit Prompt Modal -->
    <div id="prompt-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="prompt-modal-title">Create New Prompt</h2>
                <button class="close-btn" onclick="closePromptModal()">&times;</button>
            </div>
            <div class="modal-body">
                <input type="hidden" id="prompt-id">
                <label for="prompt-name">Prompt Name</label>
                <input type="text" id="prompt-name" placeholder="e.g., Summarize Key Points">
                
                <label for="prompt-text">Prompt Text</label>
                <textarea id="prompt-text" rows="6" placeholder="Enter the prompt text that will be sent to OpenAI..."></textarea>
            </div>
            <div class="modal-footer">
                <button class="btn-modal btn-modal-secondary" onclick="closePromptModal()">Cancel</button>
                <button class="btn-modal btn-modal-primary" onclick="savePrompt()">Save</button>
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
        
        function showLoading(show, text = 'Fetching transcript...') {
            document.getElementById('loading').classList.toggle('show', show);
            document.getElementById('loading-text').textContent = text;
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
        
        function copyAIResponse() {
            const aiResponseArea = document.getElementById('ai-response');
            const text = aiResponseArea.value;
            
            if (!text) {
                showMessage('No AI response to copy', 'error');
                return;
            }
            
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(() => {
                    showMessage('AI response copied to clipboard!', 'success');
                }).catch(err => {
                    fallbackCopy(aiResponseArea);
                });
            } else {
                fallbackCopy(aiResponseArea);
            }
        }
        
        function fallbackCopy(textarea) {
            try {
                textarea.select();
                textarea.setSelectionRange(0, 99999);
                document.execCommand('copy');
                showMessage('Copied to clipboard!', 'success');
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
            
            showLoading(true, 'Fetching transcript...');
            transcriptArea.value = '';
            document.getElementById('ai-response').value = '';
            document.getElementById('stats').style.display = 'none';
            document.getElementById('video-info').classList.remove('show');
            document.getElementById('analyze-btn').disabled = true;
            
            try {
                const includeTimestamps = document.getElementById('timestamp-toggle').checked;
                
                const response = await fetch('/api/transcript', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        url: url,
                        include_timestamps: includeTimestamps
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    transcriptArea.value = data.transcript;
                    updateStats(data.transcript, data.duration);
                    showVideoInfo(data.title, data.channel);
                    document.getElementById('analyze-btn').disabled = false;
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
        
        async function analyzeWithAI() {
            const analyzeBtn = document.getElementById('analyze-btn');
            const aiResponseArea = document.getElementById('ai-response');
            
            // Check if button is in "Clear" mode
            if (analyzeBtn.textContent.includes('Clear')) {
                // Clear mode - just clear the response and reset button
                aiResponseArea.value = '';
                analyzeBtn.innerHTML = '🚀 Analyze with OpenAI';
                analyzeBtn.classList.remove('btn-secondary');
                analyzeBtn.classList.add('btn-ai');
                return;
            }
            
            // Analyze mode - proceed with analysis
            const transcript = document.getElementById('transcript').value;
            const prompt = document.getElementById('ai-prompt').value.trim();
            
            if (!transcript) {
                showMessage('Please download a transcript first', 'error');
                return;
            }
            
            if (!prompt) {
                showMessage('Please enter a prompt for AI analysis', 'error');
                return;
            }
            
            showLoading(true, 'Analyzing with OpenAI...');
            aiResponseArea.value = '';
            analyzeBtn.disabled = true;
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        transcript: transcript,
                        prompt: prompt
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    aiResponseArea.value = data.response;
                    showMessage('Analysis complete!', 'success');
                    
                    // Change button to "Clear AI Response"
                    analyzeBtn.innerHTML = '🗑️ Clear AI Response';
                    analyzeBtn.classList.remove('btn-ai');
                    analyzeBtn.classList.add('btn-secondary');
                } else {
                    showMessage(data.error || 'Failed to analyze with AI', 'error');
                }
            } catch (error) {
                showMessage('Network error: ' + error.message, 'error');
            } finally {
                showLoading(false);
                analyzeBtn.disabled = false;
            }
        }
        
        function clearFields() {
            document.getElementById('youtube-url').value = '';
            document.getElementById('transcript').value = '';
            document.getElementById('ai-prompt').value = '';
            document.getElementById('ai-response').value = '';
            document.getElementById('stats').style.display = 'none';
            document.getElementById('video-info').classList.remove('show');
            document.getElementById('message').classList.remove('show');
            
            // Reset analyze button
            const analyzeBtn = document.getElementById('analyze-btn');
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '🚀 Analyze with OpenAI';
            analyzeBtn.classList.remove('btn-secondary');
            analyzeBtn.classList.add('btn-ai');
        }
        
        // Saved Prompts Management
        let savedPrompts = [];
        
        async function loadPrompts() {
            try {
                const response = await fetch('/api/prompts');
                const data = await response.json();
                if (data.success) {
                    savedPrompts = data.prompts;
                    updatePromptSelector();
                }
            } catch (error) {
                console.error('Error loading prompts:', error);
            }
        }
        
        function updatePromptSelector() {
            const selector = document.getElementById('prompt-selector');
            selector.innerHTML = '<option value="">-- Select a saved prompt --</option>';
            
            savedPrompts.forEach(prompt => {
                const option = document.createElement('option');
                option.value = prompt.id;
                option.textContent = prompt.name;
                selector.appendChild(option);
            });
        }
        
        function loadSelectedPrompt() {
            const selector = document.getElementById('prompt-selector');
            const selectedId = parseInt(selector.value);
            
            if (!selectedId) {
                return;
            }
            
            const prompt = savedPrompts.find(p => p.id === selectedId);
            if (prompt) {
                document.getElementById('ai-prompt').value = prompt.prompt;
            }
        }
        
        function openManagePromptsModal() {
            loadPromptList();
            document.getElementById('manage-prompts-modal').classList.add('show');
        }
        
        function closeManagePromptsModal() {
            document.getElementById('manage-prompts-modal').classList.remove('show');
        }
        
        function loadPromptList() {
            const listDiv = document.getElementById('prompt-list');
            
            if (savedPrompts.length === 0) {
                listDiv.innerHTML = '<p style="text-align: center; color: #999;">No saved prompts yet</p>';
                return;
            }
            
            listDiv.innerHTML = savedPrompts.map(prompt => `
                <div class="prompt-item">
                    <div class="prompt-item-content">
                        <div class="prompt-item-name">${escapeHtml(prompt.name)}</div>
                        <div class="prompt-item-text">${escapeHtml(prompt.prompt.substring(0, 100))}${prompt.prompt.length > 100 ? '...' : ''}</div>
                    </div>
                    <div class="prompt-item-actions">
                        <button class="btn-small" onclick="editPrompt(${prompt.id})">✏️ Edit</button>
                        <button class="btn-small" onclick="deletePrompt(${prompt.id})">🗑️ Delete</button>
                    </div>
                </div>
            `).join('');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function openCreatePromptModal() {
            document.getElementById('prompt-modal-title').textContent = 'Create New Prompt';
            document.getElementById('prompt-id').value = '';
            document.getElementById('prompt-name').value = '';
            document.getElementById('prompt-text').value = '';
            document.getElementById('prompt-modal').classList.add('show');
        }
        
        function editPrompt(id) {
            const prompt = savedPrompts.find(p => p.id === id);
            if (!prompt) return;
            
            document.getElementById('prompt-modal-title').textContent = 'Edit Prompt';
            document.getElementById('prompt-id').value = prompt.id;
            document.getElementById('prompt-name').value = prompt.name;
            document.getElementById('prompt-text').value = prompt.prompt;
            document.getElementById('prompt-modal').classList.add('show');
        }
        
        function closePromptModal() {
            document.getElementById('prompt-modal').classList.remove('show');
        }
        
        async function savePrompt() {
            const id = document.getElementById('prompt-id').value;
            const name = document.getElementById('prompt-name').value.trim();
            const promptText = document.getElementById('prompt-text').value.trim();
            
            if (!name || !promptText) {
                showMessage('Please fill in both name and prompt text', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/prompts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        id: id ? parseInt(id) : null,
                        name: name,
                        prompt: promptText
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage(id ? 'Prompt updated successfully!' : 'Prompt created successfully!', 'success');
                    await loadPrompts();
                    closePromptModal();
                    loadPromptList();
                } else {
                    showMessage(data.error || 'Failed to save prompt', 'error');
                }
            } catch (error) {
                showMessage('Network error: ' + error.message, 'error');
            }
        }
        
        async function deletePrompt(id) {
            if (!confirm('Are you sure you want to delete this prompt?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/prompts/' + id, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('Prompt deleted successfully!', 'success');
                    await loadPrompts();
                    loadPromptList();
                } else {
                    showMessage(data.error || 'Failed to delete prompt', 'error');
                }
            } catch (error) {
                showMessage('Network error: ' + error.message, 'error');
            }
        }
        
        // Load prompts on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadPrompts();
        });
        
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
        include_timestamps = data.get('include_timestamps', False)
        
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
            transcript_text = parse_subtitle_content(subtitle_content, include_timestamps)
            
            if not transcript_text:
                return jsonify({
                    'success': False,
                    'error': 'Could not parse subtitle content'
                }), 500
            
            # Format transcript with metadata header
            from datetime import datetime
            today = datetime.now().strftime('%B %d, %Y')
            duration_formatted = f"{duration // 60}:{duration % 60:02d}"
            
            formatted_transcript = f"""# {title}
**Channel:** {channel}
**URL:** {url}
**Duration:** {duration_formatted}
**Date Watched:** {today}

Transcript:
{transcript_text}"""
        
        return jsonify({
            'success': True,
            'transcript': formatted_transcript,
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


@app.route('/api/analyze', methods=['POST'])
def analyze_transcript():
    """API endpoint to analyze transcript with OpenAI"""
    try:
        data = request.get_json()
        transcript = data.get('transcript', '').strip()
        prompt = data.get('prompt', '').strip()
        
        if not transcript:
            return jsonify({
                'success': False,
                'error': 'No transcript provided'
            }), 400
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'No prompt provided'
            }), 400
        
        # Check if API key is configured
        if not os.getenv('OPENAI_API_KEY'):
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not configured on server'
            }), 500
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o-mini for cost efficiency
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes YouTube video transcripts. Provide clear, concise, and accurate analysis based on the user's request."
                },
                {
                    "role": "user",
                    "content": f"Here is a YouTube video transcript:\n\n{transcript}\n\nUser request: {prompt}"
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500


@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """Get all saved prompts"""
    try:
        prompts = load_prompts()
        return jsonify({
            'success': True,
            'prompts': prompts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/prompts', methods=['POST'])
def save_prompt_api():
    """Create or update a prompt"""
    try:
        data = request.get_json()
        prompt_id = data.get('id')
        name = data.get('name', '').strip()
        prompt_text = data.get('prompt', '').strip()
        
        if not name or not prompt_text:
            return jsonify({
                'success': False,
                'error': 'Name and prompt text are required'
            }), 400
        
        prompts = load_prompts()
        
        if prompt_id:
            # Update existing prompt
            prompt = next((p for p in prompts if p['id'] == prompt_id), None)
            if prompt:
                prompt['name'] = name
                prompt['prompt'] = prompt_text
            else:
                return jsonify({
                    'success': False,
                    'error': 'Prompt not found'
                }), 404
        else:
            # Create new prompt
            new_id = get_next_prompt_id(prompts)
            prompts.append({
                'id': new_id,
                'name': name,
                'prompt': prompt_text
            })
        
        if save_prompts(prompts):
            return jsonify({
                'success': True,
                'prompts': prompts
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save prompts'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt_api(prompt_id):
    """Delete a prompt"""
    try:
        prompts = load_prompts()
        prompts = [p for p in prompts if p['id'] != prompt_id]
        
        if save_prompts(prompts):
            return jsonify({
                'success': True,
                'prompts': prompts
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save prompts'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parse_subtitle_content(content, include_timestamps=False):
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
                    timestamp = None
                    if include_timestamps and 'tStartMs' in event:
                        # Convert milliseconds to MM:SS format
                        total_seconds = event['tStartMs'] / 1000
                        minutes = int(total_seconds // 60)
                        seconds = int(total_seconds % 60)
                        timestamp = f"[{minutes:02d}:{seconds:02d}]"
                    
                    for seg in event['segs']:
                        if 'utf8' in seg:
                            text = seg['utf8'].strip()
                            # Remove newline characters within segments
                            text = text.replace('\n', ' ')
                            if text:
                                if timestamp:
                                    lines.append(f"{timestamp} {text}")
                                    timestamp = None  # Only add timestamp once per event
                                else:
                                    lines.append(text)
        
        return ' '.join(lines)
    
    except (json.JSONDecodeError, KeyError):
        # Not JSON or different format, try VTT/SRT parsing
        pass
    
    # Parse VTT or SRT format
    current_timestamp = None
    for line in content.split('\n'):
        line = line.strip()
        
        # Check for timestamp line
        if '-->' in line and include_timestamps:
            # Extract start time (format: 00:00:15.000 --> 00:00:18.000)
            match = re.match(r'(\d{2}):(\d{2}):(\d{2})', line)
            if match:
                hours, minutes, seconds = match.groups()
                # Convert to MM:SS format
                total_minutes = int(hours) * 60 + int(minutes)
                current_timestamp = f"[{total_minutes:02d}:{seconds}]"
            continue
        
        # Skip empty lines and VTT headers
        if not line or line.startswith('WEBVTT') or line.isdigit():
            continue
        
        # Skip lines that are just timestamps
        if re.match(r'^\d{2}:\d{2}:\d{2}', line):
            continue
        
        # Remove HTML tags
        line = re.sub(r'<[^>]+>', '', line)
        
        if line:
            if include_timestamps and current_timestamp:
                lines.append(f"{current_timestamp} {line}")
                current_timestamp = None  # Only add timestamp once
            else:
                lines.append(line)
    
    return '\n'.join(lines)


if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Transcript Downloader with AI Analysis")
    print("=" * 60)
    print(f"Server starting on http://192.168.44.11:8000")
    
    # Check if OpenAI API key is set
    if os.getenv('OPENAI_API_KEY'):
        print("✓ OpenAI API key configured")
    else:
        print("⚠ WARNING: OpenAI API key not configured")
        print("  Set OPENAI_API_KEY environment variable to enable AI features")
    
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=False)
