# Quick Start Guide

Get your BACnet simulator up and running in 3 easy steps!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Start the Simulator

**Option A: Using the start script (easiest)**
```bash
./start.sh
```

**Option B: Direct Python command**
```bash
python3 bacnet_simulator.py
```

You should see output like:
```
2025-10-29 10:00:00 - INFO - BACnet device created: BACnet Test Device
2025-10-29 10:00:00 - INFO - Device Instance: 1001
2025-10-29 10:00:00 - INFO - Listening on: 0.0.0.0:47808
2025-10-29 10:00:00 - INFO - Created analog-value object: Temperature (instance: 1)
...
============================================================
BACnet Device Simulator Started
============================================================
Press Ctrl+C to stop the simulator
```

## Step 3: Test the Simulator

Open a **new terminal** and run:

```bash
python3 test_client.py
```

The test client will automatically:
- Discover your BACnet device
- Read all configured objects
- Test write operations
- Monitor simulated value changes

## Expected Output

The test client will show something like:

```
============================================================
Starting BACnet Test Suite
============================================================

[Test 1] Device Discovery (Who-Is)
------------------------------------------------------------
2025-10-29 10:01:00 - INFO - Sending Who-Is request...
2025-10-29 10:01:00 - INFO - Found 1 device(s):
2025-10-29 10:01:00 - INFO -   - Device 1001 at 192.168.1.100

[Test 2] Reading Device Properties
------------------------------------------------------------
2025-10-29 10:01:01 - INFO - Reading objectName from ('device', 1001)
2025-10-29 10:01:01 - INFO -   Value: BACnet Test Device
...
```

## What's Included

The default configuration creates:

### Analog Objects
- **Temperature** (Analog Value 1) - Simulated with sine wave pattern
- **Humidity** (Analog Value 2) - Random values 30-70%
- **Pressure** (Analog Input 1) - Random values 98-105 kPa
- **Temperature Setpoint** (Analog Output 1) - Writable setpoint
- **Power Consumption** (Analog Value 3) - Random 1000-3000W
- **CO2 Level** (Analog Value 4) - Incrementing 400-1000 ppm

### Binary Objects
- **Fan Status** (Binary Value 1) - Toggles every 10 seconds
- **Door Sensor** (Binary Input 1) - Random open/closed
- **Alarm Output** (Binary Output 1) - Writable alarm control

### Multi-state Objects
- **Operating Mode** (Multi-state Value 1) - Cycles through: Off, Cool, Heat, Auto
- **System Status** (Multi-state Input 1) - Random: Normal, Warning, Alarm

## Next Steps

### Customize Your Device

Edit `config.yaml` to:
- Change device name and instance number
- Add more objects
- Adjust simulation parameters
- Modify value ranges

### Use with BACnet Tools

The simulator works with standard BACnet tools:
- **YABE** (Yet Another BACnet Explorer)
- **BACnet4J**
- Any BACnet client application

### Test on Network

By default, the simulator binds to all interfaces (0.0.0.0). To test from another machine:

1. Find your IP address:
   ```bash
   # Linux/macOS
   ifconfig | grep inet
   
   # Windows
   ipconfig
   ```

2. On the other machine, modify test_client.py or use a BACnet tool to connect to your IP

### Read the Full Documentation

See `README.md` for:
- Detailed configuration options
- All simulation types
- Network setup for different scenarios
- Troubleshooting tips
- Advanced usage examples

## Troubleshooting

### Port Already in Use
Edit `config.yaml` and change the port:
```yaml
network:
  port: 47809  # or any other available port
```

### Can't Find Device
- Make sure the simulator is running in the first terminal
- Check firewall settings
- Verify both are on the same network

### Dependencies Not Installing
```bash
# Try upgrading pip first
pip install --upgrade pip

# Then install again
pip install -r requirements.txt
```

## Stop the Simulator

Press `Ctrl+C` in the terminal running the simulator.

---

**That's it! You now have a fully functional BACnet device simulator for testing.**

For more details, see the full `README.md` file.

