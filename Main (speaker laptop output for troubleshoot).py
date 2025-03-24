from ultralytics import YOLO
import cv2
import time
from gtts import gTTS

# Nama file output suara
AUDIO_FILE = r"C:\Users\Cetta\Documents\Coding\Python\Project\output.wav"

def text_to_speech(text):
    """Konversi teks ke suara dan simpan ke file .wav"""
    tts = gTTS(text=text, lang="id")
    tts.save(AUDIO_FILE)
    print(f"File suara disimpan: {AUDIO_FILE}")

# Load model YOLO
model = YOLO(r"myenv\Baarian-SIC-and-JISF\Baarian_BISINDO.pt")  # Sesuaikan dengan path model
cap = cv2.VideoCapture(0)

last_detection_time = time.time()
detected_word = ""

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    annotated_frame = frame.copy()
    current_time = time.time()

    # Deteksi setiap 2 detik agar tidak terlalu sering
    if current_time - last_detection_time >= 2.0:
        results = model.predict(frame, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()

        if len(results[0].boxes) > 0:
            detected_class = results[0].names[results[0].boxes[0].cls.item()]
            detected_word += detected_class  
            print(f"Detected: {detected_class} | Current Word: {detected_word}")
            last_detection_time = current_time

    cv2.putText(annotated_frame, f"Word: {detected_word}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("YOLOv8 Webcam Detection", annotated_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):  # Reset kata
        detected_word = ""
    elif key == ord('s'):  # Simpan sebagai audio
        if detected_word:
            text_to_speech(detected_word)
            print(f"Kata '{detected_word}' telah dikonversi ke suara dan disimpan!")
            detected_word = ""

cap.release()
cv2.destroyAllWindows()
