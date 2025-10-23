# speech_analysis.py - COMPLETE UPDATED VERSION

import whisper
import re
import os
import tempfile
import subprocess
import numpy as np

# Configuration
FILLERS = ["um", "uh", "like", "you know", "actually", "basically", "so", "well", "kind of"]
FFMPEG_PATH = r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe"

# Emotion thresholds (calibrated for interview context)
EMOTION_THRESHOLDS = {
    'pitch_stability_threshold': 0.7,      # Higher = more stable voice
    'energy_variance_threshold': 0.3,      # Lower = more consistent volume
    'speech_rate_threshold_fast': 160,     # WPM for "rushed"
    'speech_rate_threshold_slow': 100,     # WPM for "monotone"
    'pause_frequency_threshold': 0.1,      # Pauses per second
}

def convert_numpy_types(obj):
    """
    Convert numpy data types to Python native types for JSON serialization
    """
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def check_ffmpeg():
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, text=True, check=True)
        print(f"✅ FFmpeg found: {result.stdout.splitlines()[0]}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ FFmpeg not found: {e}")
        return False

def extract_voice_features(audio_path):
    """
    Extract comprehensive voice features for emotion analysis
    """
    print("🎵 Extracting voice features...")
    
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=16000)
        duration = len(y) / sr
        
        # Basic features
        features = {
            'duration_s': duration,
            'rms_energy': float(np.mean(librosa.feature.rms(y=y))),
            'rms_variance': float(np.var(librosa.feature.rms(y=y)[0])),
        }
        
        # Pitch analysis (fundamental frequency)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, 
            fmin=librosa.note_to_hz('C2'), 
            fmax=librosa.note_to_hz('C7'),
            sr=sr
        )
        
        # Pitch features
        if np.any(voiced_flag):
            f0_values = f0[voiced_flag]
            features.update({
                'pitch_mean': float(np.mean(f0_values)),
                'pitch_std': float(np.std(f0_values)),
                'pitch_range': float(np.ptp(f0_values)) if len(f0_values) > 0 else 0.0,
                'pitch_stability': float(1.0 - (np.std(f0_values) / np.mean(f0_values))) if np.mean(f0_values) > 0 else 0.0,
            })
        else:
            # Default values if no pitch detected
            features.update({
                'pitch_mean': 0.0,
                'pitch_std': 0.0,
                'pitch_range': 0.0,
                'pitch_stability': 0.0,
            })
        
        # Spectral features (voice quality)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        
        features.update({
            'spectral_centroid_mean': float(np.mean(spectral_centroid)),
            'spectral_centroid_std': float(np.std(spectral_centroid)),
            'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
        })
        
        # Temporal features (pause analysis)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, delta=0.5)
        features['pause_frequency'] = float(len(onset_frames) / duration if duration > 0 else 0)
        
        # MFCCs (voice characteristics)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features['mfcc_variance'] = float(np.mean(np.var(mfccs, axis=1)))
        
        print(f"✅ Voice features extracted: {len(features)} metrics")
        return convert_numpy_types(features)
        
    except Exception as e:
        print(f"❌ Voice feature extraction failed: {e}")
        # Return default features
        return convert_numpy_types({
            'duration_s': 5.0,
            'pitch_stability': 0.5,
            'rms_variance': 0.5,
            'pause_frequency': 0.1,
            'mfcc_variance': 0.5,
        })

def safe_extract_voice_features(audio_path):
    """
    Safe voice feature extraction with fallback
    """
    try:
        return extract_voice_features(audio_path)
    except Exception as e:
        print(f"⚠️ Voice feature extraction failed, using fallback: {e}")
        # Return basic features that don't require librosa
        return convert_numpy_types({
            'duration_s': 5.0,
            'pitch_stability': 0.5,
            'rms_variance': 0.5,
            'pause_frequency': 0.1,
            'mfcc_variance': 0.5,
        })

