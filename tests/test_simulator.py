"""
Tests for Y86-64 Simulator Module - Integration Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from y86_simulator.simulator import Simulator, run_program
from y86_simulator.constants import STAT_HLT, STAT_AOK


class TestSimulatorBasic:
    """Basic tests for the Simulator class."""
    
    def test_simple_halt(self):
        """Test simple program that halts."""
        sim = Simulator()
        sim.load_assembly("halt")
        status = sim.run()
        
        assert status == STAT_HLT
    
    def test_nop_sequence(self):
        """Test program with nop sequence."""
        sim = Simulator()
        sim.load_assembly("""
            nop
            nop
            nop
            halt
        """)
        status = sim.run()
        
        assert status == STAT_HLT
        # halt stops execution, so only 3 nops are counted as completed
        assert sim.cpu.instruction_count == 3
    
    def test_register_operations(self):
        """Test register move operations."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $100, %rax
            rrmovq %rax, %rbx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rax") == 100
        assert sim.get_register("rbx") == 100


class TestSimulatorArithmetic:
    """Tests for arithmetic operations."""
    
    def test_add(self):
        """Test addition."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $10, %rax
            irmovq $20, %rbx
            addq %rax, %rbx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rbx") == 30
    
    def test_subtract(self):
        """Test subtraction."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $30, %rax
            irmovq $100, %rbx
            subq %rax, %rbx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rbx") == 70
    
    def test_subtract_negative(self):
        """Test subtraction with negative result."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $100, %rax
            irmovq $30, %rbx
            subq %rax, %rbx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rbx") == -70
    
    def test_and(self):
        """Test bitwise AND."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $0xFF, %rax
            irmovq $0x0F, %rbx
            andq %rax, %rbx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rbx") == 0x0F
    
    def test_xor(self):
        """Test bitwise XOR."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $0xFF, %rax
            irmovq $0x0F, %rbx
            xorq %rax, %rbx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rbx") == 0xF0


class TestSimulatorMemory:
    """Tests for memory operations."""
    
    def test_store_load(self):
        """Test memory store and load."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $0x1234, %rax
            irmovq $256, %rsp
            rmmovq %rax, 0(%rsp)
            mrmovq 0(%rsp), %rbx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rbx") == 0x1234
    
    def test_displacement(self):
        """Test memory access with displacement."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $42, %rax
            irmovq $100, %rbp
            rmmovq %rax, 16(%rbp)
            mrmovq 16(%rbp), %rcx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rcx") == 42
        assert sim.read_memory(116) == 42


class TestSimulatorJumps:
    """Tests for jump operations."""
    
    def test_unconditional_jump(self):
        """Test unconditional jump."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $1, %rax
            jmp skip
            irmovq $2, %rax
        skip:
            halt
        """)
        sim.run()
        
        assert sim.get_register("rax") == 1
    
    def test_conditional_jump_taken(self):
        """Test conditional jump when taken."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $10, %rax
            irmovq $10, %rbx
            subq %rax, %rbx    # rbx = 0, ZF = 1
            je equal
            irmovq $1, %rcx
            jmp done
        equal:
            irmovq $2, %rcx
        done:
            halt
        """)
        sim.run()
        
        assert sim.get_register("rcx") == 2
    
    def test_conditional_jump_not_taken(self):
        """Test conditional jump when not taken."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $10, %rax
            irmovq $20, %rbx
            subq %rax, %rbx    # rbx = 10, ZF = 0
            je equal
            irmovq $1, %rcx
            jmp done
        equal:
            irmovq $2, %rcx
        done:
            halt
        """)
        sim.run()
        
        assert sim.get_register("rcx") == 1
    
    def test_loop(self):
        """Test simple loop."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $5, %rcx      # counter
            irmovq $0, %rax      # sum
            irmovq $1, %rbx      # increment
        loop:
            addq %rbx, %rax
            subq %rbx, %rcx
            jne loop
            halt
        """)
        sim.run()
        
        assert sim.get_register("rax") == 5
        assert sim.get_register("rcx") == 0


class TestSimulatorStack:
    """Tests for stack operations."""
    
    def test_push_pop(self):
        """Test push and pop."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $42, %rax
            pushq %rax
            popq %rbx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rbx") == 42
    
    def test_multiple_push_pop(self):
        """Test multiple push and pop."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $1, %rax
            irmovq $2, %rbx
            irmovq $3, %rcx
            pushq %rax
            pushq %rbx
            pushq %rcx
            popq %rdi
            popq %rsi
            popq %rdx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rdi") == 3
        assert sim.get_register("rsi") == 2
        assert sim.get_register("rdx") == 1


class TestSimulatorCallRet:
    """Tests for call and ret operations."""
    
    def test_simple_call_ret(self):
        """Test simple function call and return."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $0, %rax
            call func
            halt
        func:
            irmovq $42, %rax
            ret
        """)
        sim.run()
        
        assert sim.get_register("rax") == 42
    
    def test_nested_calls(self):
        """Test nested function calls."""
        sim = Simulator()
        sim.load_assembly("""
            call outer
            halt
        outer:
            irmovq $1, %rax
            call inner
            ret
        inner:
            irmovq $2, %rbx
            ret
        """)
        sim.run()
        
        assert sim.get_register("rax") == 1
        assert sim.get_register("rbx") == 2


class TestSimulatorConditionalMoves:
    """Tests for conditional move operations."""
    
    def test_cmove_taken(self):
        """Test cmove when condition is met."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $10, %rax
            irmovq $10, %rbx
            subq %rax, %rbx     # ZF = 1
            irmovq $42, %rcx
            cmove %rcx, %rdx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rdx") == 42
    
    def test_cmove_not_taken(self):
        """Test cmove when condition is not met."""
        sim = Simulator()
        sim.load_assembly("""
            irmovq $10, %rax
            irmovq $20, %rbx
            subq %rax, %rbx     # ZF = 0
            irmovq $42, %rcx
            irmovq $99, %rdx
            cmove %rcx, %rdx
            halt
        """)
        sim.run()
        
        assert sim.get_register("rdx") == 99


