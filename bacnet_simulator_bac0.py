#!/usr/bin/env python3
"""
BACnet Device Simulator using BAC0
Works better with macOS broadcast handling
"""

import BAC0
import time
import sys

def main():
    print("=" * 60)
    print("Starting BACnet Simulator with BAC0")
    print("=" * 60)
    
    # Create a BACnet/IP device at 192.168.29.27
    # BAC0 handles broadcast reception automatically
    bacnet = BAC0.connect(ip='192.168.29.27/24', port=47808)
    
    print(f"Device running on: {bacnet.localIPAddr}")
    print(f"Device instance: {bacnet.Boid}")
    print("Listening for Who-Is requests...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        # Keep the device running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        bacnet.disconnect()
        print("Simulator stopped")

if __name__ == '__main__':
    main()
