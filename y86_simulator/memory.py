"""
Y86-64 Memory Module

Implements the memory subsystem for the Y86-64 simulator.
"""

from .constants import DEFAULT_MEM_SIZE


class Memory:
    """
    Simulates the memory of a Y86-64 processor.
    
    Memory is byte-addressable and stores 64-bit values in little-endian format.
    """
    
    def __init__(self, size: int = DEFAULT_MEM_SIZE):
        """
        Initialize memory with the specified size.
        
        Args:
            size: The size of memory in bytes (default: 4096)
        """
        self.size = size
        self.data = bytearray(size)
    
    def is_valid_address(self, address: int, length: int = 1) -> bool:
        """
        Check if an address range is valid.
        
        Args:
            address: The starting address
            length: The number of bytes to access
            
        Returns:
            True if the address range is valid, False otherwise
        """
        return 0 <= address and address + length <= self.size
    
    def read_byte(self, address: int) -> int:
        """
        Read a single byte from memory.
        
        Args:
            address: The memory address to read from
            
        Returns:
            The byte value at the address
            
        Raises:
            ValueError: If the address is invalid
        """
        if not self.is_valid_address(address):
            raise ValueError(f"Invalid memory address: 0x{address:x}")
        return self.data[address]
    
    def write_byte(self, address: int, value: int) -> None:
        """
        Write a single byte to memory.
        
        Args:
            address: The memory address to write to
            value: The byte value to write (0-255)
            
        Raises:
            ValueError: If the address is invalid
        """
        if not self.is_valid_address(address):
            raise ValueError(f"Invalid memory address: 0x{address:x}")
        self.data[address] = value & 0xFF
    
    def read_quad(self, address: int) -> int:
        """
        Read a 64-bit (quad) value from memory in little-endian format.
        
        Args:
            address: The memory address to read from
            
        Returns:
            The 64-bit value at the address
            
        Raises:
            ValueError: If the address range is invalid
        """
        if not self.is_valid_address(address, 8):
            raise ValueError(f"Invalid memory address range: 0x{address:x}")
        
        value = 0
        for i in range(8):
            value |= self.data[address + i] << (i * 8)
        
        # Handle signed 64-bit values
        if value >= (1 << 63):
            value -= (1 << 64)
        
        return value
    
    def write_quad(self, address: int, value: int) -> None:
        """
        Write a 64-bit (quad) value to memory in little-endian format.
        
        Args:
            address: The memory address to write to
            value: The 64-bit value to write
            
        Raises:
            ValueError: If the address range is invalid
        """
        if not self.is_valid_address(address, 8):
            raise ValueError(f"Invalid memory address range: 0x{address:x}")
        
        # Handle negative values (two's complement)
        if value < 0:
            value += (1 << 64)
        
        for i in range(8):
            self.data[address + i] = (value >> (i * 8)) & 0xFF
    
    def load_program(self, program: bytes, start_address: int = 0) -> None:
        """
        Load a program (byte sequence) into memory starting at the specified address.
        
        Args:
            program: The program bytes to load
            start_address: The starting address (default: 0)
            
        Raises:
            ValueError: If the program doesn't fit in memory
        """
        if not self.is_valid_address(start_address, len(program)):
            raise ValueError("Program doesn't fit in memory")
        
        for i, byte in enumerate(program):
            self.data[start_address + i] = byte
    
    def dump(self, start: int = 0, length: int = 64) -> str:
        """
        Dump memory contents as a hexadecimal string.
        
        Args:
            start: Starting address
            length: Number of bytes to dump
            
        Returns:
            A formatted string showing memory contents
        """
        lines = []
        end = min(start + length, self.size)
        
        for addr in range(start, end, 16):
            hex_bytes = " ".join(f"{self.data[addr + i]:02x}" 
                                 for i in range(min(16, end - addr)))
            lines.append(f"0x{addr:04x}: {hex_bytes}")
        
        return "\n".join(lines)
    
    def reset(self) -> None:
        """Reset memory to all zeros."""
        self.data = bytearray(self.size)