class TestSimulatorPrograms:
    """Tests for complete programs."""
    
    def test_sum_array(self):
        """Test summing an array."""
        sim = Simulator()
        sim.load_assembly("""
        # Sum an array of 5 numbers
        .pos 0
            irmovq array, %rdi   # array pointer
            irmovq $5, %rsi      # count
            irmovq $0, %rax      # sum
            irmovq $8, %r8       # sizeof(quad)
            irmovq $1, %r9       # decrement
        loop:
            mrmovq 0(%rdi), %r10
            addq %r10, %rax
            addq %r8, %rdi
            subq %r9, %rsi
            jne loop
            halt
        
        .pos 0x100
        array:
            .quad 1
            .quad 2
            .quad 3
            .quad 4
            .quad 5
        """)
        sim.run()
        
        assert sim.get_register("rax") == 15
    
    def test_fibonacci(self):
        """Test Fibonacci sequence."""
        sim = Simulator()
        sim.load_assembly("""
        # Calculate Fibonacci(10)
            irmovq $10, %rdi     # n
            call fib
            halt
        
        fib:
            irmovq $1, %rax      # fib(0) = fib(1) = 1
            irmovq $2, %r8       # threshold
            subq %r8, %rdi
            jl fib_done          # if n < 2, return 1
            
            irmovq $0, %rax      # a = 0
            irmovq $1, %rbx      # b = 1
            irmovq $10, %rcx     # counter
        
        fib_loop:
            rrmovq %rbx, %rdx    # temp = b
            addq %rax, %rbx      # b = a + b
            rrmovq %rdx, %rax    # a = temp
            irmovq $1, %r9
            subq %r9, %rcx
            jne fib_loop
            
            rrmovq %rbx, %rax    # return b
        
        fib_done:
            ret
        """)
        sim.run()
        
        # Fibonacci(10) = 89
        assert sim.get_register("rax") == 89


class TestConvenienceFunction:
    """Tests for convenience functions."""
    
    def test_run_program(self):
        """Test run_program convenience function."""
        sim = run_program("""
            irmovq $42, %rax
            halt
        """)
        
        assert sim.get_register("rax") == 42
        assert sim.cpu.status == STAT_HLT
