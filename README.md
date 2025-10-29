# BACnet Device Simulator

A flexible and easy-to-use BACnet device simulator for testing BACnet applications, building automation systems, and development purposes.

## Features

- **Multiple Object Types**: Support for Analog (Value/Input/Output), Binary (Value/Input/Output), and Multi-state (Value/Input/Output) objects
- **Value Simulation**: Automatic value changes with configurable patterns:
  - Random values within a range
  - Sine wave patterns
  - Incrementing/cycling values
  - Toggle patterns for binary values
- **Easy Configuration**: YAML-based configuration for quick setup
- **Modern Stack**: Built on BACpypes3, the latest Python BACnet implementation
- **Async Architecture**: Efficient asynchronous design for handling multiple objects
- **Test Client Included**: Ready-to-use test client for verification

## Requirements

- Python 3.7 or higher
- BACpypes3 library
- PyYAML

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment (recommended)**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Start the Simulator

Run the simulator with the default configuration:

```bash
python3 bacnet_simulator.py
```

Or specify a custom configuration file:

```bash
python3 bacnet_simulator.py -c my_config.yaml
```

The simulator will start and display information about the device and objects created:

```
2025-10-29 10:00:00 - INFO - BACnet device created: BACnet Test Device
2025-10-29 10:00:00 - INFO - Device Instance: 1001
2025-10-29 10:00:00 - INFO - Listening on: 0.0.0.0:47808
2025-10-29 10:00:00 - INFO - Created analog-value object: Temperature (instance: 1)
...
```

### 2. Test the Simulator

In another terminal, run the test client:

```bash
python3 test_client.py
```

The test client will:
- Discover BACnet devices on the network
- Read various properties from the simulator
- Perform write operations
- Monitor simulated value changes

## Configuration

Edit `config.yaml` to customize your simulated device. The configuration file includes:

### Device Settings

```yaml
device:
  name: "BACnet Test Device"
  instance: 1001
  description: "Virtual BACnet Device for Testing"
  vendor_id: 999
  model: "Virtual BACnet Simulator v1.0"
```

### Network Settings

```yaml
network:
  address: "0.0.0.0"  # Listen on all interfaces
  port: 47808          # Standard BACnet port
```

### Objects Configuration

Each object can be configured with:

- **type**: Object type (analog-value, analog-input, analog-output, binary-value, etc.)
- **instance**: Unique instance number for the object type
- **name**: Object name
- **initial_value**: Starting value
- **units**: Engineering units (for analog objects)
- **description**: Object description
- **simulate**: Enable/disable automatic value changes
- **simulation**: Simulation parameters

#### Example: Temperature Sensor with Sine Wave

```yaml
- type: analog-value
  instance: 1
  name: "Temperature"
  initial_value: 22.5
  units: "degreesCelsius"
  description: "Simulated temperature sensor"
  simulate: true
  simulation:
    type: sine
    interval: 2.0
    amplitude: 5.0
    offset: 22.0
    frequency: 0.05
```

#### Example: Random Humidity Sensor

```yaml
- type: analog-value
  instance: 2
  name: "Humidity"
  initial_value: 45.0
  units: "percentRelativeHumidity"
  simulate: true
  simulation:
    type: random
    interval: 3.0
    min: 30.0
    max: 70.0
```

#### Example: Binary Toggle

```yaml
- type: binary-value
  instance: 1
  name: "Fan_Status"
  initial_value: 0
  simulate: true
  simulation:
    type: toggle
    interval: 10.0
```

### Simulation Types

#### For Analog Objects:

- **random**: Random values between min and max
  ```yaml
  simulation:
    type: random
    interval: 5.0
    min: 0.0
    max: 100.0
  ```

- **sine**: Sine wave pattern
  ```yaml
  simulation:
    type: sine
    interval: 2.0
    amplitude: 10.0
    offset: 50.0
    frequency: 0.1
  ```

- **increment**: Incrementing value with wraparound
  ```yaml
  simulation:
    type: increment
    interval: 3.0
    step: 1.0
    min: 0.0
    max: 100.0
  ```

#### For Binary Objects:

- **toggle**: Alternates between 0 and 1
  ```yaml
  simulation:
    type: toggle
    interval: 10.0
  ```

- **random**: Random 0 or 1
  ```yaml
  simulation:
    type: random
    interval: 5.0
  ```

#### For Multi-state Objects:

- **cycle**: Cycles through states sequentially
  ```yaml
  simulation:
    type: cycle
    interval: 10.0
  ```

- **random**: Random state selection
  ```yaml
  simulation:
    type: random
    interval: 5.0
  ```

## Usage Examples

### Basic Testing

Start simulator and test client on the same machine:

```bash
# Terminal 1: Start simulator
python3 bacnet_simulator.py

# Terminal 2: Run test client
python3 test_client.py
```

### Custom Configuration

Create a custom configuration for your specific testing needs:

```bash
# Copy the default config
cp config.yaml my_device.yaml

# Edit my_device.yaml with your settings

# Run with custom config
python3 bacnet_simulator.py -c my_device.yaml
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
python3 bacnet_simulator.py --debug
```

### Testing with BACnet Tools

You can use standard BACnet tools to interact with the simulator:

1. **YABE (Yet Another BACnet Explorer)**
   - Download from: https://sourceforge.net/projects/yetanotherbacnetexplorer/
   - Add device by IP address
   - Browse and interact with objects

2. **BACnet4J**
   - Use for Java-based testing

3. **BACpypes Console**
   - Command-line BACnet operations

### Reading Values Programmatically

```python
import asyncio
from test_client import BACnetTestClient

async def read_temperature():
    client = BACnetTestClient()
    await client.setup()
    
    # Discover devices
    devices = await client.who_is(1001, 1001)
    if devices:
        device_address = str(devices[0].pduSource)
        
        # Read temperature
        temp = await client.read_property(
            device_address,
            ("analogValue", 1),
            "presentValue"
        )
        print(f"Temperature: {temp}")

asyncio.run(read_temperature())
```

### Writing Values

```python
from bacpypes3.primitivedata import Real

async def set_temperature():
    client = BACnetTestClient()
    await client.setup()
    
    devices = await client.who_is(1001, 1001)
    if devices:
        device_address = str(devices[0].pduSource)
        
        # Write setpoint
        await client.write_property(
            device_address,
            ("analogOutput", 1),
            Real(23.5)
        )

asyncio.run(set_temperature())
```

## Network Configuration

### Same Machine Testing

For testing on the same machine, use different ports:

**Simulator** (config.yaml):
```yaml
network:
  address: "0.0.0.0"
  port: 47808
```

**Test Client**:
```bash
python3 test_client.py -a 0.0.0.0:47809
```

### Different Machines

**Simulator** (on machine A):
```yaml
network:
  address: "0.0.0.0"  # Listen on all interfaces
  port: 47808
```

**Test Client** (on machine B):
```bash
# Replace 192.168.1.100 with simulator's IP
python3 test_client.py -a 192.168.1.100:47808
```

### Firewall Configuration

Ensure UDP port 47808 (or your configured port) is open:

**Linux**:
```bash
sudo ufw allow 47808/udp
```

**macOS**:
```bash
# Add firewall rule in System Preferences > Security & Privacy > Firewall
```

**Windows**:
```powershell
netsh advfirewall firewall add rule name="BACnet" dir=in action=allow protocol=UDP localport=47808
```

## Troubleshooting

### Simulator won't start

1. **Check if port is already in use**:
   ```bash
   # Linux/macOS
   sudo lsof -i :47808
   
   # Windows
   netstat -ano | findstr :47808
   ```

2. **Try a different port** in config.yaml

3. **Check Python version**:
   ```bash
   python3 --version  # Should be 3.7 or higher
   ```

### Test client can't find device

1. **Verify simulator is running**
2. **Check network connectivity**:
   ```bash
   ping <simulator-ip>
   ```
3. **Verify firewall rules**
4. **Try specifying exact device instance**:
   ```bash
   python3 test_client.py -d 1001
   ```

### No simulated value changes

1. **Check that `simulate: true` is set** in config.yaml
2. **Verify simulation interval** isn't too long
3. **Check logs** for simulation errors

### Import errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `bacnet_simulator.log`

Adjust logging level in the code or use `--debug` flag for verbose output.

## Advanced Topics

### Creating Custom Object Types

You can extend the simulator to support additional BACnet object types by:

1. Importing the object class from BACpypes3
2. Adding a creation method in the `BACnetSimulator` class
3. Adding the object type to the configuration handler

### Integration with Other Systems

The simulator can be integrated with:
- Building Management Systems (BMS)
- SCADA systems
- IoT platforms
- Test automation frameworks

### Performance Tuning

For simulating many objects:
- Increase simulation intervals to reduce CPU usage
- Disable simulation for static objects
- Use appropriate logging levels

## Project Structure

```
BACnet-Simulator/
├── bacnet_simulator.py    # Main simulator application
├── config.yaml            # Configuration file
├── test_client.py         # Test client for verification
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── bacnet_simulator.log  # Log file (generated)
```

## Contributing

Feel free to extend this simulator for your specific needs. Some ideas:
- Add support for more BACnet object types
- Implement trending and logging
- Add a web interface for monitoring
- Create preset configurations for common scenarios

## License

This is a testing tool provided as-is for development and testing purposes.

## References

- **BACnet Protocol**: http://www.bacnet.org/
- **BACpypes3 Documentation**: https://bacpypes3.readthedocs.io/
- **ASHRAE Standard 135**: BACnet protocol specification

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review BACpypes3 documentation
3. Check configuration file syntax

## Version History

- **v1.0** (2025-10-29): Initial release
  - Support for analog, binary, and multi-state objects
  - YAML configuration
  - Value simulation with multiple patterns
  - Test client included

