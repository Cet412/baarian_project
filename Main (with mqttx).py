from ultralytics import YOLO
import cv2
import time
import paho.mqtt.client as mqtt
from gtts import gTTS
import base64

# Konfigurasi MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_TEXT = "baarian/text_message"
MQTT_TOPIC_AUDIO = "baarian/audio_message"
AUDIO_FILE = "output.wav"

# Inisialisasi MQTT Client
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Terhubung ke MQTT broker")
    else:
        print(f"Error MQTT, kode: {rc}")

client.on_connect = on_connect
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"Error saat menghubungkan ke MQTT: {e}")

def send_text_to_mqtt(message):
    client.publish(MQTT_TOPIC_TEXT, message)
    print(f"Data teks dikirim ke MQTT: {message}")

def send_audio_to_mqtt():
    try:
        with open(AUDIO_FILE, "rb") as f:
            while chunk := f.read(512):  # Kirim dalam potongan 512 byte
                client.publish(MQTT_TOPIC_AUDIO, chunk)
                time.sleep(0.1)  # Jeda kecil untuk menghindari buffer penuh
            
        client.publish(MQTT_TOPIC_AUDIO, b"END")  # Kirim sinyal akhir
        print("File audio dikirim ke MQTT dalam format bytes!")
    except Exception as e:
        print(f"Error saat mengirim file audio ke MQTT: {e}")

def text_to_speech(text):
    tts = gTTS(text=text, lang="id")
    tts.save(AUDIO_FILE)
    print(f"File suara dibuat: {AUDIO_FILE}")

# Load model YOLO
model = YOLO(r"Baarian_Model.pt")
cap = cv2.VideoCapture(0)

last_detection_time = time.time()
detected_word = ""
detected_sentence = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    annotated_frame = frame.copy()
    current_time = time.time()

    if current_time - last_detection_time >= 2.0:
        results = model.predict(frame, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()

        if len(results[0].boxes) > 0:
            detected_class = results[0].names[results[0].boxes[0].cls.item()]
            detected_word += detected_class  
            print(f"Detected: {detected_class} | Current Word: {detected_word}")
            last_detection_time = current_time

    cv2.putText(annotated_frame, f"Word: {detected_word}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(annotated_frame, f"Sentence: {' '.join(detected_sentence)}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("YOLOv8 Webcam Detection", annotated_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        detected_word = ""
    elif key == ord('u'):
        if detected_word:
            detected_sentence.append(detected_word)
            detected_word = ""
            print(f"Kata ditambahkan ke kalimat: {' '.join(detected_sentence)}")
    elif key == ord('s'):
        if detected_word:
            send_text_to_mqtt(detected_word)
            text_to_speech(detected_word)
            send_audio_to_mqtt()
    elif key == ord('c'):
        if detected_sentence:
            full_sentence = " ".join(detected_sentence)
            send_text_to_mqtt(full_sentence)
            text_to_speech(full_sentence)
            send_audio_to_mqtt()
    elif key == ord('x'):
        if detected_word:
            send_text_to_mqtt(detected_word)
            text_to_speech(detected_word)
            send_audio_to_mqtt()
            detected_word = ""
    elif key == ord('z'):
        if detected_sentence:
            full_sentence = " ".join(detected_sentence)
            send_text_to_mqtt(full_sentence)
            text_to_speech(full_sentence)
            send_audio_to_mqtt()
            detected_sentence = []

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()