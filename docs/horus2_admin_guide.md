# horus2 Administration Guide

**Hostname:** horus2.justice.lan  
**IP Address:** 192.168.44.11  
**OS:** Ubuntu Server 24.04.3 LTS (ARM64)  
**Architecture:** Raspberry Pi

## Installed Services

### Pi-hole FTL (Secondary DNS)
- **Port:** 53 (DNS), 80 (Web UI)
- **Web UI:** http://192.168.44.11/admin
- **Role:** Secondary DNS resolver with ad-blocking
- **Syncs from:** horus1 (192.168.44.10) every hour

### YouTube Transcript Downloader
- **Port:** 8000
- **Web UI:** http://192.168.44.11:8000
- **Service:** youtube-transcript
- **Path:** /opt/youtube-transcript/

## Service Management

### YouTube Transcript
```bash
sudo systemctl start youtube-transcript
sudo systemctl stop youtube-transcript
sudo systemctl restart youtube-transcript
sudo systemctl status youtube-transcript
```

### Pi-hole
```bash
sudo systemctl restart pihole-FTL
pihole status
pihole -g  # Update gravity
```

## Firewall (UFW)
```bash
sudo ufw status
sudo ufw allow 8000/tcp
```

## System Maintenance
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Check disk space
df -h

# View logs
sudo journalctl -u youtube-transcript -f
```
