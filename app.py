import multiprocessing
multiprocessing.set_start_method("spawn", force=True)
import streamlit as st
import whisper
import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import imageio_ffmpeg
import tempfile
import os
import shutil
from gtts import gTTS
import base64
try:
    from moviepy.editor import VideoFileClip, AudioFileClip
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip
from fpdf import FPDF
from deep_translator import GoogleTranslator
import subprocess
import requests
import json
import re

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# FFmpeg fix
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_path)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
os.environ["PATH"] = "/home/appuser/.local/bin" + os.pathsep + ffmpeg_dir + os.pathsep + os.environ["PATH"]

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

@st.cache_resource
def load_whisper():
    import whisper
    return whisper.load_model("tiny")

if "model" not in st.session_state:
    st.session_state["model"] = None

TRANSLATOR_LANGS = {
    'English': 'en', 'Hindi': 'hi', 'Kannada': 'kn', 'Marathi': 'mr', 'Gujarati': 'gu',
    'Spanish': 'es', 'French': 'fr', 'German': 'de', 'Chinese': 'zh-CN',
    'Japanese': 'ja', 'Korean': 'ko', 'Arabic': 'ar', 'Portuguese': 'pt',
    'Russian': 'ru', 'Italian': 'it'
}

LANGUAGES = {
    'English': 'en', 'Hindi': 'hi', 'Kannada': 'kn', 'Marathi': 'mr', 'Gujarati': 'gu',
    'Spanish': 'es', 'French': 'fr', 'German': 'de', 'Chinese': 'zh-cn',
    'Japanese': 'ja', 'Korean': 'ko', 'Arabic': 'ar', 'Portuguese': 'pt',
    'Russian': 'ru', 'Italian': 'it'
}

st.set_page_config(page_title="LearnEaseAI", layout="wide", page_icon="🎓")

# ─── HEADER ───
st.title("🎓 LearnEaseAI")
st.divider()

# ─── Keep all original defaults ───
tts_engine = "Google TTS (gTTS)"
voice_gender = "Female"
source_language = "English"
source_lang_code = LANGUAGES[source_language]
target_language = "English"

# ─── Language Config ───
st.subheader("⚙️ Language Settings")
col_trans, col_translate = st.columns(2)

with col_trans:
    source_language = st.selectbox(
        "🎤 Audio / Video Language",
        list(LANGUAGES.keys()), index=0,
        help="Select the language spoken in your file",
        key="source_lang"
    )
    source_lang_code = LANGUAGES[source_language]

with col_translate:
    target_language = st.selectbox(
        "🌍 Translate Output To",
        list(LANGUAGES.keys()),
        key="target_lang"
    )

st.divider()

# ─── Upload ───
st.subheader("📤 Upload Your Lecture File")
st.caption("Supports MP3 · WAV · M4A · AAC · FLAC · OGG · MP4 · AVI · MOV · MKV · WebM")

media_file = st.file_uploader(
    "Drop your audio or video lecture here",
    type=["mp3","wav","m4a","aac","flac","ogg","wma","mp4","avi","mov","mkv","flv","wmv","webm"],
    help="Max recommended: 200MB"
)

# ─────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────

