import os
import tkinter as tk
from tkinter import filedialog
from your_transcription_module import transcribe, highlight_fillers  # replace with your script name

# -----------------------------
# Open file dialog
# -----------------------------
root = tk.Tk()
root.withdraw()  # hide the main window

file_path = filedialog.askopenfilename(
    title="Select an audio file",
    filetypes=[("Audio Files", "*.mp3 *.mp4 *.m4a *.wav")]
)

if not file_path:
    print("No file selected!")
    exit()

print(f"Selected file: {file_path}")

# -----------------------------
# Transcribe and analyze
# -----------------------------
result = transcribe(file_path)

print("\n--- Transcript ---")
print(result["transcript"])

print("\n--- Metrics ---")
for k, v in result["metrics"].items():
    print(f"{k}: {v}")

print("\n--- Hints ---")
for hint in result["hints"]:
    print("-", hint)

print("\n--- Highlighted Fillers ---")
print(highlight_fillers(result["transcript"], language=result["language"]))
