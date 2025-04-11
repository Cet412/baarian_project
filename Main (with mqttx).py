from ultralytics import YOLO
import cv2
import time
import paho.mqtt.client as mqtt
import uuid
from gtts import gTTS
import os

# --- Konfigurasi MQTT ---
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_TEXT = "baarian/text_message"
MQTT_TOPIC_AUDIO = "baarian/audio_message"
AUDIO_FILE = "output.wav"
CLIENT_ID = f"baarian-{uuid.uuid4()}"

# --- Setup MQTT ---
client = mqtt.Client(client_id=CLIENT_ID)

def on_connect(client, userdata, flags, rc):
    print("MQTT Terhubung!" if rc == 0 else f"MQTT Error: {rc}")

client.on_connect = on_connect

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print("MQTT Connection Error:", e)

# --- Kirim pesan teks ke MQTT ---
def send_text_to_mqtt(message):
    if message.strip():  # Jangan kirim spasi kosong doang
        client.publish(MQTT_TOPIC_TEXT, message)
        print(f"[MQTT Teks] {message}")

# --- Kirim audio ke MQTT ---
def send_audio_to_mqtt():
    try:
        with open(AUDIO_FILE, "rb") as f:
            while chunk := f.read(1024):  # atau 2048
                client.publish(MQTT_TOPIC_AUDIO, chunk, qos=1)
                time.sleep(0.1)  # tambahin delay sedikit

        client.publish(MQTT_TOPIC_AUDIO, b"END")
        print("[MQTT Audio] Terkirim!")
    except Exception as e:
        print("Gagal kirim audio:", e)

# --- Konversi teks ke suara dan WAV ---
def text_to_speech(text):
    if not text.strip():
        print("Teks kosong, TTS dibatalkan.")
        return
    temp_mp3 = "temp_audio.mp3"
    tts = gTTS(text=text, lang="id")
    tts.save(temp_mp3)
    convert_to_wav(temp_mp3, AUDIO_FILE)

def convert_to_wav(input_mp3, output_wav):
    os.system(f'ffmpeg -y -i {input_mp3} -acodec pcm_u8 -ar 16000 -ac 1 {output_wav}')
    os.remove(input_mp3)

# --- Load YOLO Model ---
model = YOLO(r"myenv\Baarian-SIC-and-JISF\Baarian_Model_Light.pt")
cap = cv2.VideoCapture(0)

# --- Variabel Utama ---
last_detection_time = time.time()
last_char_detected_time = 0
DETECTION_COOLDOWN = 1.0  # jeda antar huruf biar ga spam

current_word = ""
detected_sentence = []

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()

        current_time = time.time()

        if len(results[0].boxes) > 0:
            if current_time - last_char_detected_time >= DETECTION_COOLDOWN:
                detected_class = results[0].names[int(results[0].boxes[0].cls.item())]
                current_word += detected_class
                send_text_to_mqtt(detected_class)
                last_detection_time = current_time
                last_char_detected_time = current_time
                print(f"Detected: {detected_class} | Word: {current_word}")

        # Tambahkan kata jika 3.5 detik tidak ada deteksi
        if current_time - last_detection_time >= 3.5 and current_word:
            detected_sentence.append(current_word)
            send_text_to_mqtt(" ")  # Untuk spasi di LCD
            print(f"[SPASI] Kata selesai: {current_word}")
            current_word = ""

        # Kirim kalimat & audio jika 5 detik tidak ada input baru
        if current_time - last_detection_time >= 5.0 and detected_sentence:
            full_sentence = " ".join(detected_sentence)
            send_text_to_mqtt(full_sentence)
            text_to_speech(full_sentence)
            send_audio_to_mqtt()
            print(f"[KIRIM KALIMAT] {full_sentence}")
            detected_sentence = []

        # --- Tampilan ---
        cv2.putText(annotated_frame, f"Word: {current_word}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Sentence: {' '.join(detected_sentence)}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("YOLOv8 Baarian Detection", annotated_frame)

        # --- Key Event ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):
            current_word = ""
            detected_sentence = []
            print("[RESET] Semua teks dihapus.")
        elif key == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    client.loop_stop()
    client.disconnect()
    print("Program selesai.")
