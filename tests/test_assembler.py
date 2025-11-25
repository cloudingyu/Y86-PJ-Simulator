"""
Tests for Y86-64 Assembler Module
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from y86_simulator.assembler import Assembler, AssemblyError


class TestAssemblerBasic:
    """Basic tests for the Assembler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_empty_program(self):
        """Test assembling empty program."""
        result = self.asm.assemble("")
        assert result == b""
    
    def test_halt(self):
        """Test assembling halt instruction."""
        result = self.asm.assemble("halt")
        assert result == bytes([0x00])
    
    def test_nop(self):
        """Test assembling nop instruction."""
        result = self.asm.assemble("nop")
        assert result == bytes([0x10])
    
    def test_ret(self):
        """Test assembling ret instruction."""
        result = self.asm.assemble("ret")
        assert result == bytes([0x90])
    
    def test_multiple_instructions(self):
        """Test assembling multiple instructions."""
        result = self.asm.assemble("nop\nnop\nhalt")
        assert result == bytes([0x10, 0x10, 0x00])
    
    def test_comments(self):
        """Test that comments are ignored."""
        result = self.asm.assemble("nop # This is a comment\nhalt")
        assert result == bytes([0x10, 0x00])
    
    def test_blank_lines(self):
        """Test that blank lines are ignored."""
        result = self.asm.assemble("\n\nnop\n\nhalt\n\n")
        assert result == bytes([0x10, 0x00])


class TestAssemblerRegisters:
    """Tests for register operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_rrmovq(self):
        """Test rrmovq instruction."""
        result = self.asm.assemble("rrmovq %rax, %rbx")
        assert result == bytes([0x20, 0x03])
    
    def test_rrmovq_all_registers(self):
        """Test rrmovq with various registers."""
        code = "rrmovq %rcx, %rdx"
        result = self.asm.assemble(code)
        assert result == bytes([0x20, 0x12])
    
    def test_cmovle(self):
        """Test conditional move."""
        result = self.asm.assemble("cmovle %rax, %rbx")
        assert result == bytes([0x21, 0x03])
    
    def test_cmovl(self):
        """Test cmovl."""
        result = self.asm.assemble("cmovl %rax, %rbx")
        assert result == bytes([0x22, 0x03])
    
    def test_cmove(self):
        """Test cmove."""
        result = self.asm.assemble("cmove %rax, %rbx")
        assert result == bytes([0x23, 0x03])
    
    def test_cmovne(self):
        """Test cmovne."""
        result = self.asm.assemble("cmovne %rax, %rbx")
        assert result == bytes([0x24, 0x03])
    
    def test_cmovge(self):
        """Test cmovge."""
        result = self.asm.assemble("cmovge %rax, %rbx")
        assert result == bytes([0x25, 0x03])
    
    def test_cmovg(self):
        """Test cmovg."""
        result = self.asm.assemble("cmovg %rax, %rbx")
        assert result == bytes([0x26, 0x03])


class TestAssemblerImmediate:
    """Tests for immediate value operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_irmovq_decimal(self):
        """Test irmovq with decimal immediate."""
        result = self.asm.assemble("irmovq $100, %rax")
        assert result[0] == 0x30
        assert result[1] == 0xF0
        # Check little-endian encoding of 100
        assert result[2] == 100
        assert result[3:10] == bytes([0, 0, 0, 0, 0, 0, 0])
    
    def test_irmovq_hex(self):
        """Test irmovq with hexadecimal immediate."""
        result = self.asm.assemble("irmovq $0x100, %rbx")
        assert result[0] == 0x30
        assert result[1] == 0xF3
        assert result[2] == 0x00
        assert result[3] == 0x01
    
    def test_irmovq_negative(self):
        """Test irmovq with negative immediate."""
        result = self.asm.assemble("irmovq $-1, %rax")
        assert result[0] == 0x30
        assert result[1] == 0xF0
        # -1 in little-endian 64-bit
        assert result[2:10] == bytes([0xFF] * 8)


class TestAssemblerMemory:
    """Tests for memory operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_rmmovq_zero_disp(self):
        """Test rmmovq with zero displacement."""
        result = self.asm.assemble("rmmovq %rax, (%rbx)")
        assert result[0] == 0x40
        assert result[1] == 0x03
        assert result[2:10] == bytes([0] * 8)
    
    def test_rmmovq_positive_disp(self):
        """Test rmmovq with positive displacement."""
        result = self.asm.assemble("rmmovq %rax, 8(%rsp)")
        assert result[0] == 0x40
        assert result[1] == 0x04
        assert result[2] == 8
    
    def test_rmmovq_negative_disp(self):
        """Test rmmovq with negative displacement."""
        result = self.asm.assemble("rmmovq %rax, -8(%rsp)")
        assert result[0] == 0x40
        assert result[1] == 0x04
        # -8 in little-endian
        assert result[2] == 0xF8
        assert result[3:10] == bytes([0xFF] * 7)
    
    def test_mrmovq(self):
        """Test mrmovq instruction."""
        result = self.asm.assemble("mrmovq 16(%rbp), %rax")
        assert result[0] == 0x50
        assert result[1] == 0x05
        assert result[2] == 16


class TestAssemblerALU:
    """Tests for ALU operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_addq(self):
        """Test addq instruction."""
        result = self.asm.assemble("addq %rax, %rbx")
        assert result == bytes([0x60, 0x03])
    
    def test_subq(self):
        """Test subq instruction."""
        result = self.asm.assemble("subq %rax, %rbx")
        assert result == bytes([0x61, 0x03])
    
    def test_andq(self):
        """Test andq instruction."""
        result = self.asm.assemble("andq %rax, %rbx")
        assert result == bytes([0x62, 0x03])
    
    def test_xorq(self):
        """Test xorq instruction."""
        result = self.asm.assemble("xorq %rax, %rbx")
        assert result == bytes([0x63, 0x03])


