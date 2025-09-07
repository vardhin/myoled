# OLED Display FastAPI Server

A FastAPI server for controlling a 1.3" GME12864-80 OLED display on Raspberry Pi 3B+.

## 🔌 Pin Connections

Connect your GME12864-80 OLED display to the Raspberry Pi 3B+ as follows:

| OLED Pin | Raspberry Pi Pin | GPIO | Function |
|----------|------------------|------|----------|
| VCC      | Pin 1            | -    | 3.3V Power |
| GND      | Pin 6            | -    | Ground |
| SCL      | Pin 5            | GPIO 3 | I2C Clock |
| SDA      | Pin 3            | GPIO 2 | I2C Data |

## 🚀 Quick Setup

1. Make the setup script executable and run it:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. Test I2C connection:
   ```bash
   i2cdetect -y 1
   ```
   You should see the display at address 0x3C.

3. Start the server:
   ```bash
   source venv/bin/activate
   python oled.py
   ```

4. Access the web interface at `http://your-pi-ip:8000`

## 📱 Features

### Display Modes
- **🕐 Clock**: Aesthetic digital clock with date and day
- **📊 System Info**: CPU, RAM, disk usage, and time
- **📝 Custom Message**: Display any text message
- **⚫ Off**: Turn off the display

### API Endpoints
- `GET /`: Web interface for controlling the display
- `GET /status`: Get current display status
- `POST /mode/{mode}`: Set display mode (clock, system, off)
- `POST /message`: Set custom message
- `POST /clear`: Clear the display
- `GET /test`: Test the display

### Example API Usage
```bash
# Set clock mode
curl -X POST "http://your-pi-ip:8000/mode/clock"

# Show custom message
curl -X POST "http://your-pi-ip:8000/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello World!"}'

# Get status
curl "http://your-pi-ip:8000/status"
```

## 🔧 Manual Installation

If you prefer to install manually:

1. Enable I2C:
   ```bash
   sudo raspi-config nonint do_i2c 0
   ```

2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv i2c-tools python3-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev
   ```

3. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 🔄 Auto-start on Boot

To run the server automatically on boot:

```bash
# Update the service file path in setup.sh first
sudo systemctl enable oled-display.service
sudo systemctl start oled-display.service

# Check status
sudo systemctl status oled-display.service
```

## 🛠️ Troubleshooting

### Display not detected
1. Check wiring connections
2. Verify I2C is enabled: `sudo raspi-config`
3. Scan for I2C devices: `i2cdetect -y 1`
4. Try different I2C addresses (0x3C or 0x3D)

### Permission errors
```bash
sudo usermod -a -G i2c $USER
# Logout and login again
```

### Service not starting
```bash
sudo journalctl -u oled-display.service -f
```

## 📦 Dependencies

- FastAPI: Web framework
- Uvicorn: ASGI server
- Adafruit CircuitPython: Hardware libraries
- Pillow: Image processing
- psutil: System information

## 🎨 Customization

You can modify the display functions in `oled.py`:
- Add new display modes
- Customize clock appearance
- Add animations
- Create custom graphics

The display resolution is 128x64 pixels, perfect for text, simple graphics, and system information.
