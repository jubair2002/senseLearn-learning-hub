"""
Text-to-Speech service for chatbot.
Converts text to audio files.
"""
import os
from typing import Optional
from flask import current_app
from src.config import config


class TTSService:
    """Service for converting text to speech."""
    
    @staticmethod
    def text_to_speech(text: str, output_path: str, language: str = 'en') -> bool:
        """
        Convert text to speech and save as audio file.
        
        Args:
            text: Text to convert to speech
            output_path: Full path where audio file should be saved
            language: Language code (default: 'en')
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            current_app.logger.warning("Empty text provided for TTS")
            return False
        
        # Clean and prepare text for TTS
        # Remove excessive whitespace and normalize
        text = ' '.join(text.split())
        # Limit text length (gTTS has a limit of ~5000 characters per request)
        max_length = 4500  # Leave some buffer
        if len(text) > max_length:
            text = text[:max_length] + "... [Text truncated for audio generation]"
            current_app.logger.info(f"Text truncated from {len(text)} to {max_length} characters for TTS")
        
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Try gTTS (Google Text-to-Speech) first - requires internet
            try:
                from gtts import gTTS
                current_app.logger.info(f"Attempting to generate audio using gTTS for {len(text)} characters")
                tts = gTTS(text=text, lang=language, slow=False)
                tts.save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    current_app.logger.info(f"Audio file created successfully using gTTS: {output_path} ({os.path.getsize(output_path)} bytes)")
                    return True
                else:
                    current_app.logger.warning(f"gTTS created file but it's empty or doesn't exist: {output_path}")
                    # Try pyttsx3 as fallback
                    raise Exception("gTTS file creation failed")
            except ImportError as e:
                current_app.logger.warning(f"gTTS not available: {str(e)}. Trying pyttsx3...")
            except Exception as e:
                current_app.logger.error(f"Error with gTTS: {str(e)}. Trying pyttsx3...")
            
            # Fallback to pyttsx3 (offline, but requires system TTS)
            try:
                import pyttsx3
                current_app.logger.info(f"Attempting to generate audio using pyttsx3 for {len(text)} characters")
                engine = pyttsx3.init()
                
                # Set properties (optional)
                engine.setProperty('rate', 150)  # Speed of speech
                engine.setProperty('volume', 0.9)  # Volume level
                
                # Save to file
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                
                # Wait a bit for file to be written
                import time
                time.sleep(0.5)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    current_app.logger.info(f"Audio file created successfully using pyttsx3: {output_path} ({os.path.getsize(output_path)} bytes)")
                    return True
                else:
                    current_app.logger.error(f"pyttsx3 did not create audio file or file is empty: {output_path}")
                    return False
            except ImportError as e:
                current_app.logger.error(f"pyttsx3 not available: {str(e)}")
                return False
            except Exception as e:
                current_app.logger.error(f"Error with pyttsx3: {str(e)}")
                return False
        except Exception as e:
            current_app.logger.error(f"Error converting text to speech: {str(e)}")
            return False
    
    @staticmethod
    def get_audio_url(audio_path: str) -> str:
        """Get URL for accessing an audio file."""
        # Convert backslashes to forward slashes for URLs
        normalized_path = audio_path.replace("\\", "/")
        return f"/uploads/{normalized_path}"

