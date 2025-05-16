from machine import Pin, SoftI2C, DAC
from machine_i2c_lcd import I2cLcd
from time import sleep
import network
import os
import sys
from umqtt.simple import MQTTClient

# === Setup SAFE MODE (GPIO 0 BOOT Button) ===
safe_pin = Pin(0, Pin.IN)
sleep(2)

if safe_pin.value() == 0:
    print("SAFE MODE aktif. Tidak menjalankan program utama.")
    sys.exit()

print("Normal mode: menjalankan program Baarian...")

# === Setup WiFi ===
SSID = "Infinix NOTE 30"
PASSWORD = "10902493"

sta = network.WLAN(network.STA_IF)
sta.active(True)

if not sta.isconnected():
    print("Menyambungkan ke WiFi...")
    sta.connect(SSID, PASSWORD)

while not sta.isconnected():
    sleep(1)

print("WiFi Connected:", sta.ifconfig())

# === Setup MQTT ===
MQTT_BROKER = "broker.emqx.io"
CLIENT_ID = "83hiufeg728j20"
TOPIC_TEXT = "baarian/text_message"
TOPIC_AUDIO = "baarian/audio_message"
TOPIC_RESET = "baarian/reset_status"

# === Setup I2C LCD ===
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
lcd.clear()
lcd.putstr("MQTT Init...")

# === Setup DAC Audio (PAM8403) ===
dac = DAC(Pin(25))  # DAC0 = GPIO25

# === Setup Tombol Reset Kata (GPIO32) ===
reset_btn = Pin(32, Pin.IN, Pin.PULL_DOWN)
prev_btn_state = 0

# === Variabel audio file ===
audio_file = None

# === Fungsi Play Audio ===
def play_audio(filename):
    try:
        with open(filename, "rb") as f:
            f.read(44)  # Skip header WAV
            while True:
                data = f.read(1)
                if not data:
                    break
                sample = ord(data)
                dac.write(sample)
                sleep(0.0005)
        print("Audio selesai diputar.")
    except Exception as e:
        print("Gagal memutar audio:", e)

# === Callback MQTT ===
def sub_cb(topic, msg):
    global audio_file

    if topic == TOPIC_TEXT.encode():
        text = msg.decode()
        print("Pesan teks diterima:", text)
        lcd.clear()
        lcd.putstr(text)
        sleep(0.5)

    elif topic == TOPIC_AUDIO.encode():
        if msg == b"END":
            print("File audio selesai diterima.")
            if audio_file:
                audio_file.close()
                audio_file = None
                play_audio("output.wav")
        else:
            try:
                if audio_file is None:
                    audio_file = open("output.wav", "wb")
                audio_file.write(msg)
                print(f"Menerima data audio: {len(msg)} bytes")
            except Exception as e:
                print("Error saat menyimpan audio:", e)

# === Fungsi Koneksi MQTT ===
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

connect_mqtt()
print("MQTT Siap, menunggu pesan...")

# === Main Loop ===
try:
    while True:
        client.check_msg()

        current_btn_state = reset_btn.value()
        if current_btn_state == 1 and prev_btn_state == 0:
            print("Tombol reset ditekan. LCD dikosongkan.")
            lcd.clear()

            # Kirim sinyal reset ke broker
            client.publish(TOPIC_RESET, b"RESET")
            print("Sinyal RESET dikirim ke broker.")

            sleep(0.3)  # debounce

        prev_btn_state = current_btn_state
        sleep(0.1)

except KeyboardInterrupt:
    print("Keyboard Interrupt")
    lcd.clear()
    lcd.putstr("Goodbye...")
    sleep(2)
    lcd.backlight_off()
    lcd.display_off()

except Exception as e:
    print("Terjadi error:", e)
    lcd.clear()
    lcd.putstr("Error, restart...")
    sleep(5)
    import machine
    machine.reset() 