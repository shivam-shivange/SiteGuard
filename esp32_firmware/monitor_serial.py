"""Read serial output from ESP32-CAM on COM7."""
import sys
import serial
import time

port = sys.argv[1] if len(sys.argv) > 1 else "COM7"
baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

print(f"Connecting to {port} at {baud} baud (Ctrl+C to exit)...")
try:
    with serial.Serial(port, baud, timeout=1) as ser:
        time.sleep(0.5)
        while True:
            line = ser.readline().decode("utf-8", errors="replace")
            if line:
                print(line, end="")
except KeyboardInterrupt:
    print("\nExiting monitor.")
except Exception as e:
    print(f"\nError: {e}")
