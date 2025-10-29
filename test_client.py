#!/usr/bin/env python3
"""
BACnet Test Client

Simple test client to verify the BACnet simulator is working correctly.
Performs Who-Is, Read-Property, and Write-Property operations.
"""

import asyncio
import sys
import logging
from typing import Optional

from bacpypes3.debugging import bacpypes_debugging, ModuleLogger
from bacpypes3.pdu import Address
from bacpypes3.app import Application
from bacpypes3.local.device import DeviceObject
from bacpypes3.local.networkport import NetworkPortObject
from bacpypes3.primitivedata import ObjectIdentifier, Real
from bacpypes3.apdu import ErrorRejectAbortNack

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class BACnetTestClient:
    """Test client for BACnet simulator"""
    
    def __init__(self, address: str = "127.0.0.1/32:47809"):
        """Initialize test client with address"""
        self.address = address
        self.app = None
        
    async def setup(self):
        """Setup the BACnet application"""
        device_instance = 999999
        
        device_object = DeviceObject(
            objectIdentifier=("device", device_instance),
            objectName=f"Test-Client-{device_instance}",
            vendorIdentifier=999,
        )
        
        # Create network port object (required for BACpypes3)
        network_port_object = NetworkPortObject(
            self.address,
            objectIdentifier=("network-port", 1),
            objectName="NetworkPort-1",
        )
        
        # Create the application with both device and network port
        self.app = Application.from_object_list(
            [device_object, network_port_object]
        )
        logger.info(f"Test client initialized on {self.address}")
    
    async def who_is(self, low_limit: Optional[int] = None, high_limit: Optional[int] = None):
        """Send Who-Is request to discover devices"""
        logger.info("Sending Who-Is request...")
        
        try:
            i_ams = await self.app.who_is(low_limit, high_limit)
            
            if i_ams:
                logger.info(f"Found {len(i_ams)} device(s):")
                for i_am in i_ams:
                    device_instance = i_am.iAmDeviceIdentifier[1]
                    device_address = i_am.pduSource
                    logger.info(f"  - Device {device_instance} at {device_address}")
                return i_ams
            else:
                logger.warning("No devices found")
                return []
        except Exception as e:
            logger.error(f"Error during Who-Is: {e}", exc_info=True)
            return []
    
    async def read_property(
        self, 
        device_address: str, 
        object_id: tuple, 
        property_name: str = "presentValue"
    ):
        """Read a property from a BACnet object"""
        try:
            logger.info(f"Reading {property_name} from {object_id} at {device_address}")
            
            address = Address(device_address)
            object_identifier = ObjectIdentifier(object_id)
            
            property_value = await self.app.read_property(
                address,
                object_identifier,
                property_name
            )
            
            if isinstance(property_value, ErrorRejectAbortNack):
                logger.error(f"Error reading property: {property_value}")
                return None
            
            logger.info(f"  Value: {property_value}")
            return property_value
            
        except Exception as e:
            logger.error(f"Error reading property: {e}", exc_info=True)
            return None
    
    async def write_property(
        self,
        device_address: str,
        object_id: tuple,
        value,
        property_name: str = "presentValue",
        priority: Optional[int] = None
    ):
        """Write a property to a BACnet object"""
        try:
            logger.info(f"Writing {value} to {property_name} of {object_id} at {device_address}")
            
            address = Address(device_address)
            object_identifier = ObjectIdentifier(object_id)
            
            response = await self.app.write_property(
                address,
                object_identifier,
                property_name,
                value,
                priority=priority
            )
            
            if isinstance(response, ErrorRejectAbortNack):
                logger.error(f"Error writing property: {response}")
                return False
            
            logger.info(f"  Write successful")
            return True
            
        except Exception as e:
            logger.error(f"Error writing property: {e}", exc_info=True)
            return False
    
    async def run_tests(self, target_device: Optional[int] = None):
        """Run a series of tests on the simulator"""
        logger.info("="*60)
        logger.info("Starting BACnet Test Suite")
        logger.info("="*60)
        
        # Test 1: Device Discovery
        logger.info("\n[Test 1] Device Discovery (Who-Is)")
        logger.info("-" * 60)
        logger.info(f"Searching for device instance {target_device}...")
        i_ams = await self.who_is(target_device, target_device)
        
        if not i_ams:
            logger.error("No devices found. Make sure the simulator is running.")
            return
        
        # Use the first device found
        target_i_am = i_ams[0]
        device_address = str(target_i_am.pduSource)
        device_instance = target_i_am.iAmDeviceIdentifier[1]
        
        await asyncio.sleep(1)
        
        # Test 2: Read Device Object
        logger.info("\n[Test 2] Reading Device Properties")
        logger.info("-" * 60)
        
        await self.read_property(device_address, ("device", device_instance), "objectName")
        await self.read_property(device_address, ("device", device_instance), "modelName")
        await self.read_property(device_address, ("device", device_instance), "vendorIdentifier")
        
        await asyncio.sleep(1)
        
        # Test 3: Read Analog Values
        logger.info("\n[Test 3] Reading Analog Values")
        logger.info("-" * 60)
        
        analog_objects = [
            ("analogValue", 1, "Temperature"),
            ("analogValue", 2, "Humidity"),
            ("analogInput", 1, "Pressure"),
        ]
        
        for obj_type, obj_instance, obj_name in analog_objects:
            value = await self.read_property(device_address, (obj_type, obj_instance), "presentValue")
            if value is not None:
                await self.read_property(device_address, (obj_type, obj_instance), "objectName")
        
        await asyncio.sleep(1)
        
        # Test 4: Read Binary Values
        logger.info("\n[Test 4] Reading Binary Values")
        logger.info("-" * 60)
        
        binary_objects = [
            ("binaryValue", 1, "Fan_Status"),
            ("binaryInput", 1, "Door_Sensor"),
        ]
        
        for obj_type, obj_instance, obj_name in binary_objects:
            value = await self.read_property(device_address, (obj_type, obj_instance), "presentValue")
            if value is not None:
                await self.read_property(device_address, (obj_type, obj_instance), "objectName")
        
        await asyncio.sleep(1)
        
        # Test 5: Read Multi-state Values
        logger.info("\n[Test 5] Reading Multi-state Values")
        logger.info("-" * 60)
        
        multistate_objects = [
            ("multiStateValue", 1, "Operating_Mode"),
            ("multiStateInput", 1, "System_Status"),
        ]
        
        for obj_type, obj_instance, obj_name in multistate_objects:
            value = await self.read_property(device_address, (obj_type, obj_instance), "presentValue")
            if value is not None:
                await self.read_property(device_address, (obj_type, obj_instance), "stateText")
        
        await asyncio.sleep(1)
        
        # Test 6: Write Operations
        logger.info("\n[Test 6] Write Operations")
        logger.info("-" * 60)
        
        # Write to analog output
        logger.info("Writing to Temperature Setpoint (Analog Output 1)")
        success = await self.write_property(
            device_address,
            ("analogOutput", 1),
            Real(23.5)
        )
        if success:
            await asyncio.sleep(0.5)
            await self.read_property(device_address, ("analogOutput", 1), "presentValue")
        
        await asyncio.sleep(1)
        
        # Write to binary output
        logger.info("Writing to Alarm Output (Binary Output 1)")
        success = await self.write_property(
            device_address,
            ("binaryOutput", 1),
            1
        )
        if success:
            await asyncio.sleep(0.5)
            await self.read_property(device_address, ("binaryOutput", 1), "presentValue")
        
        await asyncio.sleep(1)
        
        # Test 7: Monitor changing values
        logger.info("\n[Test 7] Monitoring Simulated Values (10 seconds)")
        logger.info("-" * 60)
        
        for i in range(5):
            logger.info(f"Reading #{i+1}...")
            await self.read_property(device_address, ("analogValue", 1), "presentValue")
            await asyncio.sleep(2)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Test Suite Completed")
        logger.info("="*60)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BACnet Test Client')
    parser.add_argument(
        '-a', '--address',
        default='127.0.0.1/32:47809',
        help='Client address (default: 127.0.0.1/32:47809)'
    )
    parser.add_argument(
        '-d', '--device',
        type=int,
        default=1001,
        help='Target device instance (default: 1001)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run test client
    client = BACnetTestClient(address=args.address)
    await client.setup()
    await client.run_tests(target_device=args.device)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest client stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

