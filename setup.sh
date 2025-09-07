#!/bin/bash
# filepath: /home/vardhin/Documents/git/myoled/setup_spi.sh
echo "🚀 Setting up OLED Display with SPI..."

# Enable SPI interface
echo "📡 Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

# Also enable I2C as fallback
echo "📡 Enabling I2C interface as fallback..."
sudo raspi-config nonint do_i2c 0

# Update system
echo "📦 Updating system..."
sudo apt update

# Install required system packages
echo "📦 Installing system packages..."
sudo apt install -y python3-pip python3-venv python3-dev i2c-tools

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install packages
echo "📦 Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "🔌 Wire your OLED display:"
echo "   VCC -> Pin 1  (3.3V)"
echo "   GND -> Pin 6  (Ground)"
echo "   SCK -> Pin 23 (GPIO 11 - SPI Clock)"
echo "   SDA -> Pin 19 (GPIO 10 - SPI MOSI)"
echo ""
echo "🔄 Please reboot your Pi to enable SPI:"
echo "   sudo reboot"
echo ""
echo "🧪 After reboot, test with:"
echo "   source venv/bin/activate && python oled.py"