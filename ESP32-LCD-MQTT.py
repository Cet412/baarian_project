from machine import Pin, SoftI2C, DAC
from machine_i2c_lcd import I2cLcd
from time import sleep
from umqtt.simple import MQTTClient
import network
import os

# **Setup WiFi**
SSID = "Infinix NOTE 30"
PASSWORD = "10902493"

sta = network.WLAN(network.STA_IF)
sta.active(True)

if not sta.isconnected():
    print("Menyambungkan ke WiFi...")
    sta.connect(SSID, PASSWORD)

# Tunggu sampai koneksi berhasil
while not sta.isconnected():
    sleep(1)

print("WiFi Connected:", sta.ifconfig())

# **Setup MQTT**
MQTT_BROKER = "broker.emqx.io"
CLIENT_ID = "83hiufeg728j20"
TOPIC_TEXT = "baarian/text_message"
TOPIC_AUDIO = "baarian/audio_message"

# **Setup I2C LCD**
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
lcd.clear()
lcd.putstr("MQTT Init...")

# **Setup DAC untuk audio output ke PAM8403**
dac = DAC(Pin(25))  # Gunakan pin DAC (GPIO 25)

# **Variabel penyimpanan audio**
audio_file = None

# **Fungsi untuk memutar audio dari file WAV**
def play_audio(filename):
    try:
        with open(filename, "rb") as f:
            # Lewati header WAV (biasanya 44 byte)
            f.read(44)

            while True:
                data = f.read(1)  # Baca satu byte (8-bit)
                if not data:
                    break

                sample = ord(data)  # Konversi byte ke angka (0-255)
                dac.write(sample)  # Kirim ke DAC
                sleep(0.0005)  # Delay kecil agar suara tidak terlalu cepat

        print("Audio selesai diputar.")
    except Exception as e:
        print("Gagal memutar audio:", e)

# **Callback saat pesan diterima**
def sub_cb(topic, msg):
    global audio_file

    if topic == TOPIC_TEXT.encode():
        print("Pesan teks diterima:", msg.decode())
        lcd.clear()
        lcd.putstr(msg.decode())
        sleep(2)  # Delay agar tidak langsung tertimpa

    elif topic == TOPIC_AUDIO.encode():
        if msg == b"END":
            print("File audio selesai diterima.")
            if audio_file:
                audio_file.close()  # Tutup file setelah selesai
                audio_file = None  # Reset variabel

                # **PUTAR AUDIO SETELAH SELESAI MENERIMA**
                play_audio("output.wav")

        else:
            try:
                # Jika ini adalah data pertama yang diterima, overwrite file lama
                if audio_file is None:
                    audio_file = open("output.wav", "wb")  # BUAT FILE BARU

                audio_file.write(msg)  # Tambahkan data ke file
                print(f"Menerima data audio: {len(msg)} bytes")

            except Exception as e:
                print("Error saat menyimpan audio:", e)

# **Fungsi koneksi MQTT dengan mekanisme retry**
def connect_mqtt():
    global client
    while True:
        try:
            client = MQTTClient(CLIENT_ID, MQTT_BROKER)
            client.set_callback(sub_cb)
            client.connect()
            client.subscribe(TOPIC_TEXT)
            client.subscribe(TOPIC_AUDIO)
            print("MQTT Connected")
            lcd.clear()
            lcd.putstr("MQTT Ready")
            return
        except Exception as e:
            print("Gagal koneksi MQTT, mencoba ulang...", e)
            lcd.clear()
            lcd.putstr("MQTT Failed...")
            sleep(5)

connect_mqtt()  # Jalankan fungsi koneksi MQTT

print("MQTT Siap, menunggu pesan...")

# **Loop utama**
try:
    while True:
        client.wait_msg()  # Tunggu pesan dari broker

except KeyboardInterrupt:
    print("Keyboard interrupt")
    lcd.clear()
    lcd.putstr("Goodbye!")
    sleep(2)
    lcd.backlight_off()
    lcd.display_off()
except Exception as e:
    print("Terjadi error:", e)
    lcd.clear()
    lcd.putstr("Error, restart...")
    sleep(5)
    machine.reset()  # Restart ESP32 jika error