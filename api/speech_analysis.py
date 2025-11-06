import os
import subprocess
import re
import tempfile
import whisper
from pydub import AudioSegment
import tkinter as tk
from tkinter import filedialog
import threading
import string
from pydub import AudioSegment
import spacy
nlp = spacy.load("en_core_web_lg")
import tempfile
import subprocess



# --- FFmpeg paths ---
FFMPEG_FOLDER = r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin"
FFPROBE_FOLDER = r"C:\ProgramData\chocolatey\bin"
FFMPEG_PATH = os.path.join(FFMPEG_FOLDER, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(FFPROBE_FOLDER, "ffprobe.exe")

# Add FFmpeg folder to PATH
os.environ["PATH"] = FFMPEG_FOLDER + os.pathsep + os.environ.get("PATH", "")

# Set PyDub converter and ffprobe explicitly
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH

print("Using ffmpeg:", AudioSegment.converter)
print("Using ffprobe:", AudioSegment.ffprobe)

# -----------------------------
# Check FFmpeg
# -----------------------------
def check_ffmpeg():
    try:
        subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, text=True, check=True)
        subprocess.run([FFPROBE_PATH, "-version"], capture_output=True, text=True, check=True)
        return True
    except Exception as e:
        print("❌ FFmpeg/FFprobe check failed:", e)
        return False

# -----------------------------
# Filler words
# -----------------------------
FILLERS_EN = ["um","uh","like","you know","actually","basically","so","well","kind of","right","i mean","okay","hmm","ah","er","mm","yeah","sort of","just","literally"]
FILLERS_FR = ["euh","ben","alors","quoi","en fait","donc","hein","bah","heu","d'accord","mais","genre","vous savez","voilà","bon","ouais"]
FILLERS_AR = ["اممم","يعني","طيب","حسناً","أوكي","هه","اه","يعني يعني","مم","حسنا","هاه","تمام","يع"]

# -----------------------------
# Compute metrics
# -----------------------------
def compute_metrics(transcript, duration_s, language="en"):
    words = transcript.split()
    n_words = len(words)
    
    # fallback for empty transcript
    if n_words == 0:
        n_words = 1
        transcript = " "  # prevent division by zero
    
    # fallback for duration
    if duration_s < 1.0:
        duration_s = max(3.0, n_words / 3)
    
    wpm = min((n_words / duration_s) * 60, 300)
    
    if language.startswith("fr"):
        fillers = FILLERS_FR
    elif language.startswith("ar"):
        fillers = FILLERS_AR
    else:
        fillers = FILLERS_EN

    filler_count = sum(len(re.findall(rf'\b{re.escape(f)}\b', transcript.lower())) for f in fillers)
    filler_pct = (filler_count / n_words * 100) if n_words else 0
    
    return {
        "wpm": round(wpm, 1),
        "filler_pct": round(filler_pct, 1),
        "duration_s": round(duration_s, 1),
        "word_count": n_words
    }