def remove_emojis_and_unicode(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA00-\U0001FA6F"
        u"\U0001FA70-\U0001FAFF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    text = text.encode('latin-1', 'replace').decode('latin-1')
    return text


class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'LearnEaseAI - Study Material', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        clean_title = remove_emojis_and_unicode(title)
        self.cell(0, 10, clean_title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        clean_body = remove_emojis_and_unicode(body)
        self.multi_cell(0, 6, clean_body)
        self.ln()


def create_pdf(content_dict):
    pdf = PDF()
    pdf.add_page()
    for title, content in content_dict.items():
        pdf.chapter_title(remove_emojis_and_unicode(title))
        pdf.chapter_body(remove_emojis_and_unicode(content))
    result = pdf.output(dest='S')
    if isinstance(result, (bytes, bytearray)):
        return bytes(result)
    return result.encode('latin-1')


def translate_text(text, target_lang):
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        max_length = 4500
        if len(text) <= max_length:
            return translator.translate(text)
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        return ' '.join([translator.translate(chunk) for chunk in chunks])
    except Exception as e:
        return f"Translation error: {str(e)}"


def extract_audio_from_video(video_path):
    try:
        video = VideoFileClip(video_path)
        audio_path = video_path.rsplit('.', 1)[0] + '_audio.wav'
        video.audio.write_audiofile(audio_path, logger=None)
        video.close()
        return audio_path
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def get_audio_duration(audio_path):
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        probe_cmd = [
            ffmpeg_exe.replace('ffmpeg', 'ffprobe') if 'ffprobe' in ffmpeg_exe else ffmpeg_exe,
            '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
        ]
        result = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode == 0 and result.stdout:
            return float(result.stdout.decode().strip())
        return 0
    except:
        return 0


def preprocess_audio(audio_path):
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if not os.path.exists(audio_path):
            return None, "Audio file not found"
        if os.path.getsize(audio_path) < 1000:
            return None, "Audio too small"
        duration = get_audio_duration(audio_path)
        if duration > 0 and duration < 1.0:
            return None, f"Audio too short ({duration:.1f}s)"
        output_path = audio_path.rsplit('.', 1)[0] + '_processed.wav'
        convert_cmd = [ffmpeg_exe, '-i', audio_path, '-ac', '1', '-ar', '16000',
                       '-af', 'loudnorm', '-y', output_path]
        result = subprocess.run(convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode != 0:
            return None, "Audio conversion failed"
        if not os.path.exists(output_path) or os.path.getsize(output_path) < 5000:
            return None, "Processed audio too short"
        return output_path, None
    except Exception as e:
        return None, f"Error: {str(e)}"


def convert_audio_to_mp3(audio_path):
    try:
        if audio_path.lower().endswith('.mp3'):
            return audio_path
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        output_path = audio_path.rsplit('.', 1)[0] + '_converted.mp3'
        convert_cmd = [ffmpeg_exe, '-i', audio_path, '-acodec', 'libmp3lame',
                       '-ar', '44100', '-ac', '2', '-y', output_path]
        result = subprocess.run(convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode == 0 and os.path.exists(output_path):
            try:
                if audio_path != output_path and '_converted' not in audio_path:
                    os.remove(audio_path)
            except:
                pass
            return output_path
        return audio_path
    except:
        return audio_path


def create_dubbed_video(video_path, translated_audio_path):
    try:
        audio_path = convert_audio_to_mp3(translated_audio_path)
        video = VideoFileClip(video_path)
        new_audio = AudioFileClip(audio_path)
        if new_audio.duration is None or new_audio.duration <= 0:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            ffmpeg_dir = os.path.dirname(ffmpeg_exe)
            if os.name == 'nt':
                ffprobe_exe = os.path.join(ffmpeg_dir, 'ffprobe.exe')
            else:
                ffprobe_exe = os.path.join(ffmpeg_dir, 'ffprobe')
            if not os.path.exists(ffprobe_exe):
                ffprobe_exe = shutil.which('ffprobe') or ffmpeg_exe.replace('ffmpeg', 'ffprobe')
            probe_cmd = [ffprobe_exe, '-v', 'error', '-show_entries', 'format=duration',
                         '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
            try:
                result = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                                        timeout=10)
                if result.returncode == 0 and result.stdout:
                    duration_str = result.stdout.decode().strip()
                    if duration_str and duration_str != 'N/A':
                        duration = float(duration_str)
                        if duration > 0:
                            new_audio.close()
                            new_audio = AudioFileClip(audio_path)
            except:
                pass
        if new_audio.duration and new_audio.duration > 0:
            if new_audio.duration < video.duration:
                new_audio = new_audio.audio_loop(duration=video.duration)
            elif new_audio.duration > video.duration:
                new_audio = new_audio.subclip(0, video.duration)
        else:
            new_audio = new_audio.set_duration(video.duration)
        final_video = video.set_audio(new_audio)
        output_path = video_path.rsplit('.', 1)[0] + '_dubbed.mp4'
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None, verbose=False)
        video.close()
        new_audio.close()
        final_video.close()
        try:
            if audio_path != translated_audio_path and '_converted' in audio_path:
                os.remove(audio_path)
        except:
            pass
        return output_path
    except Exception as e:
        st.error(f"Error creating dubbed video: {str(e)}")
        return None


def text_to_speech_gtts(text, lang):
    try:
        gtts_lang_map = {
            'kn': 'kn', 'mr': 'mr', 'gu': 'gu', 'hi': 'hi', 'en': 'en',
            'es': 'es', 'fr': 'fr', 'de': 'de', 'zh-cn': 'zh-cn', 'zh-CN': 'zh-cn',
            'ja': 'ja', 'ko': 'ko', 'ar': 'ar', 'pt': 'pt', 'ru': 'ru', 'it': 'it'
        }
        gtts_lang = gtts_lang_map.get(lang, lang)
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(fp.name)
        return fp.name
    except Exception as e:
        st.error(f"Error in TTS: {str(e)}. Language code used: {lang}")
        return None


def text_to_speech(text, voice_gender, lang, engine_choice="Google TTS (gTTS)"):
    try:
        return text_to_speech_gtts(text, lang)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


# ─────────────────────────────────────────
#  MAIN APPLICATION FLOW
# ─────────────────────────────────────────

if media_file is not None:
    file_extension = media_file.name.split('.')[-1].lower()
    is_video = file_extension in ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm']

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
        tmp.write(media_file.read())
        temp_filename = tmp.name

    st.success(f"✅ {'Video' if is_video else 'Audio'} file uploaded successfully!")

    if is_video:
        st.session_state['original_video'] = temp_filename
        col_video = st.columns([1, 2, 1])[1]
        with col_video:
            st.video(temp_filename)
    else:
        st.audio(temp_filename)

    # ── STEP 1: TRANSCRIPTION ──
    st.divider()
    st.subheader("Step 1 — Transcription")

    if 'transcript_text' not in st.session_state:
        if st.button("🎤 Start Transcription", type="primary", use_container_width=True):
            if is_video:
                st.info("Extracting audio from video...")
                audio_file = extract_audio_from_video(temp_filename)
                if not audio_file:
                    st.error("Failed to extract audio")
                    st.stop()
            else:
                audio_file = temp_filename

            st.info("Preprocessing audio...")
            processed_audio, error = preprocess_audio(audio_file)

            if error:
                st.error(f"❌ {error}")
                st.stop()

            with st.spinner("Transcribing with Whisper AI..."):
                try:
                    duration = get_audio_duration(processed_audio)
                    if duration > 0:
                        st.info(f"⏱ Audio duration: {duration:.1f}s")

                    if st.session_state["model"] is None:
                        with st.spinner("Loading Whisper model (first time only)..."):
                            st.session_state["model"] = load_whisper()

                    result = st.session_state["model"].transcribe(
                        processed_audio,
                        fp16=False,
                        language=source_lang_code,
                        verbose=False
                    )

                    transcript_text = result["text"]

                    if not transcript_text or len(transcript_text.strip()) < 10:
                        st.error("Transcription too short or failed.")
                        st.stop()

                    st.session_state['transcript_text'] = transcript_text
                    st.session_state['source_lang_code'] = source_lang_code
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    if "reshape tensor" in str(e):
                        st.error("Audio file corrupted or empty.")
                    st.stop()
    else:
        st.success("✅ Transcription complete!")
        with st.expander("📄 View Full Transcript", expanded=False):
            st.write(st.session_state['transcript_text'])

        # Generate summary
        if 'summary_text' not in st.session_state:
            transcript_text = st.session_state['transcript_text']
            current_source_lang = st.session_state.get('source_lang_code', 'en')
            indian_languages = ['hi', 'kn', 'mr', 'gu']
            if current_source_lang in indian_languages or current_source_lang != 'en':
                sentences = re.split(r'[.!?।।।\n]+', transcript_text)
                sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
                num_sentences = min(5, len(sentences))
                if num_sentences > 0:
                    summary_sentences = []
                    if len(sentences) >= 2:
                        summary_sentences.extend(sentences[:2])
                    if len(sentences) >= 4:
                        mid = len(sentences) // 2
                        summary_sentences.append(sentences[mid])
                    if len(sentences) >= 3:
                        summary_sentences.extend(sentences[-2:])
                    seen = set()
                    unique_sentences = []
                    for s in summary_sentences:
                        if s not in seen:
                            seen.add(s)
                            unique_sentences.append(s)
                    if current_source_lang in indian_languages:
                        separator = "। "
                        ending = "।"
                    else:
                        separator = ". "
                        ending = "."
                    st.session_state['summary_text'] = separator.join(unique_sentences[:5]) + ending
                else:
                    st.session_state['summary_text'] = transcript_text[:500] + ("..." if len(transcript_text) > 500 else "")
            else:
                try:
                    parser = PlaintextParser.from_string(transcript_text, Tokenizer("english"))
                    summarizer = LsaSummarizer()
                    summary = summarizer(parser.document, 5)
                    st.session_state['summary_text'] = "\n".join(str(s) for s in summary)
                except:
                    sentences = re.split(r'[.!?]+', transcript_text)
                    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
                    st.session_state['summary_text'] = ". ".join(sentences[:5]) + "."

        st.markdown("**📋 Auto-generated Summary**")
        st.info(st.session_state['summary_text'])

        # Download transcript
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "📥 Download Transcript (.txt)",
                st.session_state['transcript_text'],
                "transcript.txt",
                use_container_width=True
            )
        with col_dl2:
            content = {"Transcript": st.session_state['transcript_text'], "Summary": st.session_state['summary_text']}
            pdf = create_pdf(content)
            st.download_button(
                "📥 Download Transcript (.pdf)",
                pdf,
                "transcript.pdf",
                "application/pdf",
                use_container_width=True
            )

    # ── STEP 2: TRANSLATION ──
    if 'transcript_text' in st.session_state:
        if target_language != 'English':
            st.divider()
            st.subheader(f"Step 2 — Translation → {target_language}")

            if 'translated_summary' not in st.session_state:
                if st.button(f"🌐 Translate to {target_language}", type="primary", use_container_width=True):
                    with st.spinner("Translating..."):
                        target_lang_code = TRANSLATOR_LANGS[target_language]
                        translated = translate_text(st.session_state['summary_text'], target_lang_code)
                        st.session_state['translated_summary'] = translated
                        st.session_state['target_lang_code'] = target_lang_code
                        st.rerun()
            else:
                st.success(f"✅ Translation to {target_language} complete!")
                with st.expander(f"📄 View {target_language} Summary", expanded=False):
                    st.write(st.session_state['translated_summary'])
                st.download_button(
                    f"📥 Download {target_language} Summary (.txt)",
                    st.session_state['translated_summary'],
                    f"summary_{target_language}.txt",
                    use_container_width=True
                )

    # ── STEP 3: DUBBED VIDEO ──
    if 'transcript_text' in st.session_state:
        if target_language != 'English':
            target_lang_code = TRANSLATOR_LANGS[target_language]
            if 'translated_summary' in st.session_state:
                text_for_dubbing = st.session_state['translated_summary']
                lang_for_dubbing = target_lang_code
            else:
                text_for_dubbing = st.session_state.get('summary_text', '')
                lang_for_dubbing = target_lang_code
            display_lang = target_language
        else:
            text_for_dubbing = st.session_state.get('summary_text', '')
            lang_for_dubbing = st.session_state.get('source_lang_code', 'en')
            display_lang = source_language

        if text_for_dubbing:
            st.divider()
            st.subheader(f"Step 3 — Video Dubbing ({display_lang})")

            if is_video:
                if 'dubbed_video_bytes' not in st.session_state:
                    if st.button(f"🎬 Generate Dubbed Video in {display_lang}", type="primary", use_container_width=True):
                        with st.spinner(f"Creating {display_lang} dubbed video..."):
                            if target_language != 'English' and 'translated_summary' not in st.session_state:
                                with st.spinner("Auto-translating for dubbing..."):
                                    target_lang_code = TRANSLATOR_LANGS[target_language]
                                    text_for_dubbing = translate_text(text_for_dubbing, target_lang_code)
                                    st.session_state['translated_summary'] = text_for_dubbing
                                    st.session_state['target_lang_code'] = target_lang_code

                            audio = text_to_speech(text_for_dubbing, voice_gender, lang_for_dubbing, tts_engine)
                            if audio:
                                video = create_dubbed_video(st.session_state['original_video'], audio)
                                if video:
                                    with open(video, "rb") as f:
                                        st.session_state['dubbed_video_bytes'] = f.read()
                                        st.session_state['dubbed_video_name'] = f"dubbed_{display_lang}.mp4"
                                    try:
                                        os.remove(video)
                                        os.remove(audio)
                                    except:
                                        pass
                                    st.rerun()
                else:
                    st.success(f"✅ {display_lang} dubbed video is ready!")

            if 'dubbed_video_bytes' in st.session_state:
                st.markdown(f"**🎬 {display_lang} Dubbed Video**")
                col_vid = st.columns([1, 2, 1])[1]
                with col_vid:
                    st.video(st.session_state['dubbed_video_bytes'])
                st.download_button(
                    f"📥 Download Dubbed Video ({display_lang})",
                    st.session_state['dubbed_video_bytes'],
                    st.session_state['dubbed_video_name'],
                    "video/mp4",
                    use_container_width=True,
                    type="primary"
                )

    try:
        os.remove(temp_filename)
    except:
        pass

# ─── FOOTER ───
st.divider()
st.caption("🎓 LearnEaseAI ")