def classify_emotion_from_features(features, transcript_metrics):
    """
    Rule-based emotion classification for interview context
    """
    print("🧠 Classifying emotions from voice features...")
    
    # Combine audio features with transcript metrics
    wpm = transcript_metrics.get('wpm', 0)
    filler_pct = transcript_metrics.get('filler_pct', 0)
    word_count = transcript_metrics.get('word_count', 0)
    
    emotion_scores = {
        'confident': 0.0,
        'nervous': 0.0,
        'enthusiastic': 0.0,
        'monotone': 0.0,
        'rushed': 0.0,
    }
    
    # Confidence scoring (positive indicators)
    if features.get('pitch_stability', 0) > EMOTION_THRESHOLDS['pitch_stability_threshold']:
        emotion_scores['confident'] += 0.3
    
    if features.get('rms_variance', 1) < EMOTION_THRESHOLDS['energy_variance_threshold']:
        emotion_scores['confident'] += 0.2
    
    if 120 <= wpm <= 160:  # Ideal interview pace
        emotion_scores['confident'] += 0.2
    
    # Nervousness scoring
    if features.get('pitch_std', 0) > 30:  # High pitch variation
        emotion_scores['nervous'] += 0.3
    
    if wpm > EMOTION_THRESHOLDS['speech_rate_threshold_fast']:
        emotion_scores['nervous'] += 0.2
        emotion_scores['rushed'] += 0.3
    
    if filler_pct > 5:  # High filler words
        emotion_scores['nervous'] += 0.2
    
    # Enthusiasm scoring
    if features.get('rms_energy', 0) > 0.02:  # Good energy level
        emotion_scores['enthusiastic'] += 0.2
    
    if features.get('spectral_centroid_std', 0) > 500:  # Vocal variety
        emotion_scores['enthusiastic'] += 0.2
    
    # Monotone scoring
    if wpm < EMOTION_THRESHOLDS['speech_rate_threshold_slow']:
        emotion_scores['monotone'] += 0.3
    
    if features.get('pitch_range', 0) < 50:  # Limited pitch range
        emotion_scores['monotone'] += 0.2
    
    if features.get('pause_frequency', 0) < 0.05:  # Few pauses
        emotion_scores['monotone'] += 0.1
    
    # Normalize scores
    total = sum(emotion_scores.values())
    if total > 0:
        for emotion in emotion_scores:
            emotion_scores[emotion] = round(emotion_scores[emotion] / total, 2)
    
    # Determine primary emotion
    primary_emotion = max(emotion_scores, key=emotion_scores.get)
    confidence = emotion_scores[primary_emotion]
    
    print(f"✅ Emotion classification: {primary_emotion} (confidence: {confidence})")
    
    emotion_data = {
        'primary_emotion': primary_emotion,
        'confidence_score': confidence,
        'emotion_breakdown': emotion_scores,
        'voice_metrics': {
            'pitch_stability': features.get('pitch_stability', 0),
            'energy_consistency': 1 - features.get('rms_variance', 1),
            'vocal_variety': features.get('spectral_centroid_std', 0) / 1000,
            'pause_effectiveness': features.get('pause_frequency', 0) * 10,
        }
    }
    
    # Convert numpy types to Python native types
    return convert_numpy_types(emotion_data)

