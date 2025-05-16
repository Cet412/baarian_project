# Baarian Project

Baarian adalah sistem interaktif berbasis ESP32 yang memungkinkan komunikasi dua arah melalui teks dan audio menggunakan MQTT. Proyek ini terdiri dari dua bagian utama:

1. **ESP32 dengan LCD dan DAC**: Menampilkan pesan teks dan memutar audio yang diterima melalui MQTT.
2. **ESP32-CAM**: Mengirimkan gambar melalui HTTP dan dapat diintegrasikan dengan sistem pengenalan wajah atau objek.

---

## Struktur Proyek

```
baarian_project/
├── ESP32-LCD-MQTT.py         # Kode utama untuk ESP32 dengan LCD dan DAC
├── machine_i2c_lcd.py        # Library untuk mengontrol LCD via I2C
├── lcd_api.py                # API tambahan untuk LCD
├── ESP32cam/                 # Folder berisi kode untuk ESP32-CAM
│   └── ESP32cam.ino          # Kode utama untuk ESP32-CAM
├── models/                   # Folder berisi model AI (jika ada)
│   ├── Baarian_Model.pt
│   └── Baarian_Model_Light.pt
├── Streamlit/                # Aplikasi web untuk interaksi pengguna
│   └── app.py
├── requirements.txt          # Daftar dependensi Python
└── README.md                 # Dokumentasi proyek
```

---

## Persyaratan

### Perangkat Keras

* ESP32 Dev Board dengan DAC dan LCD (misalnya, ESP32-WROOM-32)
* ESP32-CAM (misalnya, AI-Thinker)
* LCD I2C 16x2
* PAM8403 Amplifier
* Speaker
* Kabel jumper dan breadboard

### Perangkat Lunak

* MicroPython firmware untuk ESP32
* Arduino IDE atau PlatformIO (untuk ESP32-CAM)
* Python 3.8+
* Thonny IDE (opsional, untuk mengunggah file ke ESP32)

---

## Instalasi

### 1. Menyiapkan ESP32 dengan LCD dan DAC

1. Flash MicroPython ke ESP32.
2. Gunakan Thonny IDE untuk mengunggah file berikut ke ESP32:

   * `ESP32-LCD-MQTT.py`
   * `machine_i2c_lcd.py`
   * `lcd_api.py`
3. Edit `ESP32-LCD-MQTT.py` untuk menyesuaikan SSID dan password WiFi Anda.
4. Jalankan `ESP32-LCD-MQTT.py` sebagai program utama.

### 2. Menyiapkan ESP32-CAM

1. Buka `ESP32cam.ino` di Arduino IDE.
2. Pilih board "AI Thinker ESP32-CAM" dan port yang sesuai.
3. Edit SSID dan password WiFi di kode.
4. Unggah kode ke ESP32-CAM.
5. Setelah berhasil terhubung ke WiFi, ESP32-CAM akan menampilkan alamat IP di Serial Monitor.

### 3. Menyiapkan Aplikasi Streamlit (Opsional)

1. Pastikan Python 3.8+ terinstal di komputer Anda.
2. Instal dependensi dengan perintah:

   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi Streamlit:

   ```bash
   streamlit run Streamlit/app.py
   ```

---

## Penggunaan

1. Nyalakan ESP32 dan ESP32-CAM.
2. ESP32 akan terhubung ke WiFi dan menunggu pesan dari broker MQTT.
3. ESP32-CAM akan mengirimkan gambar melalui HTTP yang dapat diakses melalui alamat IP yang ditampilkan.
4. Gunakan aplikasi Streamlit untuk mengirimkan pesan teks atau audio ke ESP32 melalui MQTT.
5. ESP32 akan menampilkan pesan di LCD dan memutar audio melalui speaker.

---

## Akses Kamera

Setelah ESP32-CAM terhubung ke WiFi, Anda dapat mengakses gambar melalui browser dengan mengunjungi:

```
http://<alamat-ip-esp32-cam>/capture
```

Gantilah `<alamat-ip-esp32-cam>` dengan alamat IP yang ditampilkan di Serial Monitor.

---

## Pengujian

* Gunakan MQTT client seperti MQTTX atau MQTT Explorer untuk mengirim pesan ke topik yang sesuai.
* Pastikan ESP32 menerima dan memproses pesan dengan benar.
* Uji koneksi kamera dengan mengakses URL yang disebutkan di atas.

---

## Kontak

Untuk pertanyaan atau saran, silakan hubungi [email@example.com](cettaanantamaulana@gmail.com).

---
