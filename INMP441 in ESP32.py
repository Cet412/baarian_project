import network
import socket
from machine import I2S, Pin

# =============== Konfigurasi WiFi ===============
SSID = "Infinix NOTE 30"
PASSWORD = "10902493"
PC_IP = "192.168.252.195"  # Ganti dengan IP laptop
PORT = 8888

# =============== Setup I2S ===============
SAMPLE_RATE = 16000
I2S_WS = 26
I2S_SD = 33
I2S_SCK = 27
BUFFER_LENGTH = 1024

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected(): 
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            pass
    print("Connected to WiFi:", wlan.ifconfig())

def connect_pc():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((PC_IP, PORT))
        print("Connected to PC")
        return s
    except Exception as e:
        print("PC connection failed:", e)
        return None

def setup_i2s():
    i2s = I2S(
        0,
        sck=Pin(I2S_SCK),
        ws=Pin(I2S_WS),
        sd=Pin(I2S_SD),
        mode=I2S.RX,
        bits=16,
        format=I2S.MONO,
        rate=SAMPLE_RATE,
        ibuf=40000
    )
    return i2s

def main():
    connect_wifi()
    sock = connect_pc()
    i2s = setup_i2s()
    
    audio_buffer = bytearray(BUFFER_LENGTH)
    
    while True:
        try:
            # Baca dari I2S
            num_read = i2s.readinto(audio_buffer)
            
            # Kirim via socket
            if num_read > 0 and sock:
                sock.send(audio_buffer)
                
        except Exception as e:
            print("Error:", e)
            sock = connect_pc()  # Reconnect if error

if __name__ == "__main__":
    main()