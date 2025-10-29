#!/usr/bin/env python3
"""
BACnet Device Simulator

A flexible BACnet device simulator for testing BACnet applications.
Supports multiple object types with configurable properties.
"""

import asyncio
import sys
import yaml
import logging
import random
from typing import Dict, Any, List
from datetime import datetime

from bacpypes3.debugging import bacpypes_debugging, ModuleLogger
from bacpypes3.app import Application
from bacpypes3.local.device import DeviceObject
from bacpypes3.local.networkport import NetworkPortObject
from bacpypes3.local.analog import AnalogValueObject, AnalogInputObject, AnalogOutputObject
from bacpypes3.local.binary import BinaryValueObject, BinaryInputObject, BinaryOutputObject
from bacpypes3.local.multistate import (
    MultiStateValueObject,
    MultiStateInputObject,
    MultiStateOutputObject,
)
from bacpypes3.primitivedata import Real, Date, Time
from bacpypes3.basetypes import DateTime, StatusFlags, ServicesSupported
from bacpypes3.constructeddata import AnyAtomic
from bacpypes3.pdu import Address, LocalBroadcast
from bacpypes3.apdu import WhoIsRequest

# Module logger
_debug = 0
_log = ModuleLogger(globals())

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bacnet_simulator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@bacpypes_debugging
class BroadcastAwareApplication(Application):
    """
    Custom Application that ensures I-Am responses are properly broadcast.
    
    This overrides the Who-Is handler to ensure I-Am is always broadcast,
    not unicast to the requesting client.
    """
    
    async def do_WhoIsRequest(self, apdu: WhoIsRequest) -> None:
        """
        Handle Who-Is requests and respond with broadcast I-Am.
        
        This ensures the I-Am response goes to the broadcast address
        (e.g., 192.168.29.255) instead of unicast to the client.
        """
        if _debug:
            BroadcastAwareApplication._debug("do_WhoIsRequest %r", apdu)
        
        # Get our device instance
        device_instance = self.device_object.objectIdentifier[1]
        
        # Check if the Who-Is is for us (or for all devices)
        if apdu.deviceInstanceRangeLowLimit is not None:
            if device_instance < apdu.deviceInstanceRangeLowLimit:
                return
        if apdu.deviceInstanceRangeHighLimit is not None:
            if device_instance > apdu.deviceInstanceRangeHighLimit:
                return
        
        # Log the Who-Is request
        logger.info(f"Received Who-Is from {apdu.pduSource}")
        
        # Respond with I-Am to local broadcast
        # This sends to broadcast address (e.g., 192.168.29.255)
        logger.info(f"Sending I-Am response to broadcast")
        self.i_am(address=LocalBroadcast())


