import cv2
import numpy as np
import time
import os
import uuid
import requests
from ultralytics import YOLO
from paho.mqtt.client import Client
from gtts import gTTS

# === CONFIGURATIONS === #
ESP32_CAM_URL = "http://192.168.252.106/capture"  # GANTI KE /capture
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_TEXT = r"baarian/text_message"
MQTT_TOPIC_AUDIO = r"baarian/audio_message"
MQTT_TOPIC_RESET = r"baarian/reset_status"
MODEL_PATH = r"baarian_project\Baarian_Model_Nano.pt"

# === Variabel global === #
word = ""
sentence = []

# === MQTT Setup === #
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

# === Load YOLO Model === #
model = YOLO(MODEL_PATH)

# === Helper Functions === #
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
        print(f"[MQTT] Teks: {msg}")

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

# === Main Logic === #
def run():
    global word, sentence
    last_detect = time.time()
    cooldown = 1.0

    try:
        while True:
            frame = esp32_capture(ESP32_CAM_URL)
            if frame is None:
                continue

            results = model.predict(frame, conf=0.5, verbose=False)
            boxes = results[0].boxes

            now = time.time()
            if boxes and now - last_detect > cooldown:
                label = results[0].names[int(boxes[0].cls.item())]
                word += label
                send_text(word)  # Kirim word yang sudah bertambah, bukan per huruf
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

            annotated = results[0].plot()
            cv2.putText(annotated, f"Word: {word}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.putText(annotated, f"Sentence: {' '.join(sentence)}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow("Baarian YOLO Detection", annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                word, sentence = "", []
                print("[RESET MANUAL] Word & Sentence direset.")
            elif key == ord('q'):
                break

            time.sleep(0.05)  # kecilin delay antara capture biar ga spam request

    finally:
        client.loop_stop()
        client.disconnect()
        cv2.destroyAllWindows()
        print("Program selesai.")

# === Run it === #
if __name__ == "__main__":
    run()
