"""
FastAPI server for controlling 1.3" GME12864-80 OLED display on Raspberry Pi 3B+
Displays aesthetic clock and other information
"""

import asyncio
import time
from datetime import datetime
from typing import Optional
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
import uvicorn

# Display libraries
try:
    import board
    import digitalio
    import busio
    import adafruit_ssd1306
    from PIL import Image, ImageDraw, ImageFont
    DISPLAY_AVAILABLE = True
except ImportError:
    print("Display libraries not available. Running in simulation mode.")
    DISPLAY_AVAILABLE = False

# Global variables
display = None
current_mode = "clock"
display_task = None
custom_message = ""

# Display configuration
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64

class OLEDController:
    def __init__(self):
        self.display = None
        self.font = None
        self.small_font = None
        self.initialize_display()
    
    def initialize_display(self):
        """Initialize the OLED display via SPI"""
        if not DISPLAY_AVAILABLE:
            print("Running in simulation mode - no actual display")
            return
        
        try:
            # Initialize SPI
            spi = busio.SPI(board.SCK, MOSI=board.MOSI)
            
            # Reset pin (optional, can be None)
            reset_pin = None
            
            # DC pin - you might need to connect this to another GPIO
            # For now, trying without DC pin (some displays don't need it)
            dc_pin = None
            cs_pin = None  # Chip select (optional)
            
            try:
                # Try SPI initialization
                self.display = adafruit_ssd1306.SSD1306_SPI(
                    DISPLAY_WIDTH, DISPLAY_HEIGHT, spi, dc_pin, reset_pin, cs_pin
                )
                print("SPI OLED display initialized successfully!")
            except Exception as spi_error:
                print(f"SPI initialization failed: {spi_error}")
                
                # Fallback: Try I2C with different addresses
                print("Trying I2C as fallback...")
                i2c = board.I2C()
                
                # Try common I2C addresses
                for addr in [0x3C, 0x3D, 0x78, 0x7A]:
                    try:
                        print(f"Trying I2C address: 0x{addr:02X}")
                        self.display = adafruit_ssd1306.SSD1306_I2C(
                            DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c, addr=addr
                        )
                        print(f"I2C OLED display initialized at address 0x{addr:02X}!")
                        break
                    except Exception as i2c_error:
                        print(f"I2C address 0x{addr:02X} failed: {i2c_error}")
                        continue
                
                if not self.display:
                    raise Exception("Both SPI and I2C initialization failed")
            
            # Clear display
            self.display.fill(0)
            self.display.show()
            
            # Try to load fonts
            try:
                # Try to load a nice font
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                self.small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            except:
                # Fallback to default font
                self.font = ImageFont.load_default()
                self.small_font = ImageFont.load_default()
            
            print("OLED display ready!")
            
        except Exception as e:
            print(f"Error initializing display: {e}")
            self.display = None
    
    def create_image(self):
        """Create a new image for drawing"""
        return Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT))
    
    def show_clock(self):
        """Display an aesthetic clock"""
        if not self.display:
            return
        
        image = self.create_image()
        draw = ImageDraw.Draw(image)
        
        now = datetime.now()
        
        # Main time
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        day_str = now.strftime("%A")
        
        # Draw time (centered)
        time_bbox = draw.textbbox((0, 0), time_str, font=self.font)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = (DISPLAY_WIDTH - time_width) // 2
        draw.text((time_x, 15), time_str, font=self.font, fill=255)
        
        # Draw date (centered)
        date_bbox = draw.textbbox((0, 0), date_str, font=self.small_font)
        date_width = date_bbox[2] - date_bbox[0]
        date_x = (DISPLAY_WIDTH - date_width) // 2
        draw.text((date_x, 35), date_str, font=self.small_font, fill=255)
        
        # Draw day (centered)
        day_bbox = draw.textbbox((0, 0), day_str, font=self.small_font)
        day_width = day_bbox[2] - day_bbox[0]
        day_x = (DISPLAY_WIDTH - day_width) // 2
        draw.text((day_x, 50), day_str, font=self.small_font, fill=255)
        
        # Draw decorative border
        draw.rectangle((0, 0, DISPLAY_WIDTH-1, DISPLAY_HEIGHT-1), outline=255, width=1)
        
        # Draw corner decorations
        for i in range(5):
            draw.point((i, 0), fill=255)
            draw.point((DISPLAY_WIDTH-1-i, 0), fill=255)
            draw.point((i, DISPLAY_HEIGHT-1), fill=255)
            draw.point((DISPLAY_WIDTH-1-i, DISPLAY_HEIGHT-1), fill=255)
        
        self.display.image(image)
        self.display.show()
    
    def show_message(self, message: str):
        """Display a custom message"""
        if not self.display:
            return
        
        image = self.create_image()
        draw = ImageDraw.Draw(image)
        
        # Split message into lines that fit the display
        words = message.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=self.small_font)
            if bbox[2] - bbox[0] <= DISPLAY_WIDTH - 10:  # Leave 5px margin on each side
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Center the text vertically
        line_height = 12
        total_height = len(lines) * line_height
        start_y = (DISPLAY_HEIGHT - total_height) // 2
        
        # Draw each line centered horizontally
        for i, line in enumerate(lines[:5]):  # Max 5 lines
            bbox = draw.textbbox((0, 0), line, font=self.small_font)
            text_width = bbox[2] - bbox[0]
            x = (DISPLAY_WIDTH - text_width) // 2
            y = start_y + i * line_height
            draw.text((x, y), line, font=self.small_font, fill=255)
        
        self.display.image(image)
        self.display.show()
    
    def show_system_info(self):
        """Display system information"""
        if not self.display:
            return
        
        image = self.create_image()
        draw = ImageDraw.Draw(image)
        
        try:
            # Get system info
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Current time
            now = datetime.now().strftime("%H:%M")
            
            # Display info
            draw.text((2, 2), f"Time: {now}", font=self.small_font, fill=255)
            draw.text((2, 14), f"CPU: {cpu_percent:.1f}%", font=self.small_font, fill=255)
            draw.text((2, 26), f"RAM: {memory.percent:.1f}%", font=self.small_font, fill=255)
            draw.text((2, 38), f"Disk: {disk.percent:.1f}%", font=self.small_font, fill=255)
            draw.text((2, 50), "Raspberry Pi", font=self.small_font, fill=255)
            
        except ImportError:
            draw.text((2, 20), "System info", font=self.small_font, fill=255)
            draw.text((2, 32), "unavailable", font=self.small_font, fill=255)
        
        self.display.image(image)
        self.display.show()
    
    def clear_display(self):
        """Clear the display"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.display.show()

# Initialize the OLED controller
oled = OLEDController()

async def display_loop():
    """Main display loop"""
    global current_mode, custom_message
    
    while True:
        try:
            if current_mode == "clock":
                oled.show_clock()
            elif current_mode == "message":
                oled.show_message(custom_message)
            elif current_mode == "system":
                oled.show_system_info()
            elif current_mode == "off":
                oled.clear_display()
            
            await asyncio.sleep(1)  # Update every second
            
        except Exception as e:
            print(f"Error in display loop: {e}")
            await asyncio.sleep(1)

# Updated lifespan event handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global display_task
    display_task = asyncio.create_task(display_loop())
    yield
    # Shutdown
    if display_task:
        display_task.cancel()
    oled.clear_display()

app = FastAPI(
    title="Raspberry Pi OLED Display Controller", 
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Web interface for controlling the display"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OLED Display Controller</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
            .button { padding: 10px 20px; margin: 5px; font-size: 16px; cursor: pointer; }
            .current-mode { background-color: #4CAF50; color: white; }
            textarea { width: 100%; height: 100px; }
            .status { margin: 20px 0; padding: 10px; background-color: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>🖥️ OLED Display Controller</h1>
        <div class="status">
            <p><strong>Current Mode:</strong> <span id="currentMode">clock</span></p>
            <p><strong>Display:</strong> """ + ("Connected" if oled.display else "Not Connected") + """</p>
        </div>
        
        <h2>Display Modes</h2>
        <button class="button" onclick="setMode('clock')">🕐 Clock</button>
        <button class="button" onclick="setMode('system')">📊 System Info</button>
        <button class="button" onclick="setMode('off')">⚫ Off</button>
        
        <h2>Custom Message</h2>
        <textarea id="messageText" placeholder="Enter your custom message here..."></textarea>
        <br>
        <button class="button" onclick="sendMessage()">📝 Show Message</button>
        
        <script>
            function setMode(mode) {
                fetch('/mode/' + mode, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('currentMode').textContent = mode;
                        alert(data.message);
                    });
            }
            
            function sendMessage() {
                const message = document.getElementById('messageText').value;
                if (!message.trim()) {
                    alert('Please enter a message');
                    return;
                }
                
                fetch('/message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('currentMode').textContent = 'message';
                    alert(data.message);
                });
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/status")
async def get_status():
    """Get current display status"""
    return {
        "mode": current_mode,
        "message": custom_message if current_mode == "message" else "",
        "display_available": oled.display is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/mode/{mode}")
async def set_mode(mode: str):
    """Set display mode"""
    global current_mode
    
    valid_modes = ["clock", "system", "off"]
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Valid modes: {valid_modes}")
    
    current_mode = mode
    return {"message": f"Display mode set to {mode}", "mode": mode}

@app.post("/message")
async def set_message(data: dict):
    """Set custom message to display"""
    global current_mode, custom_message
    
    if "message" not in data:
        raise HTTPException(status_code=400, detail="Message field required")
    
    custom_message = data["message"]
    current_mode = "message"
    
    return {"message": "Custom message set", "text": custom_message}

@app.post("/clear")
async def clear():
    """Clear the display"""
    global current_mode
    current_mode = "off"
    return {"message": "Display cleared"}

@app.get("/test")
async def test_display():
    """Test the display with a simple message"""
    if oled.display:
        oled.show_message("FastAPI Server\nRunning!\n\nHello from\nRaspberry Pi!")
        return {"message": "Test message sent to display"}
    else:
        return {"message": "Display not available (simulation mode)"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)