@bacpypes_debugging
class BACnetSimulator:
    """Main BACnet Device Simulator class"""
    
    def __init__(self, config_file: str = 'config.yaml'):
        """Initialize the simulator with configuration"""
        self.config_file = config_file
        self.config = self._load_config()
        self.app = None
        self.objects = {}
        self.simulation_tasks = []
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    async def setup(self):
        """Setup the BACnet application and device"""
        device_config = self.config.get('device', {})
        
        # Get network settings
        network_config = self.config.get('network', {})
        address = network_config.get('address', '192.168.29.200/24')
        port = network_config.get('port', 47808)
        
        # Format address properly for NetworkPortObject
        if '/' not in address:
            # If no netmask specified, add /24 for typical networks
            address = f"{address}/24"
        
        # Set supported services (required for bacnet4j clients)
        # ServicesSupported is a bitstring - create a list where 1 = supported, 0 = not supported
        # The list indices correspond to specific BACnet services
        services_list = [0] * 40  # Initialize with 40 service bits
        services_list[12] = 1  # read-property
        services_list[14] = 1  # read-property-multiple
        services_list[15] = 1  # write-property
        services_list[0] = 1   # acknowledge-alarm
        services_list[1] = 1   # cov-notification
        services_list[26] = 1  # who-has
        services_list[27] = 1  # who-is
        
        # Create device object with all required properties including protocolServicesSupported
        device_object = DeviceObject(
            objectIdentifier=("device", device_config.get('instance', 1001)),
            objectName=device_config.get('name', 'BACnet Simulator'),
            description=device_config.get('description', 'BACnet Device Simulator for Testing'),
            vendorIdentifier=device_config.get('vendor_id', 999),
            modelName=device_config.get('model', 'Virtual BACnet Device'),
            protocolServicesSupported=ServicesSupported(services_list),
        )
        
        # Create network port object (required for BACpypes3)
        network_port_object = NetworkPortObject(
            f"{address}:{port}",
            objectIdentifier=("network-port", 1),
            objectName="NetworkPort-1",
        )
        
        # Create the application with both device and network port
        # Use our custom BroadcastAwareApplication for proper I-Am broadcasts
        self.app = BroadcastAwareApplication.from_object_list(
            [device_object, network_port_object]
        )
        
        logger.info(f"BACnet device created: {device_object.objectName}")
        logger.info(f"Device Instance: {device_object.objectIdentifier[1]}")
        logger.info(f"Listening on: {address}:{port}")
        
        # Create objects
        await self._create_objects()
        
        # Note: BACpypes3 automatically responds to Who-Is requests with I-Am
        # No need to manually broadcast I-Am - it handles this internally
        logger.info("Device ready - will respond to Who-Is requests")
        
    async def _create_objects(self):
        """Create BACnet objects based on configuration"""
        objects_config = self.config.get('objects', [])
        
        for obj_config in objects_config:
            obj_type = obj_config.get('type')
            obj_instance = obj_config.get('instance')
            obj_name = obj_config.get('name', f'{obj_type}_{obj_instance}')
            
            # Create the appropriate object type
            if obj_type == 'analog-value':
                obj = self._create_analog_value(obj_config)
            elif obj_type == 'analog-input':
                obj = self._create_analog_input(obj_config)
            elif obj_type == 'analog-output':
                obj = self._create_analog_output(obj_config)
            elif obj_type == 'binary-value':
                obj = self._create_binary_value(obj_config)
            elif obj_type == 'binary-input':
                obj = self._create_binary_input(obj_config)
            elif obj_type == 'binary-output':
                obj = self._create_binary_output(obj_config)
            elif obj_type == 'multi-state-value':
                obj = self._create_multistate_value(obj_config)
            elif obj_type == 'multi-state-input':
                obj = self._create_multistate_input(obj_config)
            elif obj_type == 'multi-state-output':
                obj = self._create_multistate_output(obj_config)
            else:
                logger.warning(f"Unknown object type: {obj_type}")
                continue
            
            # Add object to application
            self.app.add_object(obj)
            self.objects[obj_name] = obj
            
            logger.info(f"Created {obj_type} object: {obj_name} (instance: {obj_instance})")
            
            # Start simulation if enabled
            if obj_config.get('simulate', False):
                task = asyncio.create_task(
                    self._simulate_object(obj, obj_config)
                )
                self.simulation_tasks.append(task)
    
    def _create_analog_value(self, config: Dict[str, Any]) -> AnalogValueObject:
        """Create an Analog Value object"""
        obj = AnalogValueObject(
            objectIdentifier=("analogValue", config['instance']),
            objectName=config.get('name', f"AV-{config['instance']}"),
            presentValue=Real(config.get('initial_value', 0.0)),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            units=config.get('units', 'degreesCelsius'),
            description=config.get('description', ''),
        )
        return obj
    
    def _create_analog_input(self, config: Dict[str, Any]) -> AnalogInputObject:
        """Create an Analog Input object"""
        obj = AnalogInputObject(
            objectIdentifier=("analogInput", config['instance']),
            objectName=config.get('name', f"AI-{config['instance']}"),
            presentValue=Real(config.get('initial_value', 0.0)),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            units=config.get('units', 'degreesCelsius'),
            description=config.get('description', ''),
        )
        return obj
    
    def _create_analog_output(self, config: Dict[str, Any]) -> AnalogOutputObject:
        """Create an Analog Output object"""
        obj = AnalogOutputObject(
            objectIdentifier=("analogOutput", config['instance']),
            objectName=config.get('name', f"AO-{config['instance']}"),
            presentValue=Real(config.get('initial_value', 0.0)),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            units=config.get('units', 'degreesCelsius'),
            description=config.get('description', ''),
        )
        return obj
    
    def _create_binary_value(self, config: Dict[str, Any]) -> BinaryValueObject:
        """Create a Binary Value object"""
        obj = BinaryValueObject(
            objectIdentifier=("binaryValue", config['instance']),
            objectName=config.get('name', f"BV-{config['instance']}"),
            presentValue=config.get('initial_value', 0),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            description=config.get('description', ''),
        )
        return obj
    
    def _create_binary_input(self, config: Dict[str, Any]) -> BinaryInputObject:
        """Create a Binary Input object"""
        obj = BinaryInputObject(
            objectIdentifier=("binaryInput", config['instance']),
            objectName=config.get('name', f"BI-{config['instance']}"),
            presentValue=config.get('initial_value', 0),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            description=config.get('description', ''),
        )
        return obj
    
    def _create_binary_output(self, config: Dict[str, Any]) -> BinaryOutputObject:
        """Create a Binary Output object"""
        obj = BinaryOutputObject(
            objectIdentifier=("binaryOutput", config['instance']),
            objectName=config.get('name', f"BO-{config['instance']}"),
            presentValue=config.get('initial_value', 0),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            description=config.get('description', ''),
        )
        return obj
    
    def _create_multistate_value(self, config: Dict[str, Any]) -> MultiStateValueObject:
        """Create a Multi-state Value object"""
        obj = MultiStateValueObject(
            objectIdentifier=("multiStateValue", config['instance']),
            objectName=config.get('name', f"MSV-{config['instance']}"),
            presentValue=config.get('initial_value', 1),
            numberOfStates=config.get('number_of_states', 3),
            stateText=config.get('state_text', ['State1', 'State2', 'State3']),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            description=config.get('description', ''),
        )
        return obj
    
    def _create_multistate_input(self, config: Dict[str, Any]) -> MultiStateInputObject:
        """Create a Multi-state Input object"""
        obj = MultiStateInputObject(
            objectIdentifier=("multiStateInput", config['instance']),
            objectName=config.get('name', f"MSI-{config['instance']}"),
            presentValue=config.get('initial_value', 1),
            numberOfStates=config.get('number_of_states', 3),
            stateText=config.get('state_text', ['State1', 'State2', 'State3']),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            description=config.get('description', ''),
        )
        return obj
    
    def _create_multistate_output(self, config: Dict[str, Any]) -> MultiStateOutputObject:
        """Create a Multi-state Output object"""
        obj = MultiStateOutputObject(
            objectIdentifier=("multiStateOutput", config['instance']),
            objectName=config.get('name', f"MSO-{config['instance']}"),
            presentValue=config.get('initial_value', 1),
            numberOfStates=config.get('number_of_states', 3),
            stateText=config.get('state_text', ['State1', 'State2', 'State3']),
            statusFlags=StatusFlags([0, 0, 0, 0]),
            description=config.get('description', ''),
        )
        return obj
    
    async def _simulate_object(self, obj, config: Dict[str, Any]):
        """Simulate value changes for an object"""
        sim_config = config.get('simulation', {})
        interval = sim_config.get('interval', 5.0)
        sim_type = sim_config.get('type', 'random')
        
        logger.info(f"Starting simulation for {obj.objectName} (type: {sim_type})")
        
        while True:
            try:
                await asyncio.sleep(interval)
                
                obj_type = config.get('type')
                
                if 'analog' in obj_type:
                    # Simulate analog values
                    if sim_type == 'random':
                        min_val = sim_config.get('min', 0.0)
                        max_val = sim_config.get('max', 100.0)
                        new_value = random.uniform(min_val, max_val)
                    elif sim_type == 'sine':
                        # Sine wave simulation
                        import math
                        amplitude = sim_config.get('amplitude', 50.0)
                        offset = sim_config.get('offset', 50.0)
                        frequency = sim_config.get('frequency', 0.1)
                        timestamp = datetime.now().timestamp()
                        new_value = offset + amplitude * math.sin(2 * math.pi * frequency * timestamp)
                    elif sim_type == 'increment':
                        # Incrementing value
                        step = sim_config.get('step', 1.0)
                        min_val = sim_config.get('min', 0.0)
                        max_val = sim_config.get('max', 100.0)
                        current = float(obj.presentValue)
                        new_value = current + step
                        if new_value > max_val:
                            new_value = min_val
                    else:
                        new_value = float(obj.presentValue)
                    
                    obj.presentValue = Real(new_value)
                    logger.debug(f"{obj.objectName}: {new_value:.2f}")
                
                elif 'binary' in obj_type:
                    # Simulate binary values
                    if sim_type == 'toggle':
                        new_value = 1 - int(obj.presentValue)
                    elif sim_type == 'random':
                        new_value = random.randint(0, 1)
                    else:
                        new_value = int(obj.presentValue)
                    
                    obj.presentValue = new_value
                    logger.debug(f"{obj.objectName}: {new_value}")
                
                elif 'multi' in obj_type.lower():
                    # Simulate multi-state values
                    num_states = config.get('number_of_states', 3)
                    if sim_type == 'cycle':
                        current = int(obj.presentValue)
                        new_value = (current % num_states) + 1
                    elif sim_type == 'random':
                        new_value = random.randint(1, num_states)
                    else:
                        new_value = int(obj.presentValue)
                    
                    obj.presentValue = new_value
                    logger.debug(f"{obj.objectName}: {new_value}")
                    
            except Exception as e:
                logger.error(f"Error simulating {obj.objectName}: {e}")
    
    async def run(self):
        """Run the simulator"""
        try:
            logger.info("="*60)
            logger.info("BACnet Device Simulator Started")
            logger.info("="*60)
            logger.info(f"Device: {self.config['device']['name']}")
            logger.info(f"Instance: {self.config['device']['instance']}")
            logger.info(f"Objects created: {len(self.objects)}")
            logger.info(f"Simulated objects: {len(self.simulation_tasks)}")
            logger.info("="*60)
            logger.info("Press Ctrl+C to stop the simulator")
            logger.info("="*60)
            
            # Run forever
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            logger.info("Shutting down simulator...")
        except Exception as e:
            logger.error(f"Error running simulator: {e}", exc_info=True)
        finally:
            # Cancel all simulation tasks
            for task in self.simulation_tasks:
                task.cancel()
            await asyncio.gather(*self.simulation_tasks, return_exceptions=True)
            logger.info("Simulator stopped")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BACnet Device Simulator')
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Create and run simulator
    simulator = BACnetSimulator(config_file=args.config)
    await simulator.setup()
    await simulator.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulator stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

