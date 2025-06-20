# 🦇 BattyBot

**BattyBot** is a feature-rich Discord bot written in Python. It combines music playback using FFmpeg with core moderation tools to help manage and entertain your Discord server.

---

## 🎵 Features

### 🎧 Music

- Play music from YouTube or other sources
- Pause, resume, skip, and stop playback
- Queue and loop support
- Uses **FFmpeg** for audio streaming

### 🔨 Moderation

- Kick, ban, mute, and unmute members
- Message purge (bulk delete)
- Role-based permission checks
- Logs moderation actions (optional)

---

## 📂 Project Structure

battybot/  
├── bot.py # Main entry point   
├── controls.py # Music and command controls    
├── state.py # Tracks playback and queue states    
├── ffmpeg # FFmpeg binary or configs   
├── README.md # Project overview    
└── pycache/ # Python bytecode cache    

## ⚙️ Requirements

- Python 3.8+
- FFmpeg installed and available in system PATH
- A Discord bot token
- YouTube-dl or yt-dlp (for music downloads)
