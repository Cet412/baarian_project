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
ESP32_CAM_URL = "http://192.168.84.165/stream"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_TEXT = "baarian/text_message"
MQTT_TOPIC_AUDIO = "baarian/audio_message"
MQTT_TOPIC_RESET = "baarian/reset_status"
MODEL_PATH = "myenv/Baarian-SIC-and-JISF/Baarian_Model_Light.pt"

# === Variabel global yang bisa di-reset === #
word = ""
sentence = []

# === MQTT Setup === #
client = Client(client_id=f"baarian-{uuid.uuid4()}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Terhubung!")
        client.subscribe(MQTT_TOPIC_RESET)  # ✅ Tambah listener reset
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

# === YOLO Model Load === #
model = YOLO(MODEL_PATH)

# === Helper Functions === #
def esp32_stream(url):
    response = requests.get(url, stream=True, timeout=10)
    bytes_data = b""
    for chunk in response.iter_content(1024):
        bytes_data += chunk
        a, b = bytes_data.find(b'\xff\xd8'), bytes_data.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                yield frame

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
        for frame in esp32_stream(ESP32_CAM_URL):
            results = model.predict(frame, conf=0.5, verbose=False)
            boxes = results[0].boxes

            now = time.time()
            if boxes and now - last_detect > cooldown:
                label = results[0].names[int(boxes[0].cls.item())]
                word += label
                send_text(label)
                last_detect = now
                print(f"Detected: {label} | Word: {word}")

            # Tambah spasi jika 3.5 detik tanpa huruf
            if now - last_detect >= 3.5 and word:
                sentence.append(word)
                send_text(" ")
                print(f"[SPASI] Kata selesai: {word}")
                word = ""

            # Kirim kalimat + audio jika idle 5 detik
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
            cv2.imshow("Baarian YOLO Detection", annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                word, sentence = "", []
                print("[RESET MANUAL] Word & Sentence direset.")
            elif key == ord('q'):
                break

    finally:
        client.loop_stop()
        client.disconnect()
        cv2.destroyAllWindows()
        print("Program selesai.")

# === Run it === #
if __name__ == "__main__":
    run()
