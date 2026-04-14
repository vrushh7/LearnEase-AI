# 🎓 LearnEase-AI

**Transform any lecture into comprehensive study materials — in any language.**

Live Demo 👉 [learnease-ai-fvxukzltzojqydehaywrkz.streamlit.app](https://learnease-ai-fvxukzltzojqydehaywrkz.streamlit.app)

---

## What It Does

LearnEase-AI is an AI-powered study assistant that takes any audio or video lecture file and automatically generates:

- 📝 **Full Transcript** — converts spoken audio to text using OpenAI Whisper
- 📋 **Auto Summary** — extracts the key points from the transcript
- 🌍 **Translation** — translates the summary into 15+ languages
- 🎬 **Dubbed Video** — replaces the original audio with a text-to-speech dubbed version in your target language
- 📄 **PDF & TXT Export** — download the transcript and summary as PDF or text files

---

## Features

- Supports **15+ languages** including Hindi, Kannada, Marathi, Gujarati, Spanish, French, German, Chinese, Japanese, Korean, Arabic, Portuguese, Russian, and Italian
- Accepts **audio files**: MP3, WAV, M4A, AAC, FLAC, OGG, WMA
- Accepts **video files**: MP4, AVI, MOV, MKV, FLV, WMV, WebM
- Automatic audio preprocessing and noise normalization via FFmpeg
- Google Text-to-Speech (gTTS) for dubbed audio generation
- LSA-based summarization for English content
- PDF export using fpdf2

---

## Tech Stack

| Technology | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web app framework |
| [OpenAI Whisper](https://github.com/openai/whisper) | Speech-to-text transcription |
| [MoviePy](https://zulko.github.io/moviepy/) | Video/audio processing |
| [FFmpeg](https://ffmpeg.org/) | Audio extraction and conversion |
| [gTTS](https://gtts.readthedocs.io/) | Google Text-to-Speech |
| [deep-translator](https://github.com/nidhaloff/deep-translator) | Google Translate API wrapper |
| [sumy](https://github.com/miso-belica/sumy) | LSA-based text summarization |
| [nltk](https://www.nltk.org/) | Natural language processing |
| [fpdf2](https://py-fpdf2.readthedocs.io/) | PDF generation |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | FFmpeg binaries |

---

## How to Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/vrushh7/LearnEase-AI.git
cd LearnEase-AI
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## How to Use

1. **Select language** — choose the language spoken in your file and the language you want to translate to
2. **Upload** your audio or video lecture file
3. **Transcribe** — click "Start Transcription" and wait for Whisper to process the audio
4. **Translate** — optionally translate the summary to another language
5. **Dub** — generate a dubbed video with the translated audio track
6. **Download** — export transcript and summary as PDF or TXT

---

## Project Structure

```
LearnEase-AI/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Requirements

```
streamlit
openai-whisper
nltk
sumy
imageio-ffmpeg
gTTS
moviepy==1.0.3
fpdf2
deep-translator
requests
pyttsx3
```

---

## Author

**Vrushabh Upadhye** — [github.com/vrushh7](https://github.com/vrushh7)
