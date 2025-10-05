# Whisper Voice Typing

Voice-to-text input daemon for Linux using OpenAI Whisper. Press a hotkey, speak, and have your words typed automatically in any application.

## Features

- **Voice Activity Detection (VAD)**: Automatically detects when you stop speaking
- **Local Processing**: All transcription happens offline using Whisper
- **System-wide Hotkey**: Works in any application (default: Ctrl+Alt+V)
- **Long Recording Support**: Record up to 1 hour continuously
- **Multiple Input Methods**: Supports xdotool, ydotool, and clipboard fallback
- **Systemd Integration**: Runs as a background service
- **Optimized Performance**: Efficient memory usage and fast transcription

## Requirements

- Python 3.8+
- Linux with ALSA audio support
- 2GB+ RAM (8GB+ recommended for longer recordings)
- Microphone

## Installation

### 1. Install System Dependencies

```bash
# Debian/Ubuntu
sudo apt install python3-pyaudio portaudio19-dev xdotool

# Arch Linux
sudo pacman -S python-pyaudio portaudio xdotool

# Fedora
sudo dnf install python3-pyaudio portaudio-devel xdotool
```

### 2. Install Python Dependencies

```bash
pip install faster-whisper pynput pyaudio
```

### 3. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/whisper-voice-typing.git
cd whisper-voice-typing
```

### 4. Install Service

```bash
./install.sh
```

## Usage

### Start Service

```bash
systemctl --user start voice-daemon
```

### Use Voice Input

1. Press **Ctrl+Alt+V** in any application
2. Speak your text (up to 1 hour)
3. Stop speaking and wait 5 seconds
4. Text will be typed automatically

### Stop Service

```bash
systemctl --user stop voice-daemon
```

### View Logs

```bash
journalctl --user -u voice-daemon -f
```

## Configuration

### Change Hotkey

Edit the systemd service file:

```bash
nano ~/.config/systemd/user/voice-daemon.service
```

Modify the `ExecStart` line:

```ini
ExecStart=/usr/bin/python3 /path/to/voice-daemon.py -k "<ctrl>+<shift>+v"
```

Reload and restart:

```bash
systemctl --user daemon-reload
systemctl --user restart voice-daemon
```

### Change Whisper Model

Available models (smallest to largest):
- `tiny`: Fastest, least accurate
- `base`: Good balance (default)
- `small`: Better accuracy
- `medium`: Best accuracy (slower)

```bash
# Edit service file
nano ~/.config/systemd/user/voice-daemon.service

# Change -m parameter
ExecStart=/usr/bin/python3 /path/to/voice-daemon.py -m medium
```

### Adjust Voice Detection

Edit `/path/to/voice-daemon.py`:

```python
# Increase for less sensitive detection (default: 400)
SILENCE_THRESHOLD_RMS = 500

# Increase to wait longer before stopping (default: 5.0)
SILENCE_DURATION_SECONDS = 7.0
```

## Architecture

The daemon uses:

- **PyAudio**: Audio capture from microphone
- **faster-whisper**: Optimized Whisper inference
- **pynput**: Global hotkey detection
- **xdotool/ydotool**: System-wide keyboard input simulation

### Audio Processing Pipeline

1. Hotkey press triggers recording
2. Audio captured in 8192-sample chunks
3. RMS amplitude calculated per chunk for VAD
4. Recording continues until silence detected
5. Audio saved to temporary WAV file
6. Whisper transcribes to text
7. Text typed via xdotool/ydotool
8. Temporary file cleaned up

## Performance

### Benchmark (Intel i5, 16GB RAM, Whisper Small)

- **Recording latency**: <50ms
- **Transcription speed**: ~2-3 seconds for 10-second audio
- **Memory usage**: ~500MB (model + daemon)
- **CPU usage**: 5-10% idle, 30-50% during transcription

### Memory Usage by Recording Length

| Duration | Memory (approx) |
|----------|----------------|
| 1 minute | ~10 MB        |
| 10 minutes | ~100 MB     |
| 1 hour | ~600 MB       |

## Troubleshooting

### Microphone Not Detected

```bash
# List audio devices
arecord -l

# Test recording
arecord -d 3 test.wav && aplay test.wav
```

### Hotkey Not Working

Check if another instance is running:

```bash
systemctl --user status voice-daemon
ps aux | grep voice-daemon
```

### Poor Transcription Quality

1. Use a larger model (`small` or `medium`)
2. Ensure quiet environment
3. Speak clearly and not too fast
4. Adjust `SILENCE_THRESHOLD_RMS` if voice not detected

### xdotool Fails on Wayland

Install ydotool for Wayland support:

```bash
sudo apt install ydotool
sudo systemctl enable --now ydotool
```

## Development

### Run in Foreground (Debug Mode)

```bash
python3 voice-daemon.py
```

### Run Tests

```bash
pytest tests/
```

### Code Structure

```
voice-daemon.py
├── Audio Constants (lines 25-35)
├── VoiceDaemon Class
│   ├── __init__: Configuration
│   ├── initialize_model: Load Whisper model
│   ├── record_audio: Capture and detect voice
│   ├── get_rms: Calculate audio amplitude
│   ├── transcribe: Speech-to-text conversion
│   ├── type_text_*: Keyboard input methods
│   ├── process_voice_input: Main workflow
│   └── start: Daemon entry point
```

## Security

- All processing happens locally (no cloud services)
- PID file locking prevents multiple instances
- Temporary files use secure creation (`NamedTemporaryFile`)
- No automatic dependency installation
- Proper resource cleanup on exit

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the existing code style
4. Test your changes: `python3 voice-daemon.py`
5. Commit: `git commit -m "Add feature: description"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

### Code Style
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

### Areas Needing Help
- Multi-language support configuration
- Performance optimizations
- Documentation improvements
- Bug fixes and testing

## Acknowledgments

- OpenAI Whisper for the speech recognition model
- faster-whisper for optimized inference
- The open-source community

## Support

For issues and questions:
- GitHub Issues: https://github.com/YOUR_USERNAME/whisper-voice-typing/issues
- Documentation: See `/docs` folder

## Roadmap

- [ ] Multi-language support configuration
- [ ] Custom vocabulary/dictionary
- [ ] Punctuation commands
- [ ] Voice commands for editing
- [ ] GUI configuration tool
- [ ] Windows/macOS support