def classify_emotion_simple(transcript_metrics):
    """
    Simple emotion classification based only on transcript metrics
    """
    print("🧠 Simple emotion classification...")
    
    wpm = transcript_metrics.get('wpm', 0)
    filler_pct = transcript_metrics.get('filler_pct', 0)
    word_count = transcript_metrics.get('word_count', 0)
    
    emotion_scores = {
        'confident': 0.0,
        'nervous': 0.0,
        'enthusiastic': 0.0,
        'monotone': 0.0,
        'rushed': 0.0,
    }
    
    # Confidence scoring
    if 120 <= wpm <= 160:  # Ideal interview pace
        emotion_scores['confident'] += 0.4
    if filler_pct < 3:  # Low filler words
        emotion_scores['confident'] += 0.3
    if word_count > 30:  # Good content length
        emotion_scores['confident'] += 0.3
    
    # Nervousness scoring
    if wpm > 180:  # Very fast
        emotion_scores['nervous'] += 0.4
        emotion_scores['rushed'] += 0.4
    if filler_pct > 8:  # High filler words
        emotion_scores['nervous'] += 0.4
    
    # Monotone scoring
    if wpm < 100:  # Very slow
        emotion_scores['monotone'] += 0.6
    if word_count < 15:  # Very short answer
        emotion_scores['monotone'] += 0.4
    
    # Enthusiasm scoring
    if word_count > 50:  # Detailed answer
        emotion_scores['enthusiastic'] += 0.3
    if 140 <= wpm <= 170:  # Energetic pace
        emotion_scores['enthusiastic'] += 0.3
    
    # Normalize scores
    total = sum(emotion_scores.values())
    if total > 0:
        for emotion in emotion_scores:
            emotion_scores[emotion] = round(emotion_scores[emotion] / total, 2)
    
    # Determine primary emotion
    primary_emotion = max(emotion_scores, key=emotion_scores.get)
    confidence = emotion_scores[primary_emotion]
    
    print(f"✅ Simple emotion: {primary_emotion} (confidence: {confidence})")
    
    return {
        'primary_emotion': primary_emotion,
        'confidence_score': confidence,
        'emotion_breakdown': emotion_scores,
        'voice_metrics': {
            'speech_pace_score': min(1.0, wpm / 200),
            'content_depth_score': min(1.0, word_count / 60),
            'articulation_score': max(0.0, 1.0 - (filler_pct / 20)),
            'analysis_method': 'transcript_based'
        }
    }

def generate_emotion_hints(emotion_data, transcript_metrics):
    """
    Generate specific coaching hints based on emotions
    """
    primary_emotion = emotion_data['primary_emotion']
    voice_metrics = emotion_data['voice_metrics']
    
    hints = []
    
    if primary_emotion == 'nervous':
        hints.append("🎯 You sound nervous - try taking a deep breath before speaking")
        if voice_metrics.get('pitch_stability', 0) < 0.6:
            hints.append("🎵 Your voice is shaky - practice speaking with steady tone")
        if transcript_metrics.get('wpm', 0) > 170:
            hints.append("⏰ Speaking too fast - slow down for better clarity")
            
    elif primary_emotion == 'confident':
        hints.append("✅ Excellent confidence level!")
        if voice_metrics.get('vocal_variety', 0) < 0.3:
            hints.append("💡 Add more vocal variety to sound engaging")
            
    elif primary_emotion == 'monotone':
        hints.append("🔊 Add more energy and variation to your voice")
        if voice_metrics.get('pause_effectiveness', 0) < 0.5:
            hints.append("⏸️ Use strategic pauses to emphasize key points")
            
    elif primary_emotion == 'rushed':
        hints.append("🐌 Slow down - aim for 140-160 words per minute")
        hints.append("🧘 Practice pausing between thoughts")
        
    elif primary_emotion == 'enthusiastic':
        hints.append("🎉 Great energy and enthusiasm!")
        if transcript_metrics.get('filler_pct', 0) > 3:
            hints.append("🗣️ Reduce filler words to maintain professionalism")
    
    # General voice quality hints
    if voice_metrics.get('energy_consistency', 0) < 0.6:
        hints.append("📢 Maintain consistent volume throughout your answer")
    
    if voice_metrics.get('vocal_variety', 0) < 0.4:
        hints.append("🎭 Vary your pitch and tone to keep listeners engaged")
    
    return hints

def generate_emotion_hints_simple(emotion_data, transcript_metrics):
    """
    Generate coaching hints based on simple emotion analysis
    """
    primary_emotion = emotion_data['primary_emotion']
    wpm = transcript_metrics.get('wpm', 0)
    filler_pct = transcript_metrics.get('filler_pct', 0)
    
    hints = []
    
    if primary_emotion == 'nervous':
        hints.append("🎯 You sound nervous - try taking a deep breath before speaking")
        if wpm > 170:
            hints.append("⏰ Speaking too fast - slow down to 140-160 WPM")
        if filler_pct > 5:
            hints.append("🗣️ High filler words - practice pausing instead of using fillers")
            
    elif primary_emotion == 'confident':
        hints.append("✅ Excellent composure and confidence!")
        if wpm < 130:
            hints.append("💡 Good pace - you could speak slightly faster for more energy")
            
    elif primary_emotion == 'monotone':
        hints.append("🔊 Add more energy and vocal variety")
        if wpm < 100:
            hints.append("🐌 Speaking very slowly - aim for 140-160 WPM")
        hints.append("🎭 Vary your tone to keep the interviewer engaged")
            
    elif primary_emotion == 'rushed':
        hints.append("🚀 Slow down - you're speaking very fast")
        hints.append("⏸️ Use strategic pauses between thoughts")
        hints.append("🧘 Practice taking breaths at natural break points")
        
    elif primary_emotion == 'enthusiastic':
        hints.append("🎉 Great energy and enthusiasm!")
        if filler_pct > 3:
            hints.append("🗣️ Reduce filler words to maintain professionalism")
    
    # General performance hints
    if transcript_metrics.get('word_count', 0) < 20:
        hints.append("📝 Speak longer - aim for 30+ words with specific examples")
    
    if transcript_metrics.get('word_count', 0) > 80:
        hints.append("📊 Excellent detail - very comprehensive answer")
    
    return hints

def compute_metrics(transcript, duration_s, voice_features=None):
    """Compute speech metrics"""
    if not transcript or any(msg in transcript for msg in [
        "No speech detected", "Processing error", "Speech recognition error", 
        "Could not understand audio", "service unavailable", "Audio conversion failed"
    ]):
        base_metrics = {
            "wpm": 0,
            "filler_pct": 0,
            "duration_s": max(5.0, round(duration_s, 1)),
            "word_count": 0,
        }
    else:
        words = transcript.split()
        n_words = len(words)
        
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

        base_metrics = {
            "wpm": round(wpm, 1),
            "filler_pct": round(filler_pct, 1),
            "duration_s": round(duration_s, 1),
            "word_count": n_words,
        }
    
    # Add voice features if available
    if voice_features:
        base_metrics.update({
            "pitch_stability": voice_features.get('pitch_stability', 0),
            "energy_consistency": 1 - voice_features.get('rms_variance', 1),
            "vocal_variety": voice_features.get('spectral_centroid_std', 0) / 1000,
        })
    
    # Convert numpy types to Python native types
    return convert_numpy_types(base_metrics)

