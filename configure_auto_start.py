#!/usr/bin/env python3
"""
Sensor Auto Start Configuration Tool

A cross-platform tool to configure M-A542VR1 sensors (A342/A352) to automatically
start transmitting sampling data after power-on or reset by enabling UART Auto Start mode.

This tool works on Linux, Windows, macOS, and other operating systems.

Author: Jnana Phani A
Organization: Zenith Tek

Usage:

Usage:
    python configure_auto_start.py <port> [baud_rate]
    python configure_auto_start.py --list-ports
    python configure_auto_start.py --help
    
Examples:
    # Linux
    python configure_auto_start.py /dev/ttyUSB0
    python configure_auto_start.py /dev/ttyUSB0 460800
    
    # Windows
    python configure_auto_start.py COM3
    python configure_auto_start.py COM3 460800
    
    # macOS
    python configure_auto_start.py /dev/tty.usbserial-1410
    python configure_auto_start.py /dev/tty.usbserial-1410 460800
    
    # List available ports
    python configure_auto_start.py --list-ports
"""

import argparse
import logging
import sys
from typing import Optional

# Import local modules
try:
    from platform_utils import PlatformUtils
    from sensor_comm import SensorCommunication
    from sensor_config import SensorConfigurator
except ImportError:
    # Try importing from current directory
    import os
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    try:
        from platform_utils import PlatformUtils
        from sensor_comm import SensorCommunication
        from sensor_config import SensorConfigurator
    except ImportError as e:
        print(f"Error: Failed to import required modules: {e}")
        print("Make sure all files are in the same directory:")
        print("  - configure_auto_start.py")
        print("  - platform_utils.py")
        print("  - sensor_comm.py")
        print("  - sensor_config.py")
        sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s |%(asctime)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Author and Organization information
AUTHOR = "Jnana Phani A"
ORGANIZATION = "Zenith Tek"

# Constants
DEFAULT_BAUD_RATE = 460800
SUPPORTED_BAUD_RATES = [230400, 460800, 921600]


def list_available_ports() -> None:
    """List all available serial ports."""
    print(f"\nDetected OS: {PlatformUtils.get_os()}")
    print(f"Port prefix: {PlatformUtils.get_default_port_prefix()}")
    print("\nAvailable serial ports:")
    
    ports = PlatformUtils.list_serial_ports()
    if ports:
        for i, port in enumerate(ports, 1):
            print(f"  {i}. {port}")
        print(f"\nTotal: {len(ports)} port(s) found")
    else:
        print("  No serial ports found")
        print("\nTroubleshooting:")
        print("  - Make sure the sensor is connected")
        print("  - Check USB cable connection")
        print("  - Try unplugging and replugging the device")
        if PlatformUtils.is_linux():
            print("  - Check if device appears in: ls -la /dev/ttyUSB*")


def validate_baud_rate(baud: int) -> bool:
    """Validate baud rate.
    
    Args:
        baud: Baud rate to validate
        
    Returns:
        True if valid, False otherwise
    """
    return baud in SUPPORTED_BAUD_RATES


def configure_sensor(port: str, baud: int) -> bool:
    """Configure sensor in UART Auto Start mode.
    
    Args:
        port: Serial port path
        baud: Baud rate
        
    Returns:
        True if successful, False otherwise
    """
    comm = None
    try:
        # Log author and organization information
        logger.info("=" * 60)
        logger.info(f"Sensor Auto Start Configuration Tool")
        logger.info(f"Author: {AUTHOR}")
        logger.info(f"Organization: {ORGANIZATION}")
        logger.info("=" * 60)
        
        # Validate port
        if not PlatformUtils.validate_port(port):
            logger.error(f"Invalid port name: {port}")
            logger.error(f"Valid port examples: {PlatformUtils.format_port_examples()}")
            return False
        
        # Validate baud rate
        if not validate_baud_rate(baud):
            logger.warning(f"Baud rate {baud} is not in recommended list: {SUPPORTED_BAUD_RATES}")
            logger.warning("Continuing anyway...")
        
        # Create communication object
        comm = SensorCommunication(port, baud)
        
        # Open connection
        logger.info(f"Connecting to {port} at {baud} baud")
        comm.open()
        
        # Create configurator
        configurator = SensorConfigurator(comm)
        
        # Configure sensor
        success = configurator.configure()
        
        if success:
            logger.info("=" * 60)
            logger.info("Configuration completed successfully!")
            logger.info(f"Developed by {AUTHOR} at {ORGANIZATION}")
            logger.info("=" * 60)
        
        return success
        
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        logger.error("\n" + PlatformUtils.get_port_permission_help())
        return False
    except FileNotFoundError as e:
        logger.error(f"Port not found: {e}")
        logger.error(f"Port '{port}' does not exist")
        logger.error("Use --list-ports to see available ports")
        return False
    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        return False
    finally:
        if comm:
            comm.close()


def main() -> int:
    """Main entry point for the configuration script."""
    parser = argparse.ArgumentParser(
        description="Configure M-A542VR1 sensors in UART Auto Start mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Linux
  python configure_auto_start.py /dev/ttyUSB0
  python configure_auto_start.py /dev/ttyUSB0 460800
  
  # Windows
  python configure_auto_start.py COM3
  python configure_auto_start.py COM3 460800
  
  # macOS
  python configure_auto_start.py /dev/tty.usbserial-1410
  
  # List available ports
  python configure_auto_start.py --list-ports
        """
    )
    
    parser.add_argument(
        "port",
        nargs="?",
        help="Serial port path (e.g., /dev/ttyUSB0, COM3, /dev/tty.usbserial-1410)"
    )
    parser.add_argument(
        "baud",
        nargs="?",
        type=int,
        default=DEFAULT_BAUD_RATE,
        help=f"Baud rate (default: {DEFAULT_BAUD_RATE}, supported: {SUPPORTED_BAUD_RATES})"
    )
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="List all available serial ports"
    )
    parser.add_argument(
        "--baud-rate",
        type=int,
        dest="baud",
        help=f"Baud rate (default: {DEFAULT_BAUD_RATE})"
    )
    
    args = parser.parse_args()
    
    # Handle list ports request
    if args.list_ports:
        list_available_ports()
        return 0
    
    # Check if port is provided
    if not args.port:
        parser.print_help()
        print("\nError: Port is required")
        print(f"Use --list-ports to see available ports")
        return 1
    
    # Configure sensor
    success = configure_sensor(args.port, args.baud)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
