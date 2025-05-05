import socket
import numpy as np
import wave
import whisper
import os
import time
import paho.mqtt.client as mqtt

# =================== Konfigurasi Jaringan ===================
HOST = '0.0.0.0'
PORT = 8888

# =================== Konfigurasi MQTT ===================
MQTT_BROKER = "broker.emqx.io"  # Ganti jika perlu
MQTT_PORT = 1883
MQTT_TOPIC = "baarian/text_message"  # Topik untuk hasil STT
MQTT_CLIENT_ID = "pc_stt_client_675^&$hdw"

# =================== Konfigurasi Audio ===================
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
CHUNK_DURATION = 5
CHUNK_SIZE = SAMPLE_RATE * SAMPLE_WIDTH * CHUNK_DURATION
GAIN_FACTOR = 20.0
audio_buffer = bytearray()
file_counter = 0

# Inisialisasi MQTT Client
# Ganti inisialisasi MQTT Client menjadi:
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, MQTT_CLIENT_ID)

def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[✔] Terhubung ke Broker MQTT")
    else:
        print(f"[X] Gagal terhubung ke MQTT, kode error: {rc}")

mqtt_client.on_connect = on_mqtt_connect

# Load Model Whisper
print("[!] Memuat model Whisper...")
model = whisper.load_model("base")
print("[✔] Model Whisper berhasil dimuat.")

# Setup Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((HOST, PORT))
sock.listen(1)
print("[~] Menunggu koneksi dari ESP32...")

# Koneksi MQTT
print("[~] Menghubungkan ke MQTT Broker...")
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

conn, addr = sock.accept()
print(f"[✔] Koneksi diterima dari {addr}")

# Fungsi Transkripsi + Kirim ke MQTT
def transcribe_and_publish(filename):
    print(f"[~] Memulai transkripsi: {filename}")
    try:
        result = model.transcribe(
            filename,
            language="id",
            fp16=False,
            suppress_blank=True,
            temperature=0.0
        )
        text = result["text"].strip()
        
        if text:
            print(f"[🗣️] Hasil STT: {text}")
            # Kirim hasil ke MQTT
            mqtt_client.publish(MQTT_TOPIC, text)
            print(f"[📤] Hasil dikirim ke MQTT topic: {MQTT_TOPIC}")
        else:
            print("[!] Tidak ada teks terdeteksi.")
            
    except Exception as e:
        print(f"[X] Error saat transkripsi: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# Main Loop
try:
    while True:
        raw_data = conn.recv(CHUNK_SIZE)
        if not raw_data:
            break

        audio_buffer.extend(raw_data)

        if len(audio_buffer) >= CHUNK_SIZE:
            print("[+] Buffer penuh, memulai transkripsi...")

            chunk_data = audio_buffer[:CHUNK_SIZE]
            audio_buffer = audio_buffer[CHUNK_SIZE:]

            filename = f"temp_audio_{file_counter}.wav"
            raw_audio = np.frombuffer(chunk_data, dtype=np.int16).astype(np.float32)

            # Normalisasi RMS
            rms = np.sqrt(np.mean(raw_audio ** 2))
            if rms > 0:
                normalized_audio = raw_audio / rms * 0.5
            else:
                normalized_audio = raw_audio

            # Gain Digital
            amplified_audio = normalized_audio * GAIN_FACTOR
            amplified_audio = np.clip(amplified_audio, -32768, 32767)
            final_audio = amplified_audio.astype(np.int16)

            # Simpan sebagai WAV
            with wave.open(filename, 'w') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(SAMPLE_WIDTH)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(final_audio.tobytes())

            # Jalankan transkripsi dan kirim ke MQTT
            transcribe_and_publish(filename)
            file_counter += 1

except KeyboardInterrupt:
    print("\n[!] Program dihentikan oleh pengguna.")
finally:
    conn.close()
    sock.close()
    mqtt_client.disconnect()
    mqtt_client.loop_stop()