class TestAssemblerJumps:
    """Tests for jump operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_jmp_address(self):
        """Test jmp with address."""
        result = self.asm.assemble("jmp 0x100")
        assert result[0] == 0x70
        assert result[1] == 0x00
        assert result[2] == 0x01
    
    def test_jle(self):
        """Test jle instruction."""
        result = self.asm.assemble("jle 0x50")
        assert result[0] == 0x71
        assert result[1] == 0x50
    
    def test_jl(self):
        """Test jl instruction."""
        result = self.asm.assemble("jl 0x50")
        assert result[0] == 0x72
    
    def test_je(self):
        """Test je instruction."""
        result = self.asm.assemble("je 0x50")
        assert result[0] == 0x73
    
    def test_jne(self):
        """Test jne instruction."""
        result = self.asm.assemble("jne 0x50")
        assert result[0] == 0x74
    
    def test_jge(self):
        """Test jge instruction."""
        result = self.asm.assemble("jge 0x50")
        assert result[0] == 0x75
    
    def test_jg(self):
        """Test jg instruction."""
        result = self.asm.assemble("jg 0x50")
        assert result[0] == 0x76


class TestAssemblerLabels:
    """Tests for label handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_simple_label(self):
        """Test simple label definition."""
        code = """
        start:
            nop
            halt
        """
        result = self.asm.assemble(code)
        assert result == bytes([0x10, 0x00])
        assert self.asm.labels["start"] == 0
    
    def test_jump_to_label(self):
        """Test jumping to a label."""
        code = """
            jmp done
            nop
        done:
            halt
        """
        result = self.asm.assemble(code)
        # jmp is at 0, done is at 10 (9 bytes for jmp + 1 byte for nop)
        assert result[0] == 0x70
        assert result[1] == 10  # Address of done
    
    def test_forward_reference(self):
        """Test forward reference to label."""
        code = """
            jmp end
        start:
            nop
        end:
            halt
        """
        result = self.asm.assemble(code)
        # jmp at 0, start at 9, end at 10
        assert self.asm.labels["start"] == 9
        assert self.asm.labels["end"] == 10
    
    def test_call_label(self):
        """Test calling a label."""
        code = """
            call func
            halt
        func:
            ret
        """
        result = self.asm.assemble(code)
        assert result[0] == 0x80  # call


class TestAssemblerDirectives:
    """Tests for assembler directives."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_pos(self):
        """Test .pos directive."""
        code = """
        .pos 0x100
        nop
        """
        result = self.asm.assemble(code)
        # Result should have 0x100 zero bytes, then nop
        assert len(result) == 0x101
        assert result[0x100] == 0x10
    
    def test_align(self):
        """Test .align directive."""
        code = """
        nop
        .align 8
        halt
        """
        result = self.asm.assemble(code)
        # nop at 0, then align to 8, halt at 8
        assert result[0] == 0x10
        assert result[8] == 0x00
    
    def test_quad(self):
        """Test .quad directive."""
        code = """
        .quad 0x1234567890ABCDEF
        """
        result = self.asm.assemble(code)
        assert len(result) == 8
        assert result == bytes([0xEF, 0xCD, 0xAB, 0x90, 0x78, 0x56, 0x34, 0x12])


class TestAssemblerStack:
    """Tests for stack operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_pushq(self):
        """Test pushq instruction."""
        result = self.asm.assemble("pushq %rax")
        assert result == bytes([0xA0, 0x0F])
    
    def test_popq(self):
        """Test popq instruction."""
        result = self.asm.assemble("popq %rbx")
        assert result == bytes([0xB0, 0x3F])


class TestAssemblerErrors:
    """Tests for error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.asm = Assembler()
    
    def test_unknown_instruction(self):
        """Test error on unknown instruction."""
        with pytest.raises(AssemblyError):
            self.asm.assemble("unknown")
    
    def test_invalid_register(self):
        """Test error on invalid register."""
        with pytest.raises(AssemblyError):
            self.asm.assemble("rrmovq %rxx, %rax")
    
    def test_undefined_label(self):
        """Test error on undefined label."""
        with pytest.raises(AssemblyError):
            self.asm.assemble("jmp undefined")
    
    def test_missing_operand(self):
        """Test error on missing operand."""
        with pytest.raises(AssemblyError):
            self.asm.assemble("rrmovq %rax")
