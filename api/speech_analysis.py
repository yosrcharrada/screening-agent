import os
import subprocess
import re
import tempfile
import whisper
from pydub import AudioSegment
import tkinter as tk
from tkinter import filedialog
import threading

# --- FFmpeg paths ---
FFMPEG_FOLDER = r"C:\Users\maram\OneDrive - ESPRIT\Documents\5DS1\ADSP\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\bin"
FFMPEG_PATH = os.path.join(FFMPEG_FOLDER, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(FFMPEG_FOLDER, "ffprobe.exe")

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
    return {"wpm": round(wpm,1),"filler_pct": round(filler_pct,1),"duration_s": round(duration_s,1),"word_count": n_words}

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
    ext = os.path.splitext(audio_path)[1].lower()
    if ext not in [".wav"]:
        tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_wav.close()
        AudioSegment.from_file(audio_path).export(tmp_wav.name, format="wav")
        return tmp_wav.name
    return audio_path

# ------------------------------
#convert webm to wav 
# ------------------------------
def convert_webm_to_wav(webm_path):
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    command = [
        "ffmpeg",
        "-y",
        "-i", webm_path,
        "-ac", "1",
        "-ar", "16000",
        tmp_wav.name
    ]
    subprocess.run(command, check=True)
    return tmp_wav.name

# -----------------------------
# Transcribe audio/video
# -----------------------------
def transcribe(audio_path, language=None):
    print(f"🎯 Processing: {audio_path}")
    if not check_ffmpeg():
        raise EnvironmentError("FFmpeg or FFprobe not found. Add to system PATH.")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    wav_path = convert_to_wav(audio_path)
    try:
        model = whisper.load_model("base")
        result = model.transcribe(wav_path, fp16=False, language=language)
        transcript = result.get("text","").strip()
        duration = result["segments"][-1]["end"] if result.get("segments") else 5.0
        lang_detect = result.get("language", "en")
        metrics = compute_metrics(transcript, duration, language=lang_detect)
        hints = rule_based_hints(metrics, transcript, language=lang_detect)
        highlighted = highlight_fillers(transcript, lang_detect)
        if wav_path != audio_path and os.path.exists(wav_path):
            os.unlink(wav_path)
        return {"transcript": transcript, "metrics": metrics, "hints": hints, "highlighted": highlighted, "language": lang_detect}
    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        return {"transcript": f"Speech recognition failed. File: {os.path.getsize(audio_path)} bytes",
                "metrics":{"wpm":0,"filler_pct":0,"duration_s":0,"word_count":0},
                "hints":["Check microphone, speak clearly, ensure FFmpeg is installed"],
                "highlighted":"", "language":"en"}

# -----------------------------
# GUI: Upload file
# -----------------------------
def analyze_uploaded_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select audio/video file", filetypes=[("Media files","*.mp3 *.mp4 *.m4a *.wav *.webm")])
    if not file_path:
        print("❌ No file selected.")
        return
    result = transcribe(file_path)
    print("\n📝 TRANSCRIPT:\n", result["transcript"])
    print("\n📊 METRICS:", result["metrics"])
    print("\n💡 HINTS:")
    for hint in result["hints"]:
        print("•", hint)
    print("\n🔍 HIGHLIGHTED FILLERS:\n", result["highlighted"])
    return result

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

# -----------------------------
# Extract audio and analyze
# -----------------------------
def record_and_analyze_video(duration_s=10):
    video_path = record_live_video(duration_s=duration_s)
    if not video_path:
        print("❌ Recording failed.")
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
        audio_path = tmp_audio.name
    try:
        subprocess.run([FFMPEG_PATH,"-i",video_path,"-vn","-acodec","pcm_s16le","-ar","16000","-ac","1",audio_path], check=True)
        print(f"🎧 Audio extracted: {audio_path}")
        result = transcribe(audio_path)
        print("\n📝 TRANSCRIPT:\n", result["transcript"])
        print("\n📊 METRICS:", result["metrics"])
        print("\n💡 HINTS:")
        for hint in result["hints"]:
            print("•", hint)
        print("\n🔍 HIGHLIGHTED FILLERS:\n", result["highlighted"])
        return result
    except Exception as e:
        print("❌ Audio extraction failed:", e)
        return None

# -----------------------------
# GUI
# -----------------------------
def run_gui():
    root = tk.Tk()
    root.title("Speech Analyzer")
    root.geometry("300x150")
    tk.Label(root, text="Speech Analyzer", font=("Arial",14,"bold")).pack(pady=5)
    tk.Button(root, text="Upload & Analyze File", command=lambda: threading.Thread(target=analyze_uploaded_file).start(), width=25, height=2).pack(pady=5)
    tk.Button(root, text="Record Video & Analyze", command=lambda: threading.Thread(target=lambda: record_and_analyze_video(8)).start(), width=25, height=2).pack(pady=5)
    root.mainloop()

# -----------------------------
# Run GUI
# -----------------------------
if __name__ == "__main__":
    run_gui()