def transcribe_webm_direct(webm_path):
    """
    Transcribe WebM audio using Whisper
    """
    print(f"🎯 Direct WebM transcription with Whisper: {webm_path}")
    
    if not check_ffmpeg():
        raise FileNotFoundError("FFmpeg is not installed or not found in PATH.")
    
    if not os.path.exists(webm_path):
        raise FileNotFoundError(f"Audio file not found: {webm_path}")
    
    try:
        model = whisper.load_model("base")
        result = model.transcribe(webm_path, fp16=False)
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
    Enhanced main transcription function with emotion analysis
    """
    print(f"🎯 Processing: {audio_path}")
    
    if audio_path.endswith('.webm'):
        try:
            # Step 1: Transcribe audio
            transcript, duration = transcribe_webm_direct(audio_path)
            
            # Step 2: Extract voice features (with safe fallback)
            voice_features = safe_extract_voice_features(audio_path)
            
            # Step 3: Compute basic metrics
            metrics = compute_metrics(transcript, duration, voice_features)
            
            # Step 4: Emotion analysis
            emotion_data = classify_emotion_from_features(voice_features, metrics)
            
            # Step 5: Generate hints (combine emotion and content hints)
            emotion_hints = generate_emotion_hints(emotion_data, metrics)
            content_hints = rule_based_hints(metrics, transcript)
            
            all_hints = emotion_hints + content_hints
            
            print(f"🎭 EMOTION ANALYSIS RESULT: {emotion_data['primary_emotion']}")
            print(f"📊 VOICE METRICS: {emotion_data['voice_metrics']}")
            
            return {
                "transcript": transcript,
                "metrics": metrics,
                "emotions": emotion_data,  # NEW: Emotion analysis
                "hints": all_hints
            }
            
        except Exception as e:
            print(f"❌ Enhanced analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to basic analysis without emotions
            try:
                transcript, duration = transcribe_webm_direct(audio_path)
                metrics = compute_metrics(transcript, duration)
                hints = rule_based_hints(metrics, transcript)
                
                return {
                    "transcript": transcript,
                    "metrics": metrics,
                    "emotions": {
                        "primary_emotion": "analysis_failed",
                        "confidence_score": 0,
                        "emotion_breakdown": {},
                        "voice_metrics": {}
                    },
                    "hints": hints + ["Emotion analysis temporarily unavailable"]
                }
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                
                file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
                estimated_duration = file_size / 10000
                
                return {
                    "transcript": f"Basic analysis failed. Please try again. (~{estimated_duration:.1f}s)",
                    "metrics": {"wpm": 0, "filler_pct": 0, "duration_s": estimated_duration, "word_count": 0},
                    "emotions": {
                        "primary_emotion": "unknown",
                        "confidence_score": 0,
                        "emotion_breakdown": {},
                        "voice_metrics": {}
                    },
                    "hints": [
                        "Speak clearly for 10-20 seconds",
                        "Ensure good microphone quality", 
                        "Record in a quiet environment"
                    ]
                }
    
    return {
        "transcript": "Unsupported audio format",
        "metrics": {"wpm": 0, "filler_pct": 0, "duration_s": 5, "word_count": 0},
        "emotions": {
            "primary_emotion": "unknown",
            "confidence_score": 0,
            "emotion_breakdown": {},
            "voice_metrics": {}
        },
        "hints": ["Technical error - unsupported format"]
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

# Import librosa only if available
try:
    import librosa
    print("✅ Librosa loaded successfully")
except ImportError:
    print("⚠️ Librosa not available, using simplified emotion analysis")
    # Override functions to use simple version
    def transcribe(audio_path):
        """
        Fallback transcription function using simple emotion analysis
        """
        print(f"🎯 Processing (simple mode): {audio_path}")
        
        if audio_path.endswith('.webm'):
            try:
                # Step 1: Transcribe audio
                transcript, duration = transcribe_webm_direct(audio_path)
                
                # Step 2: Compute basic metrics
                metrics = compute_metrics(transcript, duration)
                
                # Step 3: Use SIMPLE emotion analysis
                emotion_data = classify_emotion_simple(metrics)
                
                # Step 4: Generate hints
                emotion_hints = generate_emotion_hints_simple(emotion_data, metrics)
                content_hints = rule_based_hints(metrics, transcript)
                
                all_hints = emotion_hints + content_hints
                
                print(f"🎭 SIMPLE EMOTION ANALYSIS: {emotion_data['primary_emotion']}")
                print(f"📊 METRICS: WPM={metrics['wpm']}, Fillers={metrics['filler_pct']}%")
                
                return {
                    "transcript": transcript,
                    "metrics": metrics,
                    "emotions": emotion_data,
                    "hints": all_hints
                }
                
            except Exception as e:
                print(f"❌ Simple analysis failed: {e}")
                # Basic fallback...