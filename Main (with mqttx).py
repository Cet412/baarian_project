from ultralytics import YOLO
import cv2
import time
import paho.mqtt.client as mqtt
import uuid  # Untuk membuat Client ID unik secara otomatis
from gtts import gTTS
import os

# Konfigurasi MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_TEXT = "baarian/text_message"
MQTT_TOPIC_AUDIO = "baarian/audio_message"
AUDIO_FILE = "output.wav"

CLIENT_ID = f"baarian-{uuid.uuid4()}"

# Inisialisasi MQTT Client
client = mqtt.Client(client_id=CLIENT_ID)

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
            while chunk := f.read(512):
                client.publish(MQTT_TOPIC_AUDIO, chunk)
                time.sleep(0.1)
        client.publish(MQTT_TOPIC_AUDIO, b"END")
        print("File audio dikirim ke MQTT dalam format bytes!")
    except Exception as e:
        print(f"Error saat mengirim file audio ke MQTT: {e}")

def text_to_speech(text):
    temp_mp3 = "temp_audio.mp3"
    tts = gTTS(text=text, lang="id")
    tts.save(temp_mp3)
    print(f"File MP3 dibuat: {temp_mp3}")
    convert_to_wav(temp_mp3, AUDIO_FILE)

def convert_to_wav(input_mp3, output_wav):
    command = f'ffmpeg -y -i {input_mp3} -acodec pcm_s16le -ar 16000 -ac 1 {output_wav}'
    os.system(command)
    os.remove(input_mp3)
    print(f"File dikonversi ke WAV: {output_wav}")

# Load model YOLO
model = YOLO(r"myenv\Baarian-SIC-and-JISF\Baarian_Model.pt")
cap = cv2.VideoCapture(0)

last_detection_time = time.time()
detected_sentence = []
current_word = ""

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    annotated_frame = frame.copy()
    current_time = time.time()

    results = model.predict(frame, conf=0.5, verbose=False)
    annotated_frame = results[0].plot()

    if len(results[0].boxes) > 0:
        detected_class = results[0].names[int(results[0].boxes[0].cls.item())]
        current_word += detected_class  # Tambahkan huruf
        send_text_to_mqtt(detected_class)
        last_detection_time = current_time
        print(f"Detected: {detected_class} | Current Word: {current_word}")
    
    if current_time - last_detection_time >= 3.5 and current_word:
        detected_sentence.append(current_word)
        send_text_to_mqtt(" ")
        print(f"Spasi otomatis. Kata: {current_word}")
        current_word = ""
    
    if current_time - last_detection_time >= 5.0 and detected_sentence:
        full_sentence = " ".join(detected_sentence)
        send_text_to_mqtt(full_sentence)
        text_to_speech(full_sentence)
        send_audio_to_mqtt()
        detected_sentence = []
        print(f"Kalimat dikirim: {full_sentence}")
    
    cv2.putText(annotated_frame, f"Word: {current_word}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(annotated_frame, f"Sentence: {' '.join(detected_sentence)}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("YOLOv8 Webcam Detection", annotated_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('r'):
        current_word = ""
        detected_sentence = []
        print("Reset deteksi huruf dan kalimat")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()