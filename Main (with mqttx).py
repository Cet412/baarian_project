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
            while chunk := f.read(512):  # Kirim dalam potongan 512 byte
                client.publish(MQTT_TOPIC_AUDIO, chunk)
                time.sleep(0.1)  # Jeda untuk menghindari buffer penuh
            
        client.publish(MQTT_TOPIC_AUDIO, b"END")  # Sinyal akhir
        print("File audio dikirim ke MQTT dalam format bytes!")
    except Exception as e:
        print(f"Error saat mengirim file audio ke MQTT: {e}")

def text_to_speech(text):
    temp_mp3 = "temp_audio.mp3"
    tts = gTTS(text=text, lang="id")
    tts.save(temp_mp3)  # Simpan sebagai MP3
    print(f"File MP3 dibuat: {temp_mp3}")
    convert_to_wav(temp_mp3, AUDIO_FILE)

def convert_to_wav(input_mp3, output_wav):
    command = f'ffmpeg -y -i {input_mp3} -acodec pcm_s16le -ar 16000 -ac 1 {output_wav}'
    os.system(command)
    os.remove(input_mp3)  # Hapus file MP3 sementara
    print(f"File dikonversi ke WAV: {output_wav}")

# Load model YOLO
model = YOLO(r"myenv\Baarian-SIC-and-JISF\Baarian_Model.pt")
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
            detected_class = results[0].names[int(results[0].boxes[0].cls.item())]
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
    elif key in [ord('s'), ord('x')]:  # Kirim kata ke MQTT & TTS
        if detected_word:
            send_text_to_mqtt(detected_word)
            text_to_speech(detected_word)
            send_audio_to_mqtt()
            if key == ord('x'):
                detected_word = ""  # Reset setelah dikirim
    elif key in [ord('c'), ord('z')]:  # Kirim kalimat ke MQTT & TTS
        if detected_sentence:
            full_sentence = " ".join(detected_sentence)
            send_text_to_mqtt(full_sentence)
            text_to_speech(full_sentence)
            send_audio_to_mqtt()
            if key == ord('z'):
                detected_sentence = []  # Reset setelah dikirim

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()