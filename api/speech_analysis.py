import whisper
import re
import os
import tempfile
import json
import requests
import shutil
import subprocess

# Configuration
FILLERS = ["um", "uh", "like", "you know", "actually", "basically", "so", "well", "kind of"]

# Specify ffmpeg path (update this to your ffmpeg.exe location if not in PATH)
FFMPEG_PATH = r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe"  # Example: Update with your actual path

def check_ffmpeg():
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, text=True, check=True)
        print(f"✅ FFmpeg found: {result.stdout.splitlines()[0]}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ FFmpeg not found: {e}")
        return False

def compute_metrics(transcript, duration_s):
    """Compute speech metrics"""
    if not transcript or any(msg in transcript for msg in [
        "No speech detected", "Processing error", "Speech recognition error", 
        "Could not understand audio", "service unavailable", "Audio conversion failed"
    ]):
        return {
            "wpm": 0,
            "filler_pct": 0,
            "duration_s": max(5.0, round(duration_s, 1)),
            "word_count": 0,
        }
    
    words = transcript.split()
    n_words = len(words)
    
    # Improved duration validation
    if duration_s < 1.0:
        duration_s = max(3.0, n_words / 3)
    
    wpm = (n_words / duration_s) * 60 if duration_s > 0 else 0

    # Count filler words
    filler_count = 0
    transcript_lower = transcript.lower()
    for filler in FILLERS:
        filler_count += transcript_lower.count(filler)

    filler_pct = (filler_count / n_words) * 100 if n_words > 0 else 0

    wpm = min(wpm, 300)

    return {
        "wpm": round(wpm, 1),
        "filler_pct": round(filler_pct, 1),
        "duration_s": round(duration_s, 1),
        "word_count": n_words,
    }

def rule_based_hints(metrics, transcript):
    """Generate helpful hints based on metrics"""
    hints = []
    
    if metrics["word_count"] < 10:
        hints.append("Speak longer - aim for 20-40 seconds with detailed examples")
    elif metrics["word_count"] < 25:
        hints.append("Good start - try adding more specific details and outcomes")
    elif metrics["word_count"] > 80:
        hints.append("Excellent detail - very comprehensive answer")
    
    if metrics["wpm"] > 200:
        hints.append("Speaking very fast - slow down for better clarity and impact")
    elif metrics["wpm"] > 160:
        hints.append("Speaking a bit fast - try a more moderate pace")
    elif metrics["wpm"] < 100:
        hints.append("Speaking slowly - increase your pace for better engagement")
    elif 120 <= metrics["wpm"] <= 150:
        hints.append("Excellent speaking pace - perfect for interviews")
    
    if metrics["filler_pct"] > 8:
        hints.append("Many filler words - practice using intentional pauses instead")
    elif metrics["filler_pct"] > 4:
        hints.append("Some filler words - becoming more aware will help reduce them")
    elif metrics["filler_pct"] < 2 and metrics["word_count"] > 10:
        hints.append("Excellent - very few filler words")
    
    star_indicators = [
        "situation", "task", "action", "result", 
        "challenge", "goal", "implemented", "outcome",
        "because", "so that", "led to", "impact"
    ]
    found_indicators = sum(1 for word in star_indicators if word in transcript.lower())
    
    if found_indicators >= 3:
        hints.append("Good STAR method structure")
    elif found_indicators >= 1 and metrics["word_count"] > 15:
        hints.append("Try using STAR method: Situation, Task, Action, Result")
    elif metrics["word_count"] > 20:
        hints.append("Consider structuring with STAR: describe the situation, your task, actions taken, and results")
    
    return hints if hints else ["Good communication skills - continue practicing!"]

def transcribe_webm_direct(webm_path):
    """
    Transcribe WebM audio using Whisper
    """
    print(f"🎯 Direct WebM transcription with Whisper: {webm_path}")
    
    # Check if ffmpeg is available
    if not check_ffmpeg():
        raise FileNotFoundError("FFmpeg is not installed or not found in PATH. Please install FFmpeg or specify its path.")
    
    # Verify file exists
    if not os.path.exists(webm_path):
        raise FileNotFoundError(f"Audio file not found: {webm_path}")
    
    try:
        # Load Whisper model (use 'base' for faster processing on CPU)
        model = whisper.load_model("base")  # You can use 'tiny', 'small', 'medium', or 'large' depending on resources
        
        # Transcribe audio
        result = model.transcribe(webm_path, fp16=False)  # fp16=False for CPU compatibility
        transcript = result["text"].strip()
        duration = result["segments"][-1]["end"] if result["segments"] else 5.0
        
        print(f"⏱️ Audio duration: {duration}s")
        print(f"✅ SUCCESS: {transcript}")
        
        return transcript, duration
            
    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        raise

def transcribe(audio_path):
    """
    Main transcription function with robust WebM handling
    """
    print(f"🎯 Processing: {audio_path}")
    
    # Handle WebM files with Whisper
    if audio_path.endswith('.webm'):
        try:
            transcript, duration = transcribe_webm_direct(audio_path)
            
            metrics = compute_metrics(transcript, duration)
            hints = rule_based_hints(metrics, transcript)
            
            return {
                "transcript": transcript,
                "metrics": metrics,
                "hints": hints
            }
            
        except Exception as e:
            print(f"❌ All transcription methods failed: {e}")
            
            # Provide detailed error information
            file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
            estimated_duration = file_size / 10000
            
            return {
                "transcript": f"Speech recognition failed. Please ensure you're speaking clearly for 10+ seconds. (File: {file_size} bytes, ~{estimated_duration:.1f}s)",
                "metrics": {"wpm": 0, "filler_pct": 0, "duration_s": estimated_duration, "word_count": 0},
                "hints": [
                    "Speak clearly for 10-20 seconds",
                    "Ensure good microphone quality", 
                    "Record in a quiet environment",
                    "Ensure FFmpeg is installed and accessible",
                    f"Current recording: ~{estimated_duration:.1f} seconds"
                ]
            }
    
    # For non-WebM files (shouldn't happen with our setup)
    return {
        "transcript": "Unsupported audio format",
        "metrics": {"wpm": 0, "filler_pct": 0, "duration_s": 5, "word_count": 0},
        "hints": ["Technical error - unsupported format"]
    }