import cv2
import numpy as np
import time
import os
import uuid
import requests
import socket
import wave
import whisper
from ultralytics import YOLO
from paho.mqtt.client import Client
from gtts import gTTS

# =================== CONFIGURATIONS ===================
# ESP32-CAM
ESP32_CAM_URL = "http://192.168.252.106/capture"

# MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_TEXT = r"baarian/text_message"  # Topik utama untuk teks dan STT
MQTT_TOPIC_AUDIO = r"baarian/audio_message"
MQTT_TOPIC_RESET = r"baarian/reset_status"

# Model Path
MODEL_PATH = r"baarian_project\Baarian_Model_Nano.pt"

# Audio Streaming
HOST = '0.0.0.0'
PORT = 8888
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
CHUNK_DURATION = 5
CHUNK_SIZE = SAMPLE_RATE * SAMPLE_WIDTH * CHUNK_DURATION
GAIN_FACTOR = 200.0

# =================== Variabel global ===================
word = ""
sentence = []
audio_buffer = bytearray()
file_counter = 0
stream_socket = None
stream_conn = None

# =================== MQTT Setup ===================
client = Client(client_id=f"baarian-{uuid.uuid4()}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Terhubung!")
        client.subscribe(MQTT_TOPIC_RESET)
    else:
        print("MQTT Error:", rc)

def on_message(client, userdata, msg):
    global word, sentence
    if msg.topic == MQTT_TOPIC_RESET and msg.payload.decode() == "RESET":
        print("[RESET DARI ESP32] Word & Sentence direset.")
        word = ""
        sentence = []

client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# =================== Load Models ===================
# YOLO Model
model = YOLO(MODEL_PATH)

# Whisper Model
print("[!] Memuat model Whisper...")
stt_model = whisper.load_model("base")  # Menggunakan base untuk performa lebih cepat
print("[✔] Model Whisper berhasil dimuat.")

# =================== Helper Functions ===================
def esp32_capture(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame
        else:
            print("[ERROR] Gagal ambil gambar dari ESP32-CAM")
            return None
    except Exception as e:
        print(f"[ERROR] Exception ambil gambar: {e}")
        return None

def send_text(msg):
    if msg.strip():
        client.publish(MQTT_TOPIC_TEXT, msg)
        print(f"[MQTT] Teks dikirim: {msg}")

def send_audio(text, filename="output.wav"):
    tts = gTTS(text=text, lang="id")
    tts.save("temp.mp3")
    os.system(f'ffmpeg -y -i temp.mp3 -acodec pcm_u8 -ar 16000 -ac 1 {filename}')
    os.remove("temp.mp3")

    with open(filename, "rb") as f:
        while chunk := f.read(1024):
            client.publish(MQTT_TOPIC_AUDIO, chunk)
            time.sleep(0.1)
    client.publish(MQTT_TOPIC_AUDIO, b"END")
    print("[MQTT] Audio dikirim")

def setup_stream_socket():
    global stream_socket
    stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    stream_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    stream_socket.bind((HOST, PORT))
    stream_socket.listen(1)
    print("[~] Menunggu koneksi audio dari ESP32...")

def accept_audio_connection():
    global stream_conn
    if stream_socket:
        stream_conn, addr = stream_socket.accept()
        print(f"[✔] Koneksi audio diterima dari {addr}")
        return True
    return False

def transcribe_audio(filename):
    print(f"[~] Memulai transkripsi: {filename}")
    try:
        result = stt_model.transcribe(
            filename,
            language="id",
            fp16=False,
            suppress_blank=True,
            temperature=0.0
        )
        text = result["text"].strip()
        if text:
            print(f"[🗣️] Hasil STT: {text}")
            # Kirim hasil STT ke topik yang sama dengan deteksi objek
            send_text(text)
        else:
            print("[!] Tidak ada teks terdeteksi.")
    except Exception as e:
        print(f"[X] Error saat transkripsi: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def process_audio_stream():
    global audio_buffer, file_counter
    
    if not stream_conn:
        return
        
    try:
        raw_data = stream_conn.recv(CHUNK_SIZE)
        if not raw_data:
            return

        audio_buffer.extend(raw_data)

        if len(audio_buffer) >= CHUNK_SIZE:
            print("[+] Buffer audio penuh, memulai transkripsi...")
            chunk_data = audio_buffer[:CHUNK_SIZE]
            audio_buffer = audio_buffer[CHUNK_SIZE:]

            filename = f"temp_audio_{file_counter}.wav"
            raw_audio = np.frombuffer(chunk_data, dtype=np.int16).astype(np.float32)

            # Amplifikasi digital
            amplified_audio = raw_audio * GAIN_FACTOR
            amplified_audio = np.clip(amplified_audio, -32768, 32767)
            final_audio = amplified_audio.astype(np.int16)

            # Simpan sebagai WAV
            with wave.open(filename, 'w') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(SAMPLE_WIDTH)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(final_audio.tobytes())

            # Jalankan transkripsi
            transcribe_audio(filename)
            file_counter += 1
    except Exception as e:
        print(f"[X] Error audio stream: {e}")

# =================== Main Logic ===================
def run():
    global word, sentence
    
    # Setup audio socket
    setup_stream_socket()
    audio_connected = False
    
    last_detect = time.time()
    cooldown = 1.0

    try:
        while True:
            # Tangani koneksi audio
            if not audio_connected:
                audio_connected = accept_audio_connection()
            
            # Tangani streaming audio
            if audio_connected:
                process_audio_stream()
            
            # Tangani deteksi objek
            frame = esp32_capture(ESP32_CAM_URL)
            if frame is None:
                continue

            results = model.predict(frame, conf=0.5, verbose=False)
            boxes = results[0].boxes

            now = time.time()
            if boxes and now - last_detect > cooldown:
                label = results[0].names[int(boxes[0].cls.item())]
                word += label
                send_text(label)
                last_detect = now
                print(f"Detected: {label} | Word: {word}")

            if now - last_detect >= 3.5 and word:
                sentence.append(word)
                send_text(" ")
                print(f"[SPASI] Kata selesai: {word}")
                word = ""

            if now - last_detect >= 5.0 and sentence:
                kalimat = " ".join(sentence)
                send_text(kalimat)
                send_audio(kalimat)
                print(f"[KIRIM KALIMAT] {kalimat}")
                sentence = []

            # Display
            annotated = results[0].plot()
            cv2.putText(annotated, f"Word: {word}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.putText(annotated, f"Sentence: {' '.join(sentence)}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.putText(annotated, f"Audio: {'Connected' if audio_connected else 'Waiting'}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow("Baarian YOLO Detection + Audio STT", annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                word, sentence = "", []
                print("[RESET MANUAL] Word & Sentence direset.")
            elif key == ord('q'):
                break

            time.sleep(0.05)

    finally:
        client.loop_stop()
        client.disconnect()
        if stream_conn:
            stream_conn.close()
        if stream_socket:
            stream_socket.close()
        cv2.destroyAllWindows()
        print("Program selesai.")

# =================== Run it ===================
if __name__ == "__main__":
    run()