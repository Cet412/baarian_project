# Baarian Project 

Baarian is an interactive, ESP32-based IoT system that enables two-way communication through text and audio using the MQTT protocol. This project integrates hardware components with an AI model and a web interface, consisting of two main modules:

1. **ESP32 with LCD and DAC:** Displays text messages and plays audio received via MQTT.
2. **ESP32-CAM:** Transmits image feeds via HTTP, ready for integration with facial or object recognition systems.

---

## 📂 Project Structure
```text
baarian_project/
├── ESP32-LCD-MQTT.py         # Main script for ESP32 with LCD and DAC
├── machine_i2c_lcd.py        # Library for I2C LCD control
├── lcd_api.py                # Additional API for LCD operations
├── ESP32cam/                 # Directory containing ESP32-CAM code
│   └── ESP32cam.ino          # Main Arduino sketch for ESP32-CAM
├── models/                   # Directory for AI models
│   ├── Baarian_Model.pt
│   └── Baarian_Model_Light.pt
├── Streamlit/                # Web application for user interaction
│   └── app.py
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## Requirements

### Hardware

* ESP32 Dev Board with DAC and LCD support (e.g., ESP32-WROOM-32)
* ESP32-CAM (e.g., AI-Thinker module)
* I2C 16x2 LCD Display
* PAM8403 Audio Amplifier
* Speaker
* Jumper wires & Breadboard

### Software

* MicroPython firmware for ESP32
* Arduino IDE or PlatformIO (for ESP32-CAM)
* Python 3.8+
* Thonny IDE (optional, for flashing MicroPython scripts)

---

## Installation & Setup

### 1. Setting up the ESP32 (LCD & DAC)

1. Flash MicroPython firmware to your ESP32.
2. Use Thonny IDE to upload the following files to the ESP32:

   * `ESP32-LCD-MQTT.py`
   * `machine_i2c_lcd.py`
   * `lcd_api.py`
3. Edit `ESP32-LCD-MQTT.py` to configure your WiFi SSID and password.
4. Run `ESP32-LCD-MQTT.py` as the main script.

### 2. Setting up the ESP32-CAM

1. Open `ESP32cam.ino` in Arduino IDE..
2. Select the "AI Thinker ESP32-CAM" board and the appropriate COM port.
3. Update your WiFi SSID and password within the sketch.
4. Upload the code to the ESP32-CAM.
5. Once connected to WiFi, the ESP32-CAM will display its IP address in the Serial Monitor.

### 3. Setting up the Streamlit Web App

1. Ensure Python 3.8+ is installed on your machine.
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit application:

   ```bash
   streamlit run Streamlit/app.py
   ```

---

## Usage Guide

1. Power on both the ESP32 and ESP32-CAM modules.
2. The ESP32 will connect to WiFi and listen for incoming messages from the MQTT broker.
3. The ESP32-CAM will start streaming images over HTTP, accessible via the IP address shown in the Serial Monitor.
4. Use the Streamlit web app to send text or audio messages to the ESP32 via MQTT.
5. The ESP32 will display the received text on the LCD and output the audio through the connected speaker.

---

## Camera Access

Once the ESP32-CAM is connected to WiFi, you can access the image capture feed via your web browser by navigating to:

```
http://<esp32-cam-ip-address>/capture
```

(Replace `<esp32-cam-ip-address>` with the IP address printed in your Serial Monitor)

---

## Contact

For any inquiries, suggestions, or collaboration opportunities, feel free to reach out via email at [cettaanantamaulana@gmail.com](cettaanantamaulana@gmail.com).

---
