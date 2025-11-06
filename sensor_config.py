"""
Sensor configuration module.

This module handles sensor configuration operations including
UART Auto Start mode setup and flash backup.
"""

import logging
import sys
import time
from typing import List

# Import sensor communication module
try:
    from sensor_comm import SensorCommunication
except ImportError:
    # Try relative import if in package
    try:
        from .sensor_comm import SensorCommunication
    except ImportError:
        print("Error: Could not import sensor_comm module")
        sys.exit(1)

logger = logging.getLogger(__name__)

# Constants
FLASH_BACKUP_TIMEOUT = 5.0
BACKUP_POLL_INTERVAL = 0.1


class SensorConfigurator:
    """Sensor configuration operations."""

    def __init__(self, comm: SensorCommunication):
        """Initialize configurator.
        
        Args:
            comm: SensorCommunication instance
        """
        self.comm = comm

    def reset_sensor(self) -> None:
        """Send reset commands to sensor."""
        reset_commands = [
            [0, 0xFF, 0xFF, 0x0D],  # Reset spell 3 times
            [0, 0xFF, 0xFF, 0x0D],
            [0, 0xFF, 0xFF, 0x0D],
        ]
        self.comm.send_commands(reset_commands)
        logger.debug("Sensor reset commands sent")

    def set_uart_auto_start(self) -> bool:
        """Set UART_CTRL register to enable UART Auto Start mode.
        
        Sets both AUTO_START (bit [1]) and UART_AUTO (bit [0]) to 1.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.reset_sensor()
            
            commands = [
                [0, 0xFE, 0x01, 0x0D],  # Window 1
                [0, 0x88, 0x03, 0x0D],  # UART_CTRL: AUTO_START=1, UART_AUTO=1
            ]
            self.comm.send_commands(commands)
            logger.info("UART_CTRL register set to 0x03 (AUTO_START=1, UART_AUTO=1)")
            return True
        except Exception as e:
            logger.error(f"Failed to set UART_CTRL: {e}")
            return False

    def flash_backup(self) -> bool:
        """Perform non-volatile memory backup to persist Auto Start setting.
        
        According to documentation:
        1. Write FLASH_BACKUP command to GLOB_CMD register
        2. Wait for backup completion by polling GLOB_CMD bit [3]
        3. Verify backup result by checking FLASH_BU_ERR in DIAG_STAT1
        
        Returns:
            True if backup successful, False otherwise
        """
        try:
            # Step 1: Write FLASH_BACKUP command
            commands = [
                [0, 0xFE, 0x01, 0x0D],  # Window 1
                [0, 0x8A, 0x08, 0x0D],  # GLOB_CMD: FLASH_BACKUP=1 (bit [3])
            ]
            self.comm.send_commands(commands)
            logger.info("Flash backup command sent")
            
            # Step 2: Wait for backup completion by polling GLOB_CMD
            start_time = time.time()
            while time.time() - start_time < FLASH_BACKUP_TIMEOUT:
                # Read GLOB_CMD register
                read_commands = [
                    [0, 0xFE, 0x01, 0x0D],  # Window 1
                    [4, 0x0A, 0x00, 0x0D],  # Read GLOB_CMD -> 4 bytes
                ]
                result = self.comm.send_commands(read_commands)
                
                # Check bit [3] of GLOB_CMD (FLASH_BACKUP status)
                # Result format: [Addr, MSByte, LSByte, CR] for each read
                if len(result) >= 4:
                    # GLOB_CMD is 16-bit, bit [3] is in the lower byte
                    glob_cmd_low = result[2]  # LSByte
                    if (glob_cmd_low & 0b00001000) == 0:
                        logger.info("Flash backup completed")
                        break
                time.sleep(BACKUP_POLL_INTERVAL)
            else:
                logger.error("Flash backup timeout - backup may not have completed")
                return False
            
            # Step 3: Verify backup result by checking FLASH_BU_ERR
            verify_commands = [
                [0, 0xFE, 0x00, 0x0D],  # Window 0
                [4, 0x04, 0x00, 0x0D],  # Read DIAG_STAT1 -> 4 bytes
            ]
            result = self.comm.send_commands(verify_commands)
            
            if len(result) >= 4:
                # Check FLASH_BU_ERR (bit [0] of DIAG_STAT1)
                diag_stat1_low = result[2]  # LSByte
                if (diag_stat1_low & 0b00000001) == 0:
                    logger.info("Flash backup verified successfully")
                    return True
                else:
                    logger.error("Flash backup error detected (FLASH_BU_ERR=1)")
                    return False
            else:
                logger.error("Failed to read DIAG_STAT1 for verification")
                return False
                
        except Exception as e:
            logger.error(f"Flash backup failed: {e}")
            return False

    def configure(self) -> bool:
        """Configure sensor in UART Auto Start mode.
        
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            # Step 1: Set UART_CTRL to enable Auto Start
            if not self.set_uart_auto_start():
                return False
            
            # Step 2: Perform flash backup
            if not self.flash_backup():
                return False
            
            logger.info("Sensor configured in UART Auto Start mode successfully")
            logger.info("After power cycle or reset, sensor will automatically start transmitting data")
            return True
            
        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

