#!/bin/bash

# Setup script for OLED Display FastAPI Server on Raspberry Pi 3B+

echo "🚀 Setting up OLED Display FastAPI Server..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3-pip python3-venv i2c-tools python3-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev

# Enable I2C interface
echo "🔌 Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service file
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/oled-display.service > /dev/null << EOF
[Unit]
Description=OLED Display FastAPI Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/oled-display
Environment=PATH=/home/pi/oled-display/venv/bin
ExecStart=/home/pi/oled-display/venv/bin/python oled.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chmod +x oled.py

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Connect your OLED display with these pin connections:"
echo "   • VCC  → Pin 1  (3.3V)"
echo "   • GND  → Pin 6  (Ground)"
echo "   • SCL  → Pin 5  (GPIO 3 / SCL)"
echo "   • SDA  → Pin 3  (GPIO 2 / SDA)"
echo ""
echo "2. Test I2C connection: i2cdetect -y 1"
echo "3. Run the server: source venv/bin/activate && python oled.py"
echo "4. Access web interface at: http://your-pi-ip:8000"
echo ""
echo "🔄 To enable auto-start on boot:"
echo "   sudo systemctl enable oled-display.service"
echo "   sudo systemctl start oled-display.service"
