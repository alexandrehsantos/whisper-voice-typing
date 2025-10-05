#!/usr/bin/env python3

import subprocess
import sys
import tempfile
import os
import signal
import threading
import time
import wave
import struct
import math
import fcntl

try:
    from faster_whisper import WhisperModel
    from pynput import keyboard
    import pyaudio
except ImportError as e:
    print(f"Missing required dependency: {e.name}")
    print("Please install dependencies: pip install faster-whisper pynput pyaudio")
    sys.exit(1)


# Audio configuration constants
CHUNK_SIZE = 8192
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
SILENCE_THRESHOLD_RMS = 400
SILENCE_DURATION_SECONDS = 5.0
MAX_RECORDING_DURATION_SECONDS = 3600
MIN_VALID_TRANSCRIPTION_LENGTH = 3
TYPING_DELAY_SECONDS = 0.3
MIN_RECORDING_DURATION_SECONDS = 0.5


class VoiceDaemon:
    def __init__(self, model_size="small", hotkey="<ctrl>+<alt>+v", use_ydotool=False, model_cache_dir=None):
        self.model_size = model_size
        self.hotkey = hotkey
        self.use_ydotool = use_ydotool
        self.model_cache_dir = model_cache_dir or "/mnt/development/.whisper-cache"
        self.model = None
        self.is_recording = False
        self.recording_thread = None
        self.pid_file = "/tmp/voice-daemon.pid"

        # Audio settings for VAD
        self.CHUNK = CHUNK_SIZE
        self.FORMAT = AUDIO_FORMAT
        self.CHANNELS = CHANNELS
        self.RATE = SAMPLE_RATE
        self.SILENCE_THRESHOLD = SILENCE_THRESHOLD_RMS
        self.SILENCE_DURATION = SILENCE_DURATION_SECONDS
        self.MAX_RECORDING_TIME = MAX_RECORDING_DURATION_SECONDS

    def initialize_model(self):
        if self.model is None:
            # Create cache directory if it doesn't exist
            os.makedirs(self.model_cache_dir, exist_ok=True)

            print(f"[Voice Daemon] Loading Whisper {self.model_size} model...")
            print(f"[Voice Daemon] Cache dir: {self.model_cache_dir}")

            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                num_workers=4,
                download_root=self.model_cache_dir
            )
            print(f"[Voice Daemon] ✓ Model loaded!")

    def get_rms(self, data):
        """Calculate RMS (volume) of audio chunk"""
        count = len(data) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, data)
        sum_squares = sum([sample ** 2 for sample in shorts])
        rms = math.sqrt(sum_squares / count)
        return rms

    def record_audio(self):
        """Record audio until silence is detected"""
        audio = pyaudio.PyAudio()

        try:
            # Get sample width early before stream closes
            sample_width = audio.get_sample_size(self.FORMAT)

            stream = audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            print("[Voice Daemon] 🎤 Fale agora...")
            self.show_notification("Voice Input", "🎤 Fale agora...", "low")

            frames = []
            silence_chunks = 0
            max_silence_chunks = int(self.SILENCE_DURATION * self.RATE / self.CHUNK)
            started_speaking = False
            min_recording_chunks = int(MIN_RECORDING_DURATION_SECONDS * self.RATE / self.CHUNK)

            try:
                while True:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)

                    rms = self.get_rms(data)

                    if rms > self.SILENCE_THRESHOLD:
                        started_speaking = True
                        silence_chunks = 0
                        print(".", end="", flush=True)
                    else:
                        if started_speaking:
                            silence_chunks += 1

                    if started_speaking and silence_chunks > max_silence_chunks:
                        if len(frames) > min_recording_chunks:
                            print(f"\n[Voice Daemon] Silêncio detectado após {self.SILENCE_DURATION}s")
                            break

                    # Check max recording time
                    if len(frames) > int(self.MAX_RECORDING_TIME * self.RATE / self.CHUNK):
                        print(f"\n[Voice Daemon] Tempo máximo atingido ({self.MAX_RECORDING_TIME}s)")
                        break

            except KeyboardInterrupt:
                pass
            finally:
                stream.stop_stream()
                stream.close()
        finally:
            audio.terminate()

        if not started_speaking:
            return None

        # Use secure temporary file creation
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            output_file = temp_file.name

        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(sample_width)
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))

        duration = len(frames) * self.CHUNK / self.RATE
        print(f"[Voice Daemon] Gravado: {duration:.1f}s")

        return output_file

    def transcribe(self, audio_file):
        """Transcribe audio file to text"""
        self.initialize_model()

        segments, info = self.model.transcribe(
            audio_file,
            language="pt",
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.3,  # Lower threshold - more sensitive
                "min_speech_duration_ms": 200,  # Minimum 200ms of speech
                "min_silence_duration_ms": 500,  # 500ms silence = end of speech
                "speech_pad_ms": 400  # Add padding around speech
            }
        )

        text = " ".join([segment.text.strip() for segment in segments])
        return text.strip()

    def type_text_ydotool(self, text):
        """Type text using ydotool (works with Wayland and X11)"""
        if not text:
            return

        try:
            # Check if ydotool is available
            subprocess.run(["which", "ydotool"], check=True, capture_output=True)

            # Small delay
            time.sleep(TYPING_DELAY_SECONDS)

            # Type the text
            subprocess.run(
                ["ydotool", "type", text],
                check=True
            )

            # Press Enter
            subprocess.run(["ydotool", "key", "28:1", "28:0"], check=True)

            print(f"[Voice Daemon] ✓ Typed (ydotool): {text[:50]}...")
            return True

        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def type_text_xdotool(self, text):
        """Type text using xdotool (X11 only)"""
        if not text:
            return

        try:
            time.sleep(TYPING_DELAY_SECONDS)

            subprocess.run(
                ["xdotool", "type", "--delay", "10", "--", text],
                check=True
            )

            subprocess.run(["xdotool", "key", "Return"], check=True)

            print(f"[Voice Daemon] ✓ Typed (xdotool): {text[:50]}...")
            return True

        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def type_text(self, text):
        """Type text using available tool"""
        # Always try xdotool first (more reliable)
        if not self.type_text_xdotool(text):
            print("[Voice Daemon] ⚠️  xdotool failed, trying ydotool")
            if not self.type_text_ydotool(text):
                print("[Voice Daemon] ✗ Both xdotool and ydotool failed")
                # Fallback: copy to clipboard
                try:
                    subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True, timeout=5)
                    print("[Voice Daemon] ✓ Copied to clipboard as fallback")
                except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
                    print(f"[Voice Daemon] ✗ All typing methods failed: {e}")

    def show_notification(self, title, message, urgency="normal"):
        """Show desktop notification"""
        try:
            subprocess.run(
                ["notify-send", "-u", urgency, title, message],
                check=False,
                timeout=5
            )
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            # Notifications are non-critical, silently continue
            pass

    def process_voice_input(self):
        """Process voice input in a separate thread"""
        if self.is_recording:
            return

        self.is_recording = True

        def record_and_transcribe():
            try:
                audio_file = self.record_audio()

                if audio_file:
                    print("[Voice Daemon] 🔄 Transcribing...")
                    self.show_notification("Voice Input", "🔄 Transcribing...", "low")

                    text = self.transcribe(audio_file)
                    os.unlink(audio_file)

                    if text and len(text) > MIN_VALID_TRANSCRIPTION_LENGTH:
                        print(f"[Voice Daemon] 📝 Transcribed: {text}")
                        self.type_text(text)
                        self.show_notification("Voice Input", f"✓ {text[:50]}", "normal")
                    else:
                        print("[Voice Daemon] ⚠️  Nenhuma fala detectada")
                        self.show_notification("Voice Input", "⚠️ Nenhuma fala detectada", "normal")
                else:
                    print("[Voice Daemon] ⚠️  Sem áudio gravado")
                    self.show_notification("Voice Input", "⚠️ Nenhuma fala detectada", "normal")

            except Exception as e:
                print(f"[Voice Daemon] ✗ Error: {e}")
                self.show_notification("Voice Input", f"✗ Error: {str(e)}", "critical")
            finally:
                self.is_recording = False

        self.recording_thread = threading.Thread(target=record_and_transcribe)
        self.recording_thread.start()

    def on_activate(self):
        """Called when hotkey is pressed"""
        print(f"[Voice Daemon] Hotkey triggered!")
        self.process_voice_input()

    def write_pid(self):
        """Write PID to file with exclusive lock to prevent multiple instances"""
        try:
            self.pid_file_handle = open(self.pid_file, 'w')
            fcntl.flock(self.pid_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.pid_file_handle.write(str(os.getpid()))
            self.pid_file_handle.flush()
        except BlockingIOError:
            print(f"[Voice Daemon] Another instance is already running (PID file locked)")
            sys.exit(1)
        except OSError as e:
            print(f"[Voice Daemon] Failed to create PID file: {e}")
            sys.exit(1)

    def remove_pid(self):
        """Remove PID file and release lock"""
        try:
            if hasattr(self, 'pid_file_handle') and self.pid_file_handle:
                fcntl.flock(self.pid_file_handle.fileno(), fcntl.LOCK_UN)
                self.pid_file_handle.close()
            os.unlink(self.pid_file)
        except OSError:
            # PID file may not exist, continue
            pass

    def start(self):
        """Start the daemon"""
        self.write_pid()

        # Detect which tool to use
        try:
            subprocess.run(["which", "ydotool"], check=True, capture_output=True)
            self.use_ydotool = True
            tool_name = "ydotool (Wayland/X11)"
        except:
            tool_name = "xdotool (X11)"

        print("=" * 60)
        print("🎙️  Voice Input Daemon Started (VAD Mode)")
        print("=" * 60)
        print(f"Hotkey: {self.hotkey}")
        print(f"Model: Whisper {self.model_size}")
        print(f"Typing tool: {tool_name}")
        print(f"Mode: Detecção de silêncio (para quando você parar)")
        print(f"Silêncio: 5.0 segundos")
        print(f"Máximo: 1 HORA de gravação contínua")
        print(f"Buffer: 8192 chunks (otimizado para 64GB RAM)")
        print(f"PID: {os.getpid()}")
        print("=" * 60)
        print("\nPressione hotkey e FALE - para automaticamente após 5s de silêncio")
        print("Você pode falar por ATÉ 1 HORA continuamente!")
        print("Press Ctrl+C to stop the daemon\n")

        # Initialize model on startup
        self.initialize_model()

        self.show_notification(
            "Voice Daemon (VAD)",
            f"✓ Pressione {self.hotkey} e fale - para quando você parar de falar",
            "normal"
        )

        # Set up hotkey listener
        try:
            with keyboard.GlobalHotKeys({
                self.hotkey: self.on_activate
            }) as listener:
                listener.join()
        except KeyboardInterrupt:
            print("\n[Voice Daemon] Stopping...")
        finally:
            self.remove_pid()
            self.show_notification("Voice Daemon", "Stopped", "low")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Voice Input Daemon for Linux")
    parser.add_argument(
        "-m", "--model",
        default="small",
        choices=["tiny", "base", "small", "medium"],
        help="Whisper model size (default: small for better accuracy)"
    )
    parser.add_argument(
        "-k", "--hotkey",
        default="<ctrl>+<alt>+v",
        help="Global hotkey (default: Ctrl+Alt+V)"
    )
    parser.add_argument(
        "--ydotool",
        action="store_true",
        help="Force use of ydotool instead of xdotool"
    )

    args = parser.parse_args()

    daemon = VoiceDaemon(model_size=args.model, hotkey=args.hotkey, use_ydotool=args.ydotool)

    # Handle signals
    def signal_handler(sig, frame):
        daemon.remove_pid()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    daemon.start()


if __name__ == "__main__":
    main()
