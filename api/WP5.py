{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "7f30c954-ae84-419f-8642-5a7376fa9169",
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "C:\\Users\\maram\\anaconda3\\envs\\wp5\\lib\\site-packages\\ctranslate2\\__init__.py:8: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.\n",
      "  import pkg_resources\n"
     ]
    }
   ],
   "source": [
    "from faster_whisper import WhisperModel\n",
    "import soundfile as sf\n",
    "import numpy as np\n",
    "import re, json\n",
    "import warnings\n",
    "warnings.filterwarnings(\"ignore\", category=UserWarning)\n",
    "\n",
    "\n",
    "# ---- Configuration ----\n",
    "FILLERS = [\n",
    "    \"um\", \"uh\", \"uhh\", \"uhhh\",\n",
    "    \"erm\", \"er\", \"eh\", \"ehh\",\n",
    "    \"ah\", \"aah\", \"aaah\",\n",
    "    \"hmm\", \"mmm\", \"mm\",\n",
    "    \"like\", \"you know\", \"basically\", \"actually\"\n",
    "]\n",
    "\n",
    "STAR_PATTERN = {\n",
    "    \"Situation\": r\"\\b(Situation|context|when)\\b\",\n",
    "    \"Task\": r\"\\b(Task|goal|objective)\\b\",\n",
    "    \"Action\": r\"\\b(Action|I decided|I did)\\b\",\n",
    "    \"Result\": r\"\\b(Result|outcome|impact)\\b\"\n",
    "}\n",
    "\n",
    "def compute_metrics(transcript, duration_s):\n",
    "    words = transcript.split()\n",
    "    n_words = len(words)\n",
    "    wpm = (n_words / duration_s) * 60 if duration_s > 0 else 0\n",
    "\n",
    "    filler_pattern = r\"\\b(\" + \"|\".join(re.escape(f) for f in FILLERS) + r\")+\\b\"\n",
    "    filler_count = len(re.findall(filler_pattern, transcript.lower()))\n",
    "    filler_pct = (filler_count / n_words) * 100 if n_words > 0 else 0\n",
    "\n",
    "    return {\n",
    "        \"wpm\": round(wpm, 1),\n",
    "        \"filler_pct\": round(filler_pct, 1),\n",
    "        \"duration_s\": round(duration_s, 1),\n",
    "        \"word_count\": n_words,\n",
    "    }\n",
    "\n",
    "def rule_based_hints(metrics, transcript):\n",
    "    hints = []\n",
    "    if metrics[\"wpm\"] > 170:\n",
    "        hints.append(\"Pace > 170 WPM\")\n",
    "    if metrics[\"filler_pct\"] > 5:\n",
    "        hints.append(\"Filler > 5%\")\n",
    "    missing = [k for k, p in STAR_PATTERN.items() if not re.search(p, transcript, re.I)]\n",
    "    if missing:\n",
    "        hints.append(f\"STAR: {', '.join(missing)} missing\")\n",
    "    return hints or [\"Good delivery!\"]\n",
    "\n",
    "def transcribe(audio_path):\n",
    "    model = WhisperModel(\"small\", device=\"cpu\")\n",
    "    segments, info = model.transcribe(audio_path)\n",
    "    transcript = \" \".join([seg.text.strip() for seg in segments])\n",
    "    metrics = compute_metrics(transcript, info.duration)\n",
    "    hints = rule_based_hints(metrics, transcript)\n",
    "    result = {\"transcript\": transcript, \"metrics\": metrics, \"hints\": hints}\n",
    "    return result\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "162d39c2-6d5d-44b8-88e3-4cc6ed359995",
   "metadata": {},
   "outputs": [],
   "source": [
    "def explain_results(result):\n",
    "    metrics = result[\"metrics\"]\n",
    "    hints = result[\"hints\"]\n",
    "    transcript = result[\"transcript\"].lower()\n",
    "\n",
    "    # same filler list as your main script\n",
    "    FILLERS = [\"um\", \"uh\", \"like\", \"you know\", \"aah\", \"mmm\", \"er\", \"eh\", \"hmm\"]\n",
    "\n",
    "    print(\"\\n🧾 EXPLANATION:\")\n",
    "\n",
    "    # 1️⃣ WPM explanation\n",
    "    if metrics[\"wpm\"] < 100:\n",
    "        print(f\"- You spoke slowly ({metrics['wpm']} WPM). Try being a bit more energetic.\")\n",
    "    elif metrics[\"wpm\"] > 150:\n",
    "        print(f\"- You spoke quite fast ({metrics['wpm']} WPM). Ideal range: 120–160 WPM.\")\n",
    "    else:\n",
    "        print(f\"- Your pace ({metrics['wpm']} WPM) is in a good range for interviews.\")\n",
    "\n",
    "    # 2️⃣ Filler explanation\n",
    "    found_fillers = [f for f in FILLERS if f in transcript]\n",
    "\n",
    "    if metrics[\"filler_pct\"] > 10:\n",
    "        print(f\"- Fillers made up {metrics['filler_pct']}% of your words → shows nervousness. Practice silent pauses.\")\n",
    "    elif metrics[\"filler_pct\"] > 5:\n",
    "        print(f\"- Fillers made up {metrics['filler_pct']}% of your words → mild hesitation, but manageable.\")\n",
    "    else:\n",
    "        print(f\"- Very few fillers ({metrics['filler_pct']}%). Great verbal control.\")\n",
    "\n",
    "    # 👉 Show which fillers were actually found\n",
    "    if found_fillers:\n",
    "        print(f\"  • Fillers detected: {', '.join(found_fillers)}\")\n",
    "    else:\n",
    "        print(\"  • No common fillers detected 👏\")\n",
    "\n",
    "    # 3️⃣ STAR explanation\n",
    "    if any(\"STAR\" in h for h in hints):\n",
    "        print(\"- STAR structure incomplete — include Situation, Task, Action, and Result clearly.\")\n",
    "    else:\n",
    "        print(\"- STAR structure complete — strong storytelling!\")\n",
    "\n",
    "    # 4️⃣ Overall summary\n",
    "    if metrics[\"wpm\"] > 170 or metrics[\"filler_pct\"] > 10:\n",
    "        print(\"⚠️ Overall: Confident but needs calmer delivery and fewer fillers.\")\n",
    "    elif any(\"STAR\" in h for h in hints):\n",
    "        print(\"🟡 Overall: Clear tone, but expand on your story with full STAR detail.\")\n",
    "    else:\n",
    "        print(\"✅ Overall: Great delivery balance — clear, confident, and structured.\")\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "7b282a8c-f424-4d96-bd03-15d0890139e7",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "🎤 Recording... start speaking now!\n",
      "✅ Saved recording as sample.wav\n"
     ]
    }
   ],
   "source": [
    "import sounddevice as sd\n",
    "from scipy.io.wavfile import write\n",
    "\n",
    "fs = 16000  # Sample rate (Hz)\n",
    "duration = 10  # seconds — you can increase to 20 or 30 if you like\n",
    "output_path = \"sample.wav\"\n",
    "\n",
    "print(\"🎤 Recording... start speaking now!\")\n",
    "recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)\n",
    "sd.wait()  # Wait until recording is finished\n",
    "write(output_path, fs, recording)\n",
    "print(f\"✅ Saved recording as {output_path}\")\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "1cf8fafb-1ee8-4019-a578-9d326e748dba",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "application/vnd.jupyter.widget-view+json": {
       "model_id": "69ded8ae1ee348ad99dac2124427a9b3",
       "version_major": 2,
       "version_minor": 0
      },
      "text/plain": [
       "VBox(children=(FileUpload(value=(), accept='.mp3,.mp4,.m4a,.wav', description='Upload'), Button(button_style='…"
      ]
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "import os\n",
    "import subprocess\n",
    "import soundfile as sf\n",
    "import ipywidgets as widgets\n",
    "from IPython.display import display, clear_output, Audio\n",
    "\n",
    "# --- 1️⃣ Create widgets ---\n",
    "uploader = widgets.FileUpload(accept='.mp3,.mp4,.m4a,.wav', multiple=False)\n",
    "convert_button = widgets.Button(description=\"🎬 Convert to WAV\", button_style='success')\n",
    "output = widgets.Output()\n",
    "\n",
    "display(widgets.VBox([uploader, convert_button, output]))\n",
    "\n",
    "# --- 2️⃣ Conversion function ---\n",
    "def convert_file(b):\n",
    "    with output:\n",
    "        clear_output()\n",
    "        if not uploader.value:\n",
    "            print(\"⚠️ Please upload a file first.\")\n",
    "            return\n",
    "\n",
    "        # handle both old and new ipywidgets formats\n",
    "        uploaded_file = list(uploader.value.values())[0] if isinstance(uploader.value, dict) else uploader.value[0]\n",
    "\n",
    "        filename = uploaded_file.get('metadata', {}).get('name', uploaded_file.get('name', 'uploaded_audio'))\n",
    "        with open(filename, 'wb') as f:\n",
    "            f.write(uploaded_file['content'])\n",
    "        print(f\"📂 Uploaded file: {filename}\")\n",
    "\n",
    "        base, _ = os.path.splitext(filename)\n",
    "        wav_path = base + \"_converted.wav\"\n",
    "\n",
    "        print(\"🎧 Converting to .wav (16kHz mono)... please wait.\")\n",
    "        command = [\"ffmpeg\", \"-y\", \"-i\", filename, \"-ar\", \"16000\", \"-ac\", \"1\", wav_path]\n",
    "        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)\n",
    "\n",
    "        if os.path.exists(wav_path):\n",
    "            data, samplerate = sf.read(wav_path)\n",
    "            duration = len(data) / samplerate\n",
    "            print(f\"✅ Done! Saved as: {wav_path}\")\n",
    "            print(f\"🎵 Sample rate: {samplerate} Hz\")\n",
    "            print(f\"⏱ Duration: {duration:.1f} seconds\")\n",
    "            display(Audio(wav_path))\n",
    "        else:\n",
    "            print(\"❌ Conversion failed. Check FFmpeg installation.\")\n",
    "\n",
    "# --- 3️⃣ Connect button to function ---\n",
    "convert_button.on_click(convert_file)\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "id": "88bed8b2-cf30-4da6-995b-7b653c4c5407",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "🎵 Available .wav files:\n",
      "1. Enregistrement_converted.wav\n",
      "2. sample.wav\n"
     ]
    },
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "\n",
      "Select file number to transcribe:  1\n"
     ]
    },
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "\n",
      "✅ Selected: C:\\Users\\maram\\Enregistrement_converted.wav\n",
      "\n",
      "🧠 Raw Results (JSON):\n",
      "{\n",
      "  \"transcript\": \"So the situation was our marketing campaign was like not performing well, you know, and my task was to configure out why engagement was dropping so quickly, and I decided to analyze the customer feedback.\",\n",
      "  \"metrics\": {\n",
      "    \"wpm\": 87.3,\n",
      "    \"filler_pct\": 5.7,\n",
      "    \"duration_s\": 24.0,\n",
      "    \"word_count\": 35\n",
      "  },\n",
      "  \"hints\": [\n",
      "    \"Filler > 5%\",\n",
      "    \"STAR: Result missing\"\n",
      "  ]\n",
      "}\n",
      "\n",
      "🧾 EXPLANATION:\n",
      "- You spoke slowly (87.3 WPM). Try being a bit more energetic.\n",
      "- Fillers made up 5.7% of your words → mild hesitation, but manageable.\n",
      "  • Fillers detected: like, you know, er\n",
      "- STAR structure incomplete — include Situation, Task, Action, and Result clearly.\n",
      "🟡 Overall: Clear tone, but expand on your story with full STAR detail.\n"
     ]
    }
   ],
   "source": [
    "import os, json\n",
    "\n",
    "# Step 1️⃣: List available .wav files\n",
    "folder = \"C:\\\\Users\\\\maram\"\n",
    "wav_files = [f for f in os.listdir(folder) if f.lower().endswith('.wav')]\n",
    "\n",
    "if not wav_files:\n",
    "    print(\"⚠️ No .wav files found in\", folder)\n",
    "else:\n",
    "    print(\"🎵 Available .wav files:\")\n",
    "    for i, f in enumerate(wav_files, 1):\n",
    "        print(f\"{i}. {f}\")\n",
    "\n",
    "    # Step 2️⃣: Choose one to transcribe\n",
    "    choice = int(input(\"\\nSelect file number to transcribe: \")) - 1\n",
    "    file_path = os.path.join(folder, wav_files[choice])\n",
    "    print(f\"\\n✅ Selected: {file_path}\")\n",
    "\n",
    "    # Step 3️⃣: Run your ASR and metrics\n",
    "    result = transcribe(file_path)\n",
    "\n",
    "    # Step 4️⃣: Show structured JSON\n",
    "    print(\"\\n🧠 Raw Results (JSON):\")\n",
    "    print(json.dumps(result, indent=2))\n",
    "\n",
    "    # Step 5️⃣: Explain in plain language\n",
    "    explain_results(result)\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "930e9048-13f7-4e22-9df3-d57381c46dcc",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python (wp5)",
   "language": "python",
   "name": "wp5"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.18"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
