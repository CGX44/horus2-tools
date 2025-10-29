# YouTube Transcript Downloader

Web application to extract transcripts from YouTube videos.

## Features
- Extract transcripts from any YouTube video
- Display video title and channel name
- Copy transcript to clipboard
- Show word count, character count, and duration

## Installation

### Prerequisites
- Python 3.12+
- pip

### Setup
```bash
cd /opt/youtube-transcript
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run as Service
```bash
sudo cp youtube-transcript.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable youtube-transcript
sudo systemctl start youtube-transcript
```

## Usage
Access at: http://192.168.44.11:8000

## API Endpoint
POST /api/transcript
- Input: `{"url": "https://youtube.com/watch?v=..."}`
- Output: `{"success": true, "transcript": "...", "title": "...", "channel": "..."}`

## Configuration

### Setting up OpenAI API Key

1. Get your API key from https://platform.openai.com/api-keys
2. Edit the systemd service file:
```bash
   sudo nano /etc/systemd/system/youtube-transcript.service
```
3. Update the Environment line with your actual key:
```ini
   Environment="OPENAI_API_KEY=sk-your-actual-key-here"
```
4. Reload and restart:
```bash
   sudo systemctl daemon-reload
   sudo systemctl restart youtube-transcript
```

**Important:** Never commit your actual API key to the repository!
