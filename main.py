import cv2
import numpy as np
import time
import os
import uuid
import requests
import threading
from dotenv import load_dotenv
from ultralytics import YOLO
from paho.mqtt.client import Client, CallbackAPIVersion
from gtts import gTTS

# === LOAD ENVIRONMENT CONFIGURATIONS === #
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC_TEXT = os.getenv("MQTT_TOPIC_TEXT", "baarian/text_message")
MQTT_TOPIC_AUDIO = os.getenv("MQTT_TOPIC_AUDIO", "baarian/audio_message")
MQTT_TOPIC_RESET = os.getenv("MQTT_TOPIC_RESET", "baarian/reset_status")
ESP32_CAM_URL = os.getenv("ESP32_CAM_URL", "http://10.105.18.106/capture")
USE_WEBCAM = os.getenv("USE_WEBCAM", "True").lower() == "true"

# Cross-platform Path Resolution
MODEL_PATH = os.path.join("AI Model", "Baarian_Model_Nano.pt")
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join("baarian_project", "AI Model", "Baarian_Model_Nano.pt")

# === GLOBAL STATES === #
word = ""
sentence = []
mqtt_connected = False

# === MQTT CLIENT SETUP (V2) === #
client = Client(
    callback_api_version=CallbackAPIVersion.VERSION2,
    client_id=f"baarian-{uuid.uuid4()}"
)

def on_connect(client, userdata, flags, reason_code, properties):
    global mqtt_connected
    if reason_code == 0:
        print("✅ MQTT Connected!")
        mqtt_connected = True
        client.subscribe(MQTT_TOPIC_RESET)
    else:
        print(f"❌ MQTT Connection Error: {reason_code}")
        mqtt_connected = False

def on_message(client, userdata, msg):
    global word, sentence
    if msg.topic == MQTT_TOPIC_RESET and msg.payload.decode() == "RESET":
        print("[RESET MQTT] Word & sentence cleared.")
        word, sentence = "", []

def on_disconnect(client, userdata, flags, reason_code, properties):
    global mqtt_connected
    print(f"🔌 MQTT Disconnected: {reason_code}")
    mqtt_connected = False

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

def connect_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        return True
    except Exception as e:
        print(f"❌ MQTT connection failure: {e}")
        return False

# === CAPTURE SOURCE HANDLING === #
def get_frame(cap_local, url):
    if USE_WEBCAM:
        if cap_local and cap_local.isOpened():
            ret, frame = cap_local.read()
            return frame if ret else None
        return None
    else:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception:
            return None
    return None

# === MQTT PUBLISH FUNCTIONS === #
def send_text(msg):
    if mqtt_connected and msg.strip():
        try:
            client.publish(MQTT_TOPIC_TEXT, msg)
            print(f"[MQTT SEND] Text: {msg}")
        except Exception as e:
            print(f"❌ Error sending text: {e}")

def _async_send_audio(text, filename="output.wav"):
    if not mqtt_connected:
        return
    try:
        tts = gTTS(text=text, lang="id")
        tts.save("temp.mp3")
        
        # Audio conversion using FFmpeg
        convert_cmd = f'ffmpeg -y -i temp.mp3 -acodec pcm_u8 -ar 16000 -ac 1 {filename}'
        if os.system(convert_cmd) == 0:
            os.remove("temp.mp3")
            with open(filename, "rb") as f:
                while chunk := f.read(1024):
                    client.publish(MQTT_TOPIC_AUDIO, chunk)
                    time.sleep(0.05)
            client.publish(MQTT_TOPIC_AUDIO, b"END")
            print("✅ Audio sent via MQTT")
        
        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        print(f"❌ Failed to process or send audio: {e}")

def send_audio(text):
    # Non-blocking execution via thread isolation
    thread = threading.Thread(target=_async_send_audio, args=(text,))
    thread.daemon = True
    thread.start()

# === MAIN PIPELINE === #
def run():
    global word, sentence
    if not connect_mqtt():
        return

    try:
        model = YOLO(MODEL_PATH)
        print("🤖 YOLO model loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    cap = cv2.VideoCapture(0) if USE_WEBCAM else None
    last_detect = time.time()
    cooldown = 1.0

    print(f"🚀 System running on: {'Local Webcam' if USE_WEBCAM else 'ESP32-CAM'}")

    try:
        while True:
            frame = get_frame(cap, ESP32_CAM_URL)
            if frame is None:
                time.sleep(0.01)
                continue

            results = model.predict(frame, conf=0.5, verbose=False)
            boxes = results[0].boxes
            now = time.time()

            if boxes and now - last_detect > cooldown:
                label = results[0].names[int(boxes[0].cls.item())]
                word += label
                send_text(word)
                last_detect = now
                print(f"Detected: {label} | Word: {word}")

            # Automatic Space Insertion (3.5 seconds)
            if now - last_detect >= 3.5 and word:
                sentence.append(word)
                send_text(" ")
                word = ""

            # Sentence Completion & Audio Transmission (5 seconds)
            if now - last_detect >= 5.0 and sentence:
                kalimat = " ".join(sentence)
                send_text(kalimat)
                send_audio(kalimat)
                sentence = []

            # Rendering Visual Output
            annotated = results[0].plot()
            cv2.putText(annotated, f"Word: {word}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated, f"Sentence: {' '.join(sentence)}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            status_text = "🟢 MQTT OK" if mqtt_connected else "🔴 MQTT ERROR"
            cv2.putText(annotated, status_text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if mqtt_connected else (0, 0, 255), 2)

            cv2.imshow("Baarian YOLO Detection", annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                word, sentence = "", []
                print("🔄 [MANUAL RESET] Word & sentence cleared.")
            elif key == ord('q'):
                break

    finally:
        if cap:
            cap.release()
        client.loop_stop()
        client.disconnect()
        cv2.destroyAllWindows()
        print("Program completed.")

if __name__ == "__main__":
    run()