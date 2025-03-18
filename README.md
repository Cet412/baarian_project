## 📌 Instalasi dan Persyaratan
### 1️⃣ Persiapan Sistem
Pastikan Anda memiliki **Python 3.8+** dan **MicroPython** yang sudah di-flash ke ESP32.

### 2️⃣ Instalasi Library Python (Untuk PC)
Jalankan perintah berikut di terminal:
```sh
pip install ultralytics opencv-python paho-mqtt gtts
```

### 3️⃣ Instalasi Library di ESP32
Unggah file **machine_i2c_lcd.py** ke ESP32 lalu jalankan perintah berikut di MicroPython:
```sh
import upip
upip.install('umqtt.simple')
```

## 🚀 Cara Penggunaan
### 1️⃣ Jalankan Model di PC
```sh
python main.py
```

#### 🔹 Tombol Kendali di PC
- `r` : Reset kata yang sedang dikenali.
- `u` : Tambah kata ke kalimat.
- `s` : Kirim kata ke MQTT dan ubah ke suara.
- `c` : Kirim seluruh kalimat ke MQTT dan ubah ke suara.
- `x` : Kirim kata dan reset deteksi.
- `z` : Kirim kalimat dan reset deteksi.
- `q` : Keluar dari program.

### 2️⃣ Jalankan ESP32 dan Terima Data
ESP32 akan secara otomatis menampilkan teks yang diterima dari MQTT di LCD dan menyimpan file audio.

## 📡 Konfigurasi MQTT
Broker MQTT yang digunakan adalah **broker.emqx.io**.
- **Topik Teks:** `baarian/text_message`
- **Topik Audio:** `baarian/audio_message`

## 📌 Arsitektur Sistem
1. Model YOLOv8 mendeteksi gerakan tangan dan mengonversinya ke teks.
2. Teks dikirim melalui MQTT ke ESP32.
3. Komputer menghasilkan suara menggunakan gTTS dan mengirimkannya ke ESP32 melalui MQTT.
4. ESP32 menampilkan teks di LCD dan menyimpan file audio.

## 🛠️ Hardware yang Digunakan
- **ESP32**
- **LCD I2C 16x2**
- **Kamera (Webcam/ESP32-CAM)**
- **PC/Laptop dengan Python**

## 🔧 Troubleshooting
Jika terjadi error saat menjalankan model YOLO:
- Pastikan file `Baarian_Model.pt` ada di direktori yang benar.
- Gunakan Python 3.8+ dan pastikan library yang dibutuhkan sudah terinstal.
- Cek koneksi ke MQTT broker dengan perintah:
  ```sh
  ping broker.emqx.io
  ```

Jika ESP32 tidak menampilkan teks:
- Pastikan WiFi terhubung dengan benar.
- Periksa apakah ESP32 sudah berlangganan ke topik MQTT.

## 📜 Lisensi
Proyek ini dibuat untuk keperluan riset dan edukasi.

---
🚀 **Baarian** - Membantu komunikasi antara pengguna bahasa isyarat dan masyarakat luas.

