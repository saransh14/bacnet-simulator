#!/bin/bash
# Convenience script to start the BACnet simulator

echo "Starting BACnet Device Simulator..."
echo "Press Ctrl+C to stop"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if dependencies are installed
python3 -c "import bacpypes3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: BACpypes3 not found. Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start the simulator
python3 bacnet_simulator.py "$@"