# -----------------------------
# Rule-based hints
# -----------------------------
def rule_based_hints(metrics, transcript, language="en"):
    hints = []
    if metrics["word_count"] < 10:
        hints.append({"en":"Speak longer and give examples to fully explain your answer.",
                      "fr":"Parlez un peu plus et illustrez vos réponses avec des exemples concrets.",
                      "ar":"تحدث لفترة أطول وأعط أمثلة لتوضيح إجابتك بالكامل."}[language[:2]])
    elif metrics["word_count"] < 25:
        hints.append({"en":"Good start – add more details to strengthen your response.",
                      "fr":"Bon début – ajoutez des détails supplémentaires pour enrichir votre réponse.",
                      "ar":"بداية جيدة – أضف المزيد من التفاصيل لتقوية إجابتك."}[language[:2]])
    elif metrics["word_count"] > 80:
        hints.append({"en":"Excellent detail – your answer is very thorough.",
                      "fr":"Excellente réponse – vos explications sont très complètes.",
                      "ar":"تفاصيل ممتازة – إجابتك شاملة جدًا."}[language[:2]])
    if metrics["wpm"] > 200:
        hints.append({"en":"You're speaking very fast – slow down to ensure clarity.",
                      "fr":"Vous parlez trop vite – ralentissez pour que vos propos soient plus clairs.",
                      "ar":"أنت تتحدث بسرعة كبيرة – حاول التحدث ببطء لتوضيح كلامك."}[language[:2]])
    elif metrics["wpm"] < 100:
        hints.append({"en":"Your pace is a bit slow – try speaking a little faster.",
                      "fr":"Votre rythme est un peu lent – essayez de parler légèrement plus rapidement.",
                      "ar":"سرعتك بطيئة قليلاً – حاول التحدث بشكل أسرع قليلاً."}[language[:2]])
    elif 120 <= metrics["wpm"] <= 150:
        hints.append({"en":"Great pace – easy for the listener to follow.",
                      "fr":"Rythme parfait – facile à suivre pour votre interlocuteur.",
                      "ar":"إيقاع ممتاز – من السهل على المستمع المتابعة."}[language[:2]])
    if language.startswith("fr"):
        fillers_text = "mots de remplissage (euh, ben, alors)"
    elif language.startswith("ar"):
        fillers_text = "كلمات حشو (اممم، يعني، طيب)"
    else:
        fillers_text = "filler words (um, uh, like)"
    if metrics["filler_pct"] > 8:
        hints.append({"en":f"Too many {fillers_text} – pause instead of filling gaps.",
                      "fr":f"Trop de {fillers_text} – marquez des pauses au lieu de remplir les silences.",
                      "ar":f"كثرة {fillers_text} – استخدم التوقف بدلاً من ملء الفجوات بالكلمات."}[language[:2]])
    elif 4 < metrics["filler_pct"] <= 8:
        hints.append({"en":f"Some {fillers_text} – reducing them will make your speech clearer.",
                      "fr":f"Quelques {fillers_text} – les réduire rendra votre discours plus clair.",
                      "ar":f"بعض {fillers_text} – تقليلها سيجعل كلامك أكثر وضوحًا."}[language[:2]])
    elif metrics["filler_pct"] <= 2 and metrics["word_count"] > 10:
        hints.append({"en":"Excellent – very few filler words, your speech is clean.",
                      "fr":"Excellent – très peu de mots de remplissage, votre discours est clair.",
                      "ar":"ممتاز – كلمات حشو قليلة جدًا، كلامك واضح."}[language[:2]])
    indicators = ["situation","task","action","result","challenge","goal","implemented","outcome"]
    count = sum(1 for word in indicators if word in transcript.lower())
    if count >= 3:
        hints.append({"en":"Great STAR structure – clearly show Situation, Task, Action, Result.",
                      "fr":"Excellente structure STAR – présentez clairement Situation, Tâche, Action et Résultat.",
                      "ar":"هيكل STAR ممتاز – وضح الحالة، المهمة، الإجراء، النتيجة بوضوح."}[language[:2]])
    elif count >= 1 and metrics["word_count"] > 15:
        hints.append({"en":"Try following the STAR method: describe Situation, Task, Action, Result.",
                      "fr":"Essayez la méthode STAR : décrivez la Situation, la Tâche, l’Action et le Résultat.",
                      "ar":"حاول اتباع طريقة STAR: وصف الحالة، المهمة، الإجراء، النتيجة."}[language[:2]])
    elif metrics["word_count"] > 20:
        hints.append({"en":"Consider STAR: explain situation, task, actions, and results clearly.",
                      "fr":"Pensez à STAR : expliquez clairement la situation, la tâche, les actions et les résultats.",
                      "ar":"اعتبر STAR: اشرح الحالة، المهمة، الإجراءات، والنتائج بوضوح."}[language[:2]])
    if not hints:
        hints.append({"en":"Good communication – keep practicing and refining your answers.",
                      "fr":"Bonne communication – continuez à pratiquer et à affiner vos réponses.",
                      "ar":"تواصل جيد – استمر في التدرب وتحسين إجاباتك."}[language[:2]])
    return hints

