"""
Tests for Y86-64 Memory Module
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from y86_simulator.memory import Memory


class TestMemory:
    """Tests for the Memory class."""
    
    def test_init_default_size(self):
        """Test default memory size."""
        mem = Memory()
        assert mem.size == 4096
    
    def test_init_custom_size(self):
        """Test custom memory size."""
        mem = Memory(1024)
        assert mem.size == 1024
    
    def test_read_write_byte(self):
        """Test reading and writing single bytes."""
        mem = Memory()
        mem.write_byte(0, 0x42)
        assert mem.read_byte(0) == 0x42
        
        mem.write_byte(100, 0xFF)
        assert mem.read_byte(100) == 0xFF
    
    def test_read_write_quad(self):
        """Test reading and writing 64-bit values."""
        mem = Memory()
        
        # Test positive value
        mem.write_quad(0, 0x0102030405060708)
        assert mem.read_quad(0) == 0x0102030405060708
        
        # Test negative value
        mem.write_quad(16, -1)
        assert mem.read_quad(16) == -1
        
        # Test another negative value
        mem.write_quad(32, -12345)
        assert mem.read_quad(32) == -12345
    
    def test_little_endian(self):
        """Test that values are stored in little-endian format."""
        mem = Memory()
        mem.write_quad(0, 0x0807060504030201)
        
        assert mem.read_byte(0) == 0x01
        assert mem.read_byte(1) == 0x02
        assert mem.read_byte(2) == 0x03
        assert mem.read_byte(3) == 0x04
        assert mem.read_byte(4) == 0x05
        assert mem.read_byte(5) == 0x06
        assert mem.read_byte(6) == 0x07
        assert mem.read_byte(7) == 0x08
    
    def test_is_valid_address(self):
        """Test address validation."""
        mem = Memory(100)
        
        assert mem.is_valid_address(0)
        assert mem.is_valid_address(99)
        assert not mem.is_valid_address(100)
        assert not mem.is_valid_address(-1)
        
        assert mem.is_valid_address(0, 8)
        assert mem.is_valid_address(92, 8)
        assert not mem.is_valid_address(93, 8)
    
    def test_invalid_address_read(self):
        """Test that reading from invalid address raises error."""
        mem = Memory(100)
        
        with pytest.raises(ValueError):
            mem.read_byte(100)
        
        with pytest.raises(ValueError):
            mem.read_quad(93)
    
    def test_invalid_address_write(self):
        """Test that writing to invalid address raises error."""
        mem = Memory(100)
        
        with pytest.raises(ValueError):
            mem.write_byte(100, 0)
        
        with pytest.raises(ValueError):
            mem.write_quad(93, 0)
    
    def test_load_program(self):
        """Test loading a program into memory."""
        mem = Memory()
        program = bytes([0x00, 0x10, 0x30, 0xF2, 0x05])
        
        mem.load_program(program, 0)
        
        assert mem.read_byte(0) == 0x00
        assert mem.read_byte(1) == 0x10
        assert mem.read_byte(2) == 0x30
        assert mem.read_byte(3) == 0xF2
        assert mem.read_byte(4) == 0x05
    
    def test_load_program_offset(self):
        """Test loading a program at an offset."""
        mem = Memory()
        program = bytes([0x42])
        
        mem.load_program(program, 100)
        
        assert mem.read_byte(99) == 0x00
        assert mem.read_byte(100) == 0x42
        assert mem.read_byte(101) == 0x00
    
    def test_reset(self):
        """Test memory reset."""
        mem = Memory()
        mem.write_byte(0, 0xFF)
        mem.write_byte(100, 0xFF)
        
        mem.reset()
        
        assert mem.read_byte(0) == 0x00
        assert mem.read_byte(100) == 0x00
    
    def test_dump(self):
        """Test memory dump."""
        mem = Memory()
        mem.write_byte(0, 0x42)
        
        dump = mem.dump(0, 16)
        assert "42" in dump


class TestMemoryEdgeCases:
    """Edge case tests for Memory."""
    
    def test_zero_value(self):
        """Test storing and retrieving zero."""
        mem = Memory()
        mem.write_quad(0, 0)
        assert mem.read_quad(0) == 0
    
    def test_max_positive(self):
        """Test maximum positive 64-bit value."""
        mem = Memory()
        max_val = (1 << 63) - 1
        mem.write_quad(0, max_val)
        assert mem.read_quad(0) == max_val
    
    def test_min_negative(self):
        """Test minimum negative 64-bit value."""
        mem = Memory()
        min_val = -(1 << 63)
        mem.write_quad(0, min_val)
        assert mem.read_quad(0) == min_val
