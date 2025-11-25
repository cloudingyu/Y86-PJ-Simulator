"""
Tests for Y86-64 CPU Module
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from y86_simulator.cpu import CPU
from y86_simulator.memory import Memory
from y86_simulator.constants import (
    RRAX, RRCX, RRDX, RRBX, RRSP, RRBP, RRSI, RRDI,
    RR8, RR9, RR10, RR11, RR12, RR13, RR14, RNONE,
    STAT_AOK, STAT_HLT, STAT_ADR, STAT_INS,
    ALUADD, ALUSUB, ALUAND, ALUXOR,
    C_YES, C_LE, C_L, C_E, C_NE, C_GE, C_G
)


class TestCPURegisters:
    """Tests for CPU register operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.memory = Memory()
        self.cpu = CPU(self.memory)
    
    def test_initial_state(self):
        """Test initial CPU state."""
        assert self.cpu.pc == 0
        assert self.cpu.status == STAT_AOK
        assert all(r == 0 for r in self.cpu.registers)
        assert self.cpu.zf is True
        assert self.cpu.sf is False
        assert self.cpu.of is False
    
    def test_get_set_register(self):
        """Test getting and setting registers."""
        self.cpu.set_register(RRAX, 42)
        assert self.cpu.get_register(RRAX) == 42
        
        self.cpu.set_register(RRBX, -1)
        assert self.cpu.get_register(RRBX) == -1
    
    def test_get_register_none(self):
        """Test that RNONE returns 0."""
        assert self.cpu.get_register(RNONE) == 0
    
    def test_set_register_none(self):
        """Test that setting RNONE is ignored."""
        self.cpu.set_register(RNONE, 42)  # Should not raise
    
    def test_invalid_register(self):
        """Test that invalid register numbers raise error."""
        with pytest.raises(ValueError):
            self.cpu.get_register(16)
        
        with pytest.raises(ValueError):
            self.cpu.set_register(16, 0)
    
    def test_reset(self):
        """Test CPU reset."""
        self.cpu.set_register(RRAX, 42)
        self.cpu.pc = 100
        self.cpu.status = STAT_HLT
        
        self.cpu.reset()
        
        assert self.cpu.get_register(RRAX) == 0
        assert self.cpu.pc == 0
        assert self.cpu.status == STAT_AOK