# -----------------------------
# Highlight filler words
# -----------------------------
def highlight_fillers(transcript, language="en"):
    if not transcript:
        return "(No transcript available)"
    words = transcript.split()
    if language.startswith("fr"):
        fillers = FILLERS_FR
    elif language.startswith("ar"):
        fillers = FILLERS_AR
    else:
        fillers = FILLERS_EN
    highlighted = [f"[{w}]" if w.lower() in fillers else w for w in words]
    return " ".join(highlighted)

# -----------------------------
# Convert audio to WAV
# -----------------------------
def convert_to_wav(audio_path):
    """
    Convert any audio file to mono 16kHz WAV using PyDub.
    Returns path to temporary WAV file.
    """
    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_wav.close()

    try:
        # Load audio file via PyDub
        audio = AudioSegment.from_file(audio_path)
        # Convert to mono, 16kHz, PCM16
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        audio.export(tmp_wav.name, format="wav")
        return tmp_wav.name
    except Exception as e:
        print("❌ Audio conversion failed:", str(e))
        raise RuntimeError(f"Cannot convert {audio_path} to WAV. The file may be corrupted or unsupported.") from e

def convert_webm_to_mp4(input_path):
    """Convert WebM to MP4 using FFmpeg."""
    tmp_mp4 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp_mp4.close()
    cmd = [
        "ffmpeg",  # assumes ffmpeg is on PATH
        "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        tmp_mp4.name
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return tmp_mp4.name

def emotion_hint(emotion):
    """Return a hint message for a given emotion."""
    hints = {
        "happy": "You seem happy! Keep it up.",
        "sad": "You look sad, maybe try smiling.",
        "angry": "Take a deep breath to relax your tone.",
        "surprise": "You look surprised, stay calm.",
        "neutral": "Neutral expression, good for professional tone.",
        "fear": "You seem afraid, try to relax.",
        "disgust": "You look disgusted, maintain a neutral expression."
    }
    return hints.get(str(emotion).lower(), "Expression detected.")

# -----------------------------
# Convert audio to WAV
# -----------------------------
def convert_to_wav(audio_path):
    """
    Convert any audio file to mono 16kHz WAV using PyDub.
    Returns path to temporary WAV file.
    """
    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_wav.close()

    try:
        # Load audio file via PyDub
        audio = AudioSegment.from_file(audio_path)
        # Convert to mono, 16kHz, PCM16
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        audio.export(tmp_wav.name, format="wav")
        return tmp_wav.name
    except Exception as e:
        print("❌ Audio conversion failed:", str(e))
        raise RuntimeError(f"Cannot convert {audio_path} to WAV. The file may be corrupted or unsupported.") from e

# -----------------------------
# Transcribe audio/video
# -----------------------------
def transcribe(audio_path, language=None):
    import wave

    print(f"🎯 Processing audio: {audio_path}")

    # Check FFmpeg
    if not check_ffmpeg():
        raise EnvironmentError("FFmpeg or FFprobe not found. Add to system PATH.")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Convert to WAV if needed
    ext = os.path.splitext(audio_path)[1].lower()
    if ext in [".webm", ".mp4", ".m4a"]:
        # Video/audio file → convert to WAV using FFmpeg
        wav_path = convert_webm_to_wav(audio_path)
    else:
        # Already audio file → convert if not WAV
        wav_path = convert_to_wav(audio_path)

    try:
        # Load Whisper model
        model = whisper.load_model("base")
        result = model.transcribe(wav_path, fp16=False, language=language)

        # DEBUG: print raw Whisper output
        print("🎯 Whisper raw result:", result)

        # Extract transcript safely
        transcript = result.get("text", "").strip()
        if not transcript:
            transcript = "(No speech detected)"
        print("🎯 Transcript extracted:", transcript)

        # Compute duration
        if result.get("segments"):
            duration = result["segments"][-1]["end"]
        else:
            # Fallback: estimate duration from WAV file length
            with wave.open(wav_path, "rb") as wf:
                duration = wf.getnframes() / wf.getframerate()
        print("⏱ Estimated duration (s):", duration)

        # Language detected
        lang_detect = result.get("language", "en")
        print("🌐 Detected language:", lang_detect)

        # Compute metrics and hints
        metrics = compute_metrics(transcript, duration, language=lang_detect)
        hints = rule_based_hints(metrics, transcript, language=lang_detect)
        highlighted = highlight_fillers(transcript, lang_detect)

        # DEBUG: print metrics
        print("📊 Computed metrics:", metrics)
        print("💡 Hints:", hints)

        return {
            "transcript": transcript,
            "metrics": metrics,
            "hints": hints,
            "highlighted": highlighted,
            "language": lang_detect
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Whisper transcription failed: {e}")
        return {
            "transcript": "(Transcription failed)",
            "metrics": {"wpm": 0, "filler_pct": 0, "duration_s": 0, "word_count": 0},
            "hints": ["Check microphone, speak clearly, ensure FFmpeg is installed"],
            "highlighted": "",
            "language": "en"
        }
    finally:
        # Clean up temporary WAV file
        if wav_path != audio_path and os.path.exists(wav_path):
            os.unlink(wav_path)

# -----------------------------
# GUI: Upload file
# -----------------------------
def analyze_uploaded_file(metrics_widget, hints_widget, highlighted_widget):
    root = tk.Tk()
    root.withdraw()  # hide the temporary window for file selection
    file_path = filedialog.askopenfilename(
        title="Select audio/video file",
        filetypes=[("Media files","*.mp3 *.mp4 *.m4a *.wav *.webm")]
    )
    if not file_path:
        print("❌ No file selected.")
        return

    result = transcribe(file_path)

    # Update metrics
    metrics_widget.config(state="normal")
    metrics_widget.delete("1.0", tk.END)
    metrics_widget.insert(tk.END,
                          f"WPM: {result['metrics']['wpm']}\n"
                          f"Filler %: {result['metrics']['filler_pct']}\n"
                          f"Answer length: {result['metrics']['word_count']}\n"
                          f"Duration: {result['metrics']['duration_s']}s")
    metrics_widget.config(state="disabled")

    # Update hints
    hints_widget.config(state="normal")
    hints_widget.delete("1.0", tk.END)
    for hint in result["hints"]:
        hints_widget.insert(tk.END, f"• {hint}\n")
    hints_widget.config(state="disabled")

    # Update highlighted transcript
    highlighted_widget.config(state="normal")
    highlighted_widget.delete("1.0", tk.END)
    highlighted_widget.insert(tk.END, result["highlighted"])
    highlighted_widget.config(state="disabled")

# -----------------------------
# Record live video/audio
# -----------------------------
def record_live_video(duration_s=10, output_path="live_recording.mp4"):
    print("🎥 Detecting video/audio devices...")
    try:
        result = subprocess.run([FFMPEG_PATH,"-list_devices","true","-f","dshow","-i","dummy"], capture_output=True, text=True, check=True)
        output = result.stderr
    except subprocess.CalledProcessError as e:
        output = e.stderr
    # Use regex to extract device names
    video_devices = re.findall(r'\]  "([^"]+)"', output)
    audio_devices = re.findall(r'\]  "([^"]+)"', output)
    if not video_devices or not audio_devices:
        print("❌ No video/audio devices found.")
        return None
    video_device = video_devices[0]
    audio_device = audio_devices[0]
    print(f"Using video: {video_device}, audio: {audio_device}")
    try:
        cmd = [FFMPEG_PATH,"-y","-f","dshow","-i",f"video={video_device}:audio={audio_device}","-t",str(duration_s), output_path]
        subprocess.run(cmd, check=True)
        print(f"✅ Video saved: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg recording failed:", e)
        return None


# ✅ Add it here, after record_live_video
def record_and_analyze_video(metrics_widget, hints_widget, highlighted_widget, duration_s=8):
    video_path = record_live_video(duration_s=duration_s)
    if not video_path:
        print("❌ Recording failed.")
        return
    result = transcribe(video_path)

    # Update GUI widgets (same as analyze_uploaded_file)
    metrics_widget.config(state="normal")
    metrics_widget.delete("1.0", tk.END)
    metrics_widget.insert(tk.END,
                          f"WPM: {result['metrics']['wpm']}\n"
                          f"Filler %: {result['metrics']['filler_pct']}\n"
                          f"Answer length: {result['metrics']['word_count']}\n"
                          f"Duration: {result['metrics']['duration_s']}s")
    metrics_widget.config(state="disabled")

    hints_widget.config(state="normal")
    hints_widget.delete("1.0", tk.END)
    for hint in result["hints"]:
        hints_widget.insert(tk.END, f"• {hint}\n")
    hints_widget.config(state="disabled")

    highlighted_widget.config(state="normal")
    highlighted_widget.delete("1.0", tk.END)
    highlighted_widget.insert(tk.END, result["highlighted"])
    highlighted_widget.config(state="disabled")

    
# -----------------------------
# GUI: Upload file
# -----------------------------
def analyze_uploaded_file(metrics_widget, hints_widget, highlighted_widget):
    root = tk.Tk()
    root.withdraw()  # hide the temporary window for file selection
    file_path = filedialog.askopenfilename(
        title="Select audio/video file",
        filetypes=[("Media files","*.mp3 *.mp4 *.m4a *.wav *.webm")]
    )
    if not file_path:
        print("❌ No file selected.")
        return

    result = transcribe(file_path)

    # Update metrics
    metrics_widget.config(state="normal")
    metrics_widget.delete("1.0", tk.END)
    metrics_widget.insert(tk.END,
                          f"WPM: {result['metrics']['wpm']}\n"
                          f"Filler %: {result['metrics']['filler_pct']}\n"
                          f"Answer length: {result['metrics']['word_count']}\n"
                          f"Duration: {result['metrics']['duration_s']}s")
    metrics_widget.config(state="disabled")

    # Update hints
    hints_widget.config(state="normal")
    hints_widget.delete("1.0", tk.END)
    for hint in result["hints"]:
        hints_widget.insert(tk.END, f"• {hint}\n")
    hints_widget.config(state="disabled")

    # Update highlighted transcript
    highlighted_widget.config(state="normal")
    highlighted_widget.delete("1.0", tk.END)
    highlighted_widget.insert(tk.END, result["highlighted"])
    highlighted_widget.config(state="disabled")

# -----------------------------
# GUI
# -----------------------------
def run_gui():
    root = tk.Tk()
    root.title("Speech Analyzer")
    root.geometry("600x500")

    tk.Label(root, text="Speech Analyzer", font=("Arial",14,"bold")).pack(pady=5)

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)
    tk.Button(button_frame, text="Upload & Analyze File",
              command=lambda: threading.Thread(
                  target=analyze_uploaded_file,
                  args=(metrics_text, hints_text, highlighted_text)
              ).start(),
              width=25, height=2).grid(row=0, column=0, padx=5)
    tk.Button(button_frame, text="Record Video & Analyze",
              command=lambda: threading.Thread(
                  target=record_and_analyze_video,
                  args=(metrics_text, hints_text, highlighted_text, 8)
              ).start(),
              width=25, height=2).grid(row=0, column=1, padx=5)

    # Metrics display
    tk.Label(root, text="📊 Metrics:", font=("Arial",12,"bold")).pack(anchor="w", padx=10, pady=(10,0))
    metrics_text = tk.Text(root, height=5, width=70, state="disabled", bg="#f0f0f0")
    metrics_text.pack(padx=10, pady=2)

    # Hints display
    tk.Label(root, text="💡 Hints:", font=("Arial",12,"bold")).pack(anchor="w", padx=10, pady=(10,0))
    hints_text = tk.Text(root, height=7, width=70, state="disabled", bg="#f9f9f9")
    hints_text.pack(padx=10, pady=2)

    # Highlighted transcript
    tk.Label(root, text="🔍 Highlighted Fillers:", font=("Arial",12,"bold")).pack(anchor="w", padx=10, pady=(10,0))
    highlighted_text = tk.Text(root, height=8, width=70, state="disabled", bg="#f0f0f0")
    highlighted_text.pack(padx=10, pady=2)

    root.mainloop()

# -----------------------------
# Run GUI
# -----------------------------
if __name__ == "__main__":
    run_gui()