#!/usr/bin/env python3
"""
Direct BACnet Connection Test

Tests the simulator by directly reading properties without using Who-Is discovery.
This bypasses broadcast issues and tests if the simulator is actually responding.
"""

import asyncio
import logging
from bacpypes3.pdu import Address
from bacpypes3.app import Application
from bacpypes3.local.device import DeviceObject
from bacpypes3.local.networkport import NetworkPortObject
from bacpypes3.primitivedata import ObjectIdentifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def direct_test():
    """Test by directly connecting to the simulator"""
    
    logger.info("="*60)
    logger.info("Direct BACnet Connection Test")
    logger.info("="*60)
    
    # Create test client
    device_object = DeviceObject(
        objectIdentifier=("device", 888888),
        objectName="DirectTestClient",
        vendorIdentifier=999,
    )
    
    network_port_object = NetworkPortObject(
        "127.0.0.1/32:47809",
        objectIdentifier=("network-port", 1),
        objectName="NetworkPort-1",
    )
    
    app = Application.from_object_list([device_object, network_port_object])
    logger.info("Test client created on 127.0.0.1:47809")
    
    await asyncio.sleep(1)
    
    # Direct address of the simulator
    simulator_address = Address("127.0.0.1:47808")
    device_instance = 1001
    
    logger.info(f"\nAttempting direct connection to device {device_instance} at {simulator_address}")
    logger.info("-" * 60)
    
    try:
        # Test 1: Read Device Name
        logger.info("\n[Test 1] Reading Device Object Name")
        result = await app.read_property(
            simulator_address,
            ("device", device_instance),
            "objectName"
        )
        logger.info(f"✓ Success! Device Name: {result}")
        
        # Test 2: Read Device Model
        logger.info("\n[Test 2] Reading Device Model Name")
        result = await app.read_property(
            simulator_address,
            ("device", device_instance),
            "modelName"
        )
        logger.info(f"✓ Success! Model Name: {result}")
        
        # Test 3: Read Device Description
        logger.info("\n[Test 3] Reading Device Description")
        result = await app.read_property(
            simulator_address,
            ("device", device_instance),
            "description"
        )
        logger.info(f"✓ Success! Description: {result}")
        
        # Test 4: Read Temperature (Analog Value 1)
        logger.info("\n[Test 4] Reading Temperature (Analog Value 1)")
        result = await app.read_property(
            simulator_address,
            ("analogValue", 1),
            "presentValue"
        )
        logger.info(f"✓ Success! Temperature: {result}°C")
        
        # Test 5: Read Humidity (Analog Value 2)
        logger.info("\n[Test 5] Reading Humidity (Analog Value 2)")
        result = await app.read_property(
            simulator_address,
            ("analogValue", 2),
            "presentValue"
        )
        logger.info(f"✓ Success! Humidity: {result}%")
        
        # Test 6: Read Fan Status (Binary Value 1)
        logger.info("\n[Test 6] Reading Fan Status (Binary Value 1)")
        result = await app.read_property(
            simulator_address,
            ("binaryValue", 1),
            "presentValue"
        )
        status = "ON" if result else "OFF"
        logger.info(f"✓ Success! Fan Status: {status}")
        
        # Test 7: Read Operating Mode (Multi-state Value 1)
        logger.info("\n[Test 7] Reading Operating Mode (Multi-state Value 1)")
        result = await app.read_property(
            simulator_address,
            ("multiStateValue", 1),
            "presentValue"
        )
        logger.info(f"✓ Success! Operating Mode: State {result}")
        
        # Test 8: Read state text
        result = await app.read_property(
            simulator_address,
            ("multiStateValue", 1),
            "stateText"
        )
        logger.info(f"  State Names: {result}")
        
        logger.info("\n" + "="*60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("The simulator is working correctly!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}", exc_info=True)
        logger.error("\nMake sure the simulator is running:")
        logger.error("  python3 bacnet_simulator.py")
        return False
    
    return True


if __name__ == '__main__':
    try:
        result = asyncio.run(direct_test())
        if not result:
            exit(1)
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)

