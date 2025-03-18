## 📌 Instalasi dan Persyaratan
### 1️⃣ Persiapan Sistem
Pastikan Anda memiliki **Python 3.8+** dan **MicroPython** yang sudah di-flash ke ESP32.

### 2️⃣ Instalasi Library Python (Untuk PC)
Jalankan perintah berikut di terminal:
```sh
pip install ultralytics opencv-python paho-mqtt gtts
```

### **📌 Cara Instalasi Library di ESP32 menggunakan Thonny IDE**  
---

### **🛠 1️⃣ Persiapan Awal**
Sebelum memulai, pastikan sudah:
✅ Menginstal **Thonny IDE**  
✅ Menghubungkan **ESP32 ke komputer** melalui kabel USB  
✅ Menginstal **MicroPython firmware** di ESP32  
✅ Menyiapkan file **machine_i2c_lcd.py** di komputer  

---

### **📂 2️⃣ Mengunggah File `machine_i2c_lcd.py` ke ESP32**
1️⃣ **Buka Thonny IDE**  
2️⃣ **Hubungkan ESP32 ke Thonny**:
   - Klik **Tools** → **Options...**  
   - Pilih tab **Interpreter**  
   - Pada "Interpreter", pilih **MicroPython (ESP32)**  
   - Pada "Port", pilih COM port ESP32 (misalnya: COM3 atau /dev/ttyUSB0)  
   - Klik **OK**  

3️⃣ **Buka File Manager ESP32**:
   - Klik **View** → **Files**  
   - Akan muncul **File Explorer**, yang menampilkan file di komputer dan di ESP32  

4️⃣ **Unggah file `machine_i2c_lcd.py` ke ESP32**:
   - Di panel kiri (komputer), cari file **machine_i2c_lcd.py**  
   - Klik kanan file tersebut → Pilih **Upload to / (ESP32)**  
   - File akan diunggah ke ESP32  

💡 **Cek apakah file berhasil diunggah**:  
   - Ketik di Thonny Shell:  
     ```python
     import os
     os.listdir()
     ```
   - Jika `machine_i2c_lcd.py` muncul, berarti sudah berhasil ter-upload.  

---

### **📥 3️⃣ Instal Library `umqtt.simple` di ESP32**
Sekarang, kita akan menginstal library **umqtt.simple** menggunakan **upip**.  

1️⃣ **Buka Thonny Shell**  
2️⃣ **Jalankan perintah berikut di MicroPython**:
   ```python
   import upip
   upip.install('umqtt.simple')
   ```
3️⃣ **Tunggu beberapa detik** sampai proses instalasi selesai.  
4️⃣ Jika berhasil, tidak akan ada error, dan library sudah bisa digunakan di ESP32.

---

### **✅ 4️⃣ Cek Apakah Library Sudah Terinstal**
Untuk memastikan `umqtt.simple` sudah terinstal, jalankan di Thonny:  
```python
import umqtt.simple
print("Library umqtt.simple berhasil diinstal!")
```
Jika tidak ada error, berarti library sudah siap digunakan.

---

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
- **LCD I2C 20x4**
- **Kamera (Webcam)**
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