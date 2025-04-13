import cv2
import time
import uuid
import os
import paho.mqtt.client as mqtt
from gtts import gTTS
from ultralytics import YOLO

# --- MQTT CONFIG ---
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_TEXT = "baarian/text_message"
MQTT_TOPIC_AUDIO = "baarian/audio_message"
MQTT_TOPIC_RESET = "baarian/reset_status"  # ✅ Tambahan topik reset
AUDIO_FILE = "output.wav"
CLIENT_ID = f"baarian-{uuid.uuid4()}"

# --- Variabel global yang bisa di-reset ---
detected_word = ""
full_sentence = []

# --- MQTT SETUP ---
client = mqtt.Client(client_id=CLIENT_ID)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Terhubung!")
        client.subscribe(MQTT_TOPIC_RESET)  # ✅ Subscribe ke topik reset
    else:
        print(f"MQTT Error: {rc}")

def on_message(client, userdata, msg):
    global detected_word, full_sentence
    if msg.topic == MQTT_TOPIC_RESET and msg.payload.decode() == "RESET":
        print("[MQTT RESET] Diterima dari ESP32, teks dihapus.")
        detected_word = ""
        full_sentence = []

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print("MQTT Connection Error:", e)

def send_text_to_mqtt(message):
    if message.strip():
        client.publish(MQTT_TOPIC_TEXT, message)
        print(f"[MQTT Teks] {message}")

def send_audio_to_mqtt():
    try:
        with open(AUDIO_FILE, "rb") as f:
            while chunk := f.read(1024):
                client.publish(MQTT_TOPIC_AUDIO, chunk, qos=1)
                time.sleep(0.1)
        client.publish(MQTT_TOPIC_AUDIO, b"END")
        print("[MQTT Audio] Terkirim!")
    except Exception as e:
        print("Gagal kirim audio:", e)

def text_to_speech(text):
    if not text.strip():
        print("Teks kosong, TTS dibatalkan.")
        return
    temp_mp3 = "temp_audio.mp3"
    tts = gTTS(text=text.lower(), lang="id")
    tts.save(temp_mp3)
    convert_to_wav(temp_mp3, AUDIO_FILE)

def convert_to_wav(input_mp3, output_wav):
    os.system(f'ffmpeg -y -i {input_mp3} -acodec pcm_u8 -ar 16000 -ac 1 {output_wav}')
    os.remove(input_mp3)

# --- YOLO SETUP ---
model = YOLO("myenv\Baarian-SIC-and-JISF\Baarian_Model_Light.pt")
cap = cv2.VideoCapture(0)

last_detection_time = time.time()
last_char_detected_time = 0
DETECTION_COOLDOWN = 1.0

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        current_time = time.time()
        results = model.predict(frame, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()

        # Deteksi huruf
        if len(results[0].boxes) > 0:
            if current_time - last_char_detected_time >= DETECTION_COOLDOWN:
                detected_class = results[0].names[int(results[0].boxes[0].cls.item())]
                detected_word += detected_class
                send_text_to_mqtt(detected_word)
                last_char_detected_time = current_time
                last_detection_time = current_time
                print(f"Detected: {detected_class} | Word: {detected_word}")

        # Word selesai setelah 3.5 detik tidak mendeteksi
        if current_time - last_char_detected_time >= 3.5 and detected_word:
            full_sentence.append(detected_word)
            print(f"[KATA SELESAI] {detected_word}")
            detected_word = ""

        # Kalimat selesai setelah 5 detik idle
        if current_time - last_detection_time >= 5.0 and full_sentence:
            kalimat = " ".join(full_sentence)
            send_text_to_mqtt(kalimat)
            text_to_speech(kalimat)
            send_audio_to_mqtt()
            print(f"[KIRIM KALIMAT] {kalimat}")
            full_sentence = []

        # --- Tampilan frame ---
        cv2.putText(annotated_frame, f"Kata: {detected_word}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Kalimat: {' '.join(full_sentence)}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Baarian - YOLO Detection", annotated_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):
            detected_word = ""
            full_sentence = []
            print("[RESET MANUAL] Semua teks dihapus.")
        elif key == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    client.loop_stop()
    client.disconnect()
    print("Program selesai.")
