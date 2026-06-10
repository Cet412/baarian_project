# Symbara Project: IoT & Edge AI Sign Language Interpreter
Symbara is an advanced, interactive Edge AI and IoT system that enables real-time communication by translating visual hand gestures or objects into both text messages and audio feeds. The project integrates a local YOLOv8 detection pipeline, an asynchronous MQTT messaging architecture, and a MicroPython-enabled hardware interface.

## 📂 Project Directory Structure

```text
symbara_project/
├── .env.example              # Configuration template for credentials
├── .gitignore                # Git exclusion rules for security
├── AI Model/                 # Edge AI weights
│   └── symbara_Model_Nano.pt
├── ESP32 required program/   # MicroPython receiver scripts
│   ├── ESP32-LCD-MQTT.py     # Main hardware subscriber script
│   ├── machine_i2c_lcd.py    # I2C LCD driver
│   └── lcd_api.py            # Hardware LCD API
├── ESP32cam/                 # Camera firmware
│   └── ESP32cam.ino          # Arduino C++ stream sketch
├── main.py                   # Unified processing and detection client
└── requirements.txt          # Absolute Python dependencies
```

## Installation & Setup
### PC/Server Deployment
A. Prerequisites
Ensure you have [**Python 3.8+**](https://www.python.org/downloads/) and [**FFmpeg**](https://www.ffmpeg.org/) installed and added to your system's PATH for handling audio conversions

B. Clone & Environment Configuration
```bash
# Clone the repository and navigate into it
git clone https://github.com/Cet412/symbara_project.git
cd symbara_project

# Set up a python virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows:
.\\.venv\\Scripts\\activate
# Linux/macOS:
source .venv/bin/activate
```

C. Install Dependencies
```bash
pip install -r requirements.txt
```

D. Local Variables Configuration
Create a `.env` file in the project root by copying the .env.example file
```bash
cp .env.example .env
```
Fill in the `.env` file with your specific target configuration
```env
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
MQTT_TOPIC_TEXT=symbara/text_message
MQTT_TOPIC_AUDIO=symbara/audio_message
MQTT_TOPIC_RESET=symbara/reset_status
ESP32_CAM_URL=http://<esp32-cam-ip>/capture
USE_WEBCAM=True
```

### MicroPython ESP32 Deployment
A. Flashing the Scripts
   1. Open Thonny IDE, go to Tools → Options → Interpreter, and set it to MicroPython (ESP32).
   2. Upload the following files to the root directory of your ESP32:
   `ESP32-LCD-MQTT.py`
   `machine_i2c_lcd.py`
   `lcd_api.py`

B. Install MQTT Dependencies on ESP32
Open the Thonny Shell while connected to the ESP32 and execute the following:
```python
import upip
upip.install('umqtt.simple')
```

## Usage Guide
### Starting the System
Once the ESP32 is powered and connected to the MQTT broker, execute the detection engine on the server:
```sh
python main.py
```

### Manual Interface & Controls
The detection engine continuously runs in real-time. Use the following keystrokes in the visual detection window:
- `r` : Manual Reset — Clears the current word and sentence buffers.
- `q` : Terminate — Closes the application safely.

### Background Automation
- **Auto-Space**: If no matching detection changes for 3.5 seconds, the engine completes the current word and adds a trailing space.
- **Auto-Sentence**: After 5.0 seconds of idle detection time, the accumulated words are joined into a sentence, published via text MQTT, translated to speech, and emitted to the hardware speaker asynchronously.

## Troubleshooting

1. Blocking I/O or Performance Lag
- Solution: Ensure FFmpeg is correctly mapped to your environmental path. The audio processing is run asynchronously via standard threads to prevent interface freezing.
2. MQTT Subscription Failures
- Solution: Test the reachability of the broker using standard network tools:
```bash
 ping broker.emqx.io
```
3. ESP32 Disconnection
- Solution: Confirm stable Wi-Fi connectivity and valid credential provisioning inside the `ESP32-LCD-MQTT.py` setup module.