class TestConditionCodes:
    """Tests for condition code handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.memory = Memory()
        self.cpu = CPU(self.memory)
    
    def test_update_cc_zero(self):
        """Test condition codes for zero result."""
        self.cpu.update_condition_codes(0)
        assert self.cpu.zf is True
        assert self.cpu.sf is False
    
    def test_update_cc_positive(self):
        """Test condition codes for positive result."""
        self.cpu.update_condition_codes(42)
        assert self.cpu.zf is False
        assert self.cpu.sf is False
    
    def test_update_cc_negative(self):
        """Test condition codes for negative result."""
        self.cpu.update_condition_codes(-1)
        assert self.cpu.zf is False
        assert self.cpu.sf is True
    
    def test_check_condition_yes(self):
        """Test unconditional condition."""
        assert self.cpu.check_condition(C_YES) is True
    
    def test_check_condition_e(self):
        """Test equal condition."""
        self.cpu.zf = True
        assert self.cpu.check_condition(C_E) is True
        
        self.cpu.zf = False
        assert self.cpu.check_condition(C_E) is False
    
    def test_check_condition_ne(self):
        """Test not equal condition."""
        self.cpu.zf = False
        assert self.cpu.check_condition(C_NE) is True
        
        self.cpu.zf = True
        assert self.cpu.check_condition(C_NE) is False
    
    def test_check_condition_l(self):
        """Test less than condition."""
        # SF != OF means less
        self.cpu.sf = True
        self.cpu.of = False
        assert self.cpu.check_condition(C_L) is True
        
        self.cpu.sf = False
        self.cpu.of = True
        assert self.cpu.check_condition(C_L) is True
        
        self.cpu.sf = False
        self.cpu.of = False
        assert self.cpu.check_condition(C_L) is False
    
    def test_check_condition_le(self):
        """Test less or equal condition."""
        # (SF != OF) || ZF
        self.cpu.sf = True
        self.cpu.of = False
        self.cpu.zf = False
        assert self.cpu.check_condition(C_LE) is True
        
        self.cpu.sf = False
        self.cpu.of = False
        self.cpu.zf = True
        assert self.cpu.check_condition(C_LE) is True
        
        self.cpu.sf = False
        self.cpu.of = False
        self.cpu.zf = False
        assert self.cpu.check_condition(C_LE) is False
    
    def test_check_condition_g(self):
        """Test greater than condition."""
        # (SF == OF) && !ZF
        self.cpu.sf = False
        self.cpu.of = False
        self.cpu.zf = False
        assert self.cpu.check_condition(C_G) is True
        
        self.cpu.sf = True
        self.cpu.of = True
        self.cpu.zf = False
        assert self.cpu.check_condition(C_G) is True
        
        self.cpu.sf = False
        self.cpu.of = False
        self.cpu.zf = True
        assert self.cpu.check_condition(C_G) is False
    
    def test_check_condition_ge(self):
        """Test greater or equal condition."""
        # SF == OF
        self.cpu.sf = False
        self.cpu.of = False
        assert self.cpu.check_condition(C_GE) is True
        
        self.cpu.sf = True
        self.cpu.of = True
        assert self.cpu.check_condition(C_GE) is True
        
        self.cpu.sf = True
        self.cpu.of = False
        assert self.cpu.check_condition(C_GE) is False


class TestCPUInstructions:
    """Tests for CPU instruction execution."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.memory = Memory()
        self.cpu = CPU(self.memory)
    
    def test_halt(self):
        """Test halt instruction."""
        # halt = 0x00
        self.memory.write_byte(0, 0x00)
        
        result = self.cpu.execute_instruction()
        
        assert result is False
        assert self.cpu.status == STAT_HLT
    
    def test_nop(self):
        """Test nop instruction."""
        # nop = 0x10
        self.memory.write_byte(0, 0x10)
        
        result = self.cpu.execute_instruction()
        
        assert result is True
        assert self.cpu.pc == 1
    
    def test_rrmovq(self):
        """Test rrmovq instruction."""
        # rrmovq %rax, %rbx = 0x20 0x03
        self.memory.write_byte(0, 0x20)
        self.memory.write_byte(1, 0x03)
        self.cpu.set_register(RRAX, 42)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == 42
        assert self.cpu.pc == 2
    
    def test_cmovle_taken(self):
        """Test conditional move (taken)."""
        # cmovle %rax, %rbx = 0x21 0x03
        self.memory.write_byte(0, 0x21)
        self.memory.write_byte(1, 0x03)
        self.cpu.set_register(RRAX, 42)
        self.cpu.zf = True  # Condition satisfied
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == 42
    
    def test_cmovle_not_taken(self):
        """Test conditional move (not taken)."""
        # cmovle %rax, %rbx = 0x21 0x03
        self.memory.write_byte(0, 0x21)
        self.memory.write_byte(1, 0x03)
        self.cpu.set_register(RRAX, 42)
        self.cpu.set_register(RRBX, 99)
        self.cpu.zf = False
        self.cpu.sf = False
        self.cpu.of = False  # Condition not satisfied
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == 99  # Unchanged
    
    def test_irmovq(self):
        """Test irmovq instruction."""
        # irmovq $123, %rdx = 0x30 0xF2 + 8-byte immediate
        self.memory.write_byte(0, 0x30)
        self.memory.write_byte(1, 0xF2)
        self.memory.write_quad(2, 123)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRDX) == 123
        assert self.cpu.pc == 10
    
    def test_rmmovq(self):
        """Test rmmovq instruction."""
        # rmmovq %rax, 0(%rsp) = 0x40 0x04 + 8-byte displacement
        self.memory.write_byte(0, 0x40)
        self.memory.write_byte(1, 0x04)
        self.memory.write_quad(2, 0)  # Displacement
        
        self.cpu.set_register(RRAX, 0x1234)
        self.cpu.set_register(RRSP, 100)
        
        self.cpu.execute_instruction()
        
        assert self.memory.read_quad(100) == 0x1234
        assert self.cpu.pc == 10
    
    def test_mrmovq(self):
        """Test mrmovq instruction."""
        # mrmovq 0(%rsp), %rax = 0x50 0x04 + 8-byte displacement
        self.memory.write_byte(0, 0x50)
        self.memory.write_byte(1, 0x04)
        self.memory.write_quad(2, 0)  # Displacement
        self.memory.write_quad(100, 0x5678)
        
        self.cpu.set_register(RRSP, 100)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRAX) == 0x5678
        assert self.cpu.pc == 10
    
    def test_addq(self):
        """Test addq instruction."""
        # addq %rax, %rbx = 0x60 0x03
        self.memory.write_byte(0, 0x60)
        self.memory.write_byte(1, 0x03)
        
        self.cpu.set_register(RRAX, 10)
        self.cpu.set_register(RRBX, 20)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == 30
        assert self.cpu.zf is False
        assert self.cpu.sf is False
    
    def test_subq(self):
        """Test subq instruction."""
        # subq %rax, %rbx = 0x61 0x03
        self.memory.write_byte(0, 0x61)
        self.memory.write_byte(1, 0x03)
        
        self.cpu.set_register(RRAX, 10)
        self.cpu.set_register(RRBX, 30)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == 20
    
    def test_subq_negative(self):
        """Test subq with negative result."""
        # subq %rax, %rbx = 0x61 0x03
        self.memory.write_byte(0, 0x61)
        self.memory.write_byte(1, 0x03)
        
        self.cpu.set_register(RRAX, 30)
        self.cpu.set_register(RRBX, 10)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == -20
        assert self.cpu.sf is True
    
    def test_andq(self):
        """Test andq instruction."""
        # andq %rax, %rbx = 0x62 0x03
        self.memory.write_byte(0, 0x62)
        self.memory.write_byte(1, 0x03)
        
        self.cpu.set_register(RRAX, 0xFF)
        self.cpu.set_register(RRBX, 0x0F)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == 0x0F
    
    def test_xorq(self):
        """Test xorq instruction."""
        # xorq %rax, %rbx = 0x63 0x03
        self.memory.write_byte(0, 0x63)
        self.memory.write_byte(1, 0x03)
        
        self.cpu.set_register(RRAX, 0xFF)
        self.cpu.set_register(RRBX, 0x0F)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == 0xF0
    
    def test_jmp(self):
        """Test unconditional jump."""
        # jmp 0x100 = 0x70 + 8-byte address
        self.memory.write_byte(0, 0x70)
        self.memory.write_quad(1, 0x100)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.pc == 0x100
    
    def test_je_taken(self):
        """Test conditional jump (taken)."""
        # je 0x100 = 0x73 + 8-byte address
        self.memory.write_byte(0, 0x73)
        self.memory.write_quad(1, 0x100)
        self.cpu.zf = True
        
        self.cpu.execute_instruction()
        
        assert self.cpu.pc == 0x100
    
    def test_je_not_taken(self):
        """Test conditional jump (not taken)."""
        # je 0x100 = 0x73 + 8-byte address
        self.memory.write_byte(0, 0x73)
        self.memory.write_quad(1, 0x100)
        self.cpu.zf = False
        
        self.cpu.execute_instruction()
        
        assert self.cpu.pc == 9
    
    def test_call(self):
        """Test call instruction."""
        # call 0x100 = 0x80 + 8-byte address
        self.memory.write_byte(0, 0x80)
        self.memory.write_quad(1, 0x100)
        self.cpu.set_register(RRSP, 1000)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.pc == 0x100
        assert self.cpu.get_register(RRSP) == 992
        assert self.memory.read_quad(992) == 9  # Return address
    
    def test_ret(self):
        """Test ret instruction."""
        # ret = 0x90
        self.memory.write_byte(0, 0x90)
        self.memory.write_quad(100, 0x200)  # Return address on stack
        self.cpu.set_register(RRSP, 100)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.pc == 0x200
        assert self.cpu.get_register(RRSP) == 108
    
    def test_pushq(self):
        """Test pushq instruction."""
        # pushq %rax = 0xA0 0x0F
        self.memory.write_byte(0, 0xA0)
        self.memory.write_byte(1, 0x0F)
        self.cpu.set_register(RRAX, 0x42)
        self.cpu.set_register(RRSP, 1000)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRSP) == 992
        assert self.memory.read_quad(992) == 0x42
    
    def test_popq(self):
        """Test popq instruction."""
        # popq %rbx = 0xB0 0x3F
        self.memory.write_byte(0, 0xB0)
        self.memory.write_byte(1, 0x3F)
        self.memory.write_quad(100, 0x99)
        self.cpu.set_register(RRSP, 100)
        
        self.cpu.execute_instruction()
        
        assert self.cpu.get_register(RRBX) == 0x99
        assert self.cpu.get_register(RRSP) == 108
    
    def test_invalid_instruction(self):
        """Test invalid instruction handling."""
        self.memory.write_byte(0, 0xF0)  # Invalid icode
        
        result = self.cpu.execute_instruction()
        
        assert result is False
        assert self.cpu.status == STAT_INS
    
    def test_invalid_memory_access(self):
        """Test invalid memory access handling."""
        # mrmovq from invalid address
        self.memory.write_byte(0, 0x50)
        self.memory.write_byte(1, 0x04)
        self.memory.write_quad(2, 0)
        self.cpu.set_register(RRSP, 10000)  # Beyond memory
        
        result = self.cpu.execute_instruction()
        
        assert result is False
        assert self.cpu.status == STAT_ADR
