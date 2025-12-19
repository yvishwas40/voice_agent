import asyncio
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import tempfile
import edge_tts
from faster_whisper import WhisperModel
from .logger import logger

# Suppress pygame banner
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


class VoiceInterface:
    def __init__(self, input_lang: str = "te", output_voice: str = "te-IN-ShrutiNeural"):
        self.input_lang = input_lang or "te"
        self.output_voice = output_voice
        self.sample_rate = 16000
        self.channels = 1
        # Short window for responsiveness; increase if needed
        self.duration = 4

        self.model: WhisperModel | None = None
        self._load_model()

        # Init pygame mixer for audio playback
        try:
            pygame.mixer.init()
        except Exception as e:
            logger.warning(f"Audio Output setup failed: {e}")

    def _load_model(self):
        """
        Load Whisper model for Telugu recognition.
        Strategy:
        - Prefer 'small' with int8 for better accuracy.
        - Fallback to 'tiny' if 'small' is unavailable.
        """
        try:
            logger.info("[INIT] Loading Whisper Model (small, int8, Telugu)...")
            self.model = WhisperModel("small", device="cpu", compute_type="int8")
            logger.info("[INIT] Whisper (small, int8) Loaded.")
        except Exception as e:
            logger.warning(f"Failed to load 'small' model: {e}. Falling back to 'tiny'.")
            try:
                logger.info("[INIT] Loading Whisper Model (tiny, int8, Telugu)...")
                self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
                logger.info("[INIT] Whisper (tiny, int8) Loaded.")
            except Exception as e2:
                logger.critical(f"All Whisper models failed: {e2}")
                self.model = None

    def listen_with_quality(self) -> tuple[str, float]:
        """
        Records audio for fixed duration and transcribes using Whisper.
        Returns (transcript_text, quality_score) where quality is in [0,1].
        """
        if not self.model:
            logger.error("Whisper Model missing. Check logs for load failure.")
            return "", 0.0

        logger.info(f"[LISTENING] Recording for {self.duration} seconds...")

        try:
            num_samples = int(self.duration * self.sample_rate)
            recording = sd.rec(
                num_samples,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
            )
            sd.wait()

            # Quick energy check to ignore pure silence / very low audio
            audio_float = recording.astype("float32") / 32768.0
            energy = float(np.mean(np.abs(audio_float)))
            if energy < 0.002:
                logger.info("[LISTENING] Detected near-silence, ignoring turn.")
                return "", 0.0

            logger.info("[PROCESSING] Transcribing with Whisper (Telugu)...")

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_path = temp_file.name
            temp_file.close()

            wav.write(temp_path, self.sample_rate, recording)

            # Domain prompt to bias towards govt schemes
            keywords_prompt = (
                "నమస్కారం, తెలంగాణ ప్రభుత్వం సంక్షేమ పథకాలు, రైతు బంధు, ఆసరా పెన్షన్, "
                "కళ్యాణ లక్ష్మి, విత్తనాలు, ఎకరాలు, ఆదాయం, వయస్సు."
            )
            segments, info = self.model.transcribe(
                temp_path,
                beam_size=3,
                language=self.input_lang,
                initial_prompt=keywords_prompt,
                condition_on_previous_text=False,
                vad_filter=True,
            )

            text_blocks = []
            for segment in segments:
                text_blocks.append(segment.text)

            final_text = " ".join(text_blocks).strip()

            quality = 0.0
            if final_text:
                # language_probability is in [0,1]
                lang_prob = getattr(info, "language_probability", 0.0) or 0.0
                telugu_chars = [
                    ch for ch in final_text
                    if "\u0c00" <= ch <= "\u0c7f"
                ]
                ratio = len(telugu_chars) / max(len(final_text), 1)
                quality = float(lang_prob) * float(ratio)

                logger.info(
                    f"[USER][Whisper] text='{final_text}' "
                    f"(lang_prob={lang_prob:.2f}, te_ratio={ratio:.2f}, quality={quality:.2f})"
                )

            if os.path.exists(temp_path):
                os.remove(temp_path)

            return final_text, quality

        except Exception as e:
            logger.error(f"Audio/Transcription Error (Whisper): {e}")
            return "", 0.0

    def listen(self) -> str:
        """
        Backwards-compatible wrapper: just return text.
        """
        text, _ = self.listen_with_quality()
        return text

    async def speak(self, text: str):
        """
        Converts text to speech and plays it using pygame.
        Uses Edge TTS neural Telugu voice.
        Optimized for faster response - TTS generation happens in background.
        """
        if not text:
            return

        logger.info(f"[AGENT]: {text}")

        communicate = edge_tts.Communicate(text, self.output_voice)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        temp_file.close()

        try:
            # Generate TTS asynchronously (already async, no blocking)
            await communicate.save(temp_path)

            # Play using Pygame (non-blocking start)
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Optimized wait - check more frequently initially for faster response
            # Reduced initial wait time from 100ms to 50ms for better responsiveness
            check_count = 0
            while pygame.mixer.music.get_busy():
                # Check more frequently at start (every 50ms), then less frequently
                if check_count < 10:
                    await asyncio.sleep(0.05)  # 50ms for first 500ms - faster response
                else:
                    await asyncio.sleep(0.1)   # 100ms after that
                check_count += 1

            # Unload to release file lock
            pygame.mixer.music.unload()

        except Exception as e:
            logger.error(f"TTS Playback Error: {e}")
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
