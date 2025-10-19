# 🎙️ WP5 — ASR & Delivery Metrics & Real-time Hints

This project implements an offline speech-to-text and delivery analysis system.  
It uses **faster-whisper** for automatic speech recognition (ASR), computes metrics like **WPM**, **filler%**, and **STAR hints**, and explains the results for interview-like speaking analysis.

---

## 🚀 Features

- 🎧 Local audio transcription (offline)
- 📊 Delivery metrics: Words Per Minute (WPM), filler percentage, and duration
- 💬 Real-time or batch hints for speech pacing and structure
- 🧠 STAR analysis (Situation, Task, Action, Result)
- 🪄 Optional WebSocket streaming for partial updates
- 🪶 Works fully offline after setup

---

## 🧩 Dependencies

Install these libraries inside your conda or virtual environment:

```bash
pip install faster-whisper soundfile numpy re regex websockets
pip install ipywidgets
pip install scipy
pip install ffmpeg-python
