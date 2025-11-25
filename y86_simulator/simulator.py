"""
Y86-64 Simulator Module

Main simulator class that integrates CPU, memory, and assembler.
"""

from typing import Optional, Dict, List
from .cpu import CPU
from .memory import Memory
from .assembler import Assembler
from .constants import STAT_AOK, STAT_HLT, STATUS_NAMES, RRSP, DEFAULT_MEM_SIZE


class Simulator:
    """
    Y86-64 Processor Simulator
    
    Provides a complete simulation environment for Y86-64 programs.
    """
    
    def __init__(self, mem_size: int = DEFAULT_MEM_SIZE):
        """
        Initialize the simulator.
        
        Args:
            mem_size: Size of memory in bytes (default: 4096)
        """
        self.memory = Memory(mem_size)
        self.cpu = CPU(self.memory)
        self.assembler = Assembler()
        self.labels: Dict[str, int] = {}
        self.trace = False
        self.max_instructions = 10000  # Prevent infinite loops
    
    def reset(self) -> None:
        """Reset the simulator to initial state."""
        self.memory.reset()
        self.cpu.reset()
        self.labels = {}
    
    def load_program(self, program: bytes, start_address: int = 0) -> None:
        """
        Load a program into memory.
        
        Args:
            program: The program bytes to load
            start_address: The starting address (default: 0)
        """
        self.memory.load_program(program, start_address)
    
    def load_assembly(self, source: str, stack_address: Optional[int] = None) -> None:
        """
        Assemble and load a Y86-64 assembly program.
        
        Args:
            source: Y86-64 assembly source code
            stack_address: Initial stack pointer value (default: end of memory)
        """
        self.reset()
        program = self.assembler.assemble(source)
        self.labels = self.assembler.get_labels()
        self.load_program(program)
        
        # Set initial stack pointer
        if stack_address is None:
            stack_address = self.memory.size
        self.cpu.set_register(RRSP, stack_address)
    
    def load_assembly_file(self, filename: str, stack_address: Optional[int] = None) -> None:
        """
        Load a Y86-64 assembly file.
        
        Args:
            filename: Path to the source file
            stack_address: Initial stack pointer value
        """
        with open(filename, "r") as f:
            source = f.read()
        self.load_assembly(source, stack_address)
    
    def step(self) -> bool:
        """
        Execute a single instruction.
        
        Returns:
            True if execution should continue, False if halted
        """
        if self.trace:
            print(f"\n=== Step {self.cpu.instruction_count + 1} ===")
            print(f"PC: 0x{self.cpu.pc:04x}")
        
        result = self.cpu.execute_instruction()
        
        if self.trace:
            print(f"Status: {STATUS_NAMES.get(self.cpu.status, 'UNKNOWN')}")
            print(f"CC: ZF={int(self.cpu.zf)} SF={int(self.cpu.sf)} OF={int(self.cpu.of)}")
        
        return result
    
    def run(self, trace: bool = False) -> int:
        """
        Run the program until it halts or an error occurs.
        
        Args:
            trace: If True, print execution trace
            
        Returns:
            The final status code
        """
        self.trace = trace
        
        while self.cpu.status == STAT_AOK:
            if self.cpu.instruction_count >= self.max_instructions:
                print(f"Warning: Maximum instructions ({self.max_instructions}) reached")
                break
            self.step()
        
        if trace:
            print("\n=== Final State ===")
            print(self.cpu.dump_state())
        
        return self.cpu.status
    
    def get_register(self, reg_name: str) -> int:
        """
        Get a register value by name.
        
        Args:
            reg_name: Register name (e.g., "%rax" or "rax")
            
        Returns:
            The register value
        """
        if not reg_name.startswith("%"):
            reg_name = "%" + reg_name
        reg_code = self.assembler.REGISTERS.get(reg_name.lower())
        if reg_code is None:
            raise ValueError(f"Unknown register: {reg_name}")
        return self.cpu.get_register(reg_code)
    
    def set_register(self, reg_name: str, value: int) -> None:
        """
        Set a register value by name.
        
        Args:
            reg_name: Register name (e.g., "%rax" or "rax")
            value: The value to set
        """
        if not reg_name.startswith("%"):
            reg_name = "%" + reg_name
        reg_code = self.assembler.REGISTERS.get(reg_name.lower())
        if reg_code is None:
            raise ValueError(f"Unknown register: {reg_name}")
        self.cpu.set_register(reg_code, value)
    
    def read_memory(self, address: int, size: int = 8) -> int:
        """
        Read a value from memory.
        
        Args:
            address: Memory address
            size: Size in bytes (1 or 8)
            
        Returns:
            The memory value
        """
        if size == 1:
            return self.memory.read_byte(address)
        elif size == 8:
            return self.memory.read_quad(address)
        else:
            raise ValueError("Size must be 1 or 8")
    
    def write_memory(self, address: int, value: int, size: int = 8) -> None:
        """
        Write a value to memory.
        
        Args:
            address: Memory address
            value: Value to write
            size: Size in bytes (1 or 8)
        """
        if size == 1:
            self.memory.write_byte(address, value)
        elif size == 8:
            self.memory.write_quad(address, value)
        else:
            raise ValueError("Size must be 1 or 8")
    
    def dump_state(self) -> str:
        """
        Get a string representation of the current state.
        
        Returns:
            Formatted state string
        """
        return self.cpu.dump_state()
    
    def dump_memory(self, start: int = 0, length: int = 64) -> str:
        """
        Get a hexdump of memory contents.
        
        Args:
            start: Starting address
            length: Number of bytes
            
        Returns:
            Formatted memory dump
        """
        return self.memory.dump(start, length)


def run_program(source: str, trace: bool = False) -> Simulator:
    """
    Convenience function to run a Y86-64 program.
    
    Args:
        source: Y86-64 assembly source code
        trace: If True, print execution trace
        
    Returns:
        The Simulator instance after execution
    """
    sim = Simulator()
    sim.load_assembly(source)
    sim.run(trace)
    return sim
