"""
Y86-64 CPU Module

Implements the CPU state and execution logic for the Y86-64 simulator.
"""

from typing import Tuple, Optional
from .constants import (
    RRAX, RRCX, RRDX, RRBX, RRSP, RRBP, RRSI, RRDI,
    RR8, RR9, RR10, RR11, RR12, RR13, RR14, RNONE,
    REGISTER_NAMES, STATUS_NAMES,
    STAT_AOK, STAT_HLT, STAT_ADR, STAT_INS,
    IHALT, INOP, IRRMOVQ, IIRMOVQ, IRMMOVQ, IMRMOVQ,
    IOPQ, IJXX, ICALL, IRET, IPUSHQ, IPOPQ,
    ALUADD, ALUSUB, ALUAND, ALUXOR,
    C_YES, C_LE, C_L, C_E, C_NE, C_GE, C_G,
    ALU_NAMES, CONDITION_NAMES
)
from .memory import Memory


class CPU:
    """
    Simulates the CPU of a Y86-64 processor.
    
    The CPU has:
    - 15 64-bit registers (%rax through %r14)
    - A program counter (PC)
    - Condition codes (ZF, SF, OF)
    - A status code indicating the processor state
    """
    
    def __init__(self, memory: Memory):
        """
        Initialize the CPU with a reference to memory.
        
        Args:
            memory: The Memory object to use for memory operations
        """
        self.memory = memory
        self.reset()
    
    def reset(self) -> None:
        """Reset all CPU state to initial values."""
        # 15 64-bit registers (index 0-14)
        self.registers = [0] * 15
        
        # Program counter
        self.pc = 0
        
        # Condition codes
        self.zf = True   # Zero flag
        self.sf = False  # Sign flag
        self.of = False  # Overflow flag
        
        # Processor status
        self.status = STAT_AOK
        
        # Cycle counter
        self.cycle_count = 0
        
        # Instruction counter
        self.instruction_count = 0
    
    def get_register(self, reg: int) -> int:
        """
        Get the value of a register.
        
        Args:
            reg: Register number (0-14) or RNONE (15)
            
        Returns:
            The register value, or 0 if reg is RNONE
        """
        if reg == RNONE:
            return 0
        if 0 <= reg < 15:
            return self.registers[reg]
        raise ValueError(f"Invalid register: {reg}")
    
    def set_register(self, reg: int, value: int) -> None:
        """
        Set the value of a register.
        
        Args:
            reg: Register number (0-14), ignored if RNONE
            value: The value to set
        """
        if reg == RNONE:
            return
        if 0 <= reg < 15:
            # Ensure 64-bit signed value
            if value >= (1 << 63):
                value -= (1 << 64)
            elif value < -(1 << 63):
                value += (1 << 64)
            self.registers[reg] = value
        else:
            raise ValueError(f"Invalid register: {reg}")
    
    def update_condition_codes(self, result: int, a: int = 0, b: int = 0, op: int = ALUADD) -> None:
        """
        Update condition codes based on an ALU operation result.
        
        Args:
            result: The result of the operation
            a: First operand
            b: Second operand
            op: ALU operation type
        """
        # Ensure 64-bit representation
        result_64 = result & 0xFFFFFFFFFFFFFFFF
        if result_64 >= (1 << 63):
            result_64 -= (1 << 64)
        
        # Zero flag
        self.zf = (result_64 == 0)
        
        # Sign flag (based on most significant bit)
        self.sf = (result_64 < 0)
        
        # Overflow flag (depends on operation)
        if op == ALUADD:
            # Overflow if signs of operands are same but different from result
            self.of = ((a > 0 and b > 0 and result_64 < 0) or
                       (a < 0 and b < 0 and result_64 > 0))
        elif op == ALUSUB:
            # For subtraction: a - b = result
            # Overflow if sign of a differs from sign of b, and sign of result differs from sign of a
            self.of = ((a > 0 and b < 0 and result_64 < 0) or
                       (a < 0 and b > 0 and result_64 > 0))
        else:
            # AND and XOR don't cause overflow
            self.of = False
    
    def check_condition(self, ifun: int) -> bool:
        """
        Check if a condition is satisfied based on condition codes.
        
        Args:
            ifun: The condition function code
            
        Returns:
            True if the condition is satisfied
        """
        if ifun == C_YES:
            return True
        elif ifun == C_LE:
            return (self.sf != self.of) or self.zf
        elif ifun == C_L:
            return self.sf != self.of
        elif ifun == C_E:
            return self.zf
        elif ifun == C_NE:
            return not self.zf
        elif ifun == C_GE:
            return self.sf == self.of
        elif ifun == C_G:
            return (self.sf == self.of) and not self.zf
        else:
            return False
    
    def fetch(self) -> Tuple[int, int, int, int, int]:
        """
        Fetch stage: Read instruction from memory.
        
        Returns:
            Tuple of (icode, ifun, rA, rB, valC)
        """
        if not self.memory.is_valid_address(self.pc):
            self.status = STAT_ADR
            return (IHALT, 0, RNONE, RNONE, 0)
        
        # Read first byte (icode:ifun)
        byte0 = self.memory.read_byte(self.pc)
        icode = (byte0 >> 4) & 0xF
        ifun = byte0 & 0xF
        
        rA = RNONE
        rB = RNONE
        valC = 0
        
        # Determine instruction length and read additional bytes
        if icode == IHALT or icode == INOP or icode == IRET:
            # 1-byte instructions
            pass
        elif icode in (IRRMOVQ, IOPQ, IPUSHQ, IPOPQ):
            # 2-byte instructions
            if not self.memory.is_valid_address(self.pc + 1):
                self.status = STAT_ADR
                return (IHALT, 0, RNONE, RNONE, 0)
            byte1 = self.memory.read_byte(self.pc + 1)
            rA = (byte1 >> 4) & 0xF
            rB = byte1 & 0xF
        elif icode in (IJXX, ICALL):
            # 9-byte instructions (1 + 8 for destination)
            if not self.memory.is_valid_address(self.pc + 8, 1):
                self.status = STAT_ADR
                return (IHALT, 0, RNONE, RNONE, 0)
            valC = self.memory.read_quad(self.pc + 1)
        elif icode in (IIRMOVQ, IRMMOVQ, IMRMOVQ):
            # 10-byte instructions (1 + 1 + 8)
            if not self.memory.is_valid_address(self.pc + 9, 1):
                self.status = STAT_ADR
                return (IHALT, 0, RNONE, RNONE, 0)
            byte1 = self.memory.read_byte(self.pc + 1)
            rA = (byte1 >> 4) & 0xF
            rB = byte1 & 0xF
            valC = self.memory.read_quad(self.pc + 2)
        else:
            # Invalid instruction
            self.status = STAT_INS
            return (IHALT, 0, RNONE, RNONE, 0)
        
        return (icode, ifun, rA, rB, valC)
    
    def get_instruction_length(self, icode: int) -> int:
        """
        Get the length of an instruction in bytes.
        
        Args:
            icode: The instruction code
            
        Returns:
            The instruction length in bytes
        """
        if icode in (IHALT, INOP, IRET):
            return 1
        elif icode in (IRRMOVQ, IOPQ, IPUSHQ, IPOPQ):
            return 2
        elif icode in (IJXX, ICALL):
            return 9
        elif icode in (IIRMOVQ, IRMMOVQ, IMRMOVQ):
            return 10
        else:
            return 1  # Invalid instruction
    
    def execute_instruction(self) -> bool:
        """
        Execute a single instruction.
        
        Returns:
            True if execution should continue, False if halted
        """
        if self.status != STAT_AOK:
            return False
        
        # Fetch
        icode, ifun, rA, rB, valC = self.fetch()
        
        if self.status != STAT_AOK:
            return False
        
        # Calculate next PC
        next_pc = self.pc + self.get_instruction_length(icode)
        
        # Decode and Execute
        valA = self.get_register(rA)
        valB = self.get_register(rB)
        
        if icode == IHALT:
            self.status = STAT_HLT
            return False
        
        elif icode == INOP:
            pass
        
        elif icode == IRRMOVQ:
            # Conditional move
            if self.check_condition(ifun):
                self.set_register(rB, valA)
        
        elif icode == IIRMOVQ:
            self.set_register(rB, valC)
        
        elif icode == IRMMOVQ:
            # Memory write: M[rB + D] = rA
            address = valB + valC
            if not self.memory.is_valid_address(address, 8):
                self.status = STAT_ADR
                return False
            self.memory.write_quad(address, valA)
        
        elif icode == IMRMOVQ:
            # Memory read: rA = M[rB + D]
            address = valB + valC
            if not self.memory.is_valid_address(address, 8):
                self.status = STAT_ADR
                return False
            value = self.memory.read_quad(address)
            self.set_register(rA, value)
        
        elif icode == IOPQ:
            # ALU operation
            if ifun == ALUADD:
                result = valB + valA
            elif ifun == ALUSUB:
                result = valB - valA
            elif ifun == ALUAND:
                result = valB & valA
            elif ifun == ALUXOR:
                result = valB ^ valA
            else:
                self.status = STAT_INS
                return False
            
            # Mask to 64 bits and handle sign
            result = result & 0xFFFFFFFFFFFFFFFF
            if result >= (1 << 63):
                result -= (1 << 64)
            
            self.update_condition_codes(result, valA, valB, ifun)
            self.set_register(rB, result)
        
        elif icode == IJXX:
            # Conditional jump
            if self.check_condition(ifun):
                next_pc = valC
        
        elif icode == ICALL:
            # Push return address and jump
            sp = self.get_register(RRSP) - 8
            if not self.memory.is_valid_address(sp, 8):
                self.status = STAT_ADR
                return False
            self.memory.write_quad(sp, next_pc)
            self.set_register(RRSP, sp)
            next_pc = valC
        
        elif icode == IRET:
            # Pop return address and jump
            sp = self.get_register(RRSP)
            if not self.memory.is_valid_address(sp, 8):
                self.status = STAT_ADR
                return False
            next_pc = self.memory.read_quad(sp)
            self.set_register(RRSP, sp + 8)
        
        elif icode == IPUSHQ:
            # Push register onto stack
            sp = self.get_register(RRSP) - 8
            if not self.memory.is_valid_address(sp, 8):
                self.status = STAT_ADR
                return False
            self.memory.write_quad(sp, valA)
            self.set_register(RRSP, sp)
        
        elif icode == IPOPQ:
            # Pop value from stack into register
            sp = self.get_register(RRSP)
            if not self.memory.is_valid_address(sp, 8):
                self.status = STAT_ADR
                return False
            value = self.memory.read_quad(sp)
            self.set_register(RRSP, sp + 8)
            self.set_register(rA, value)
        
        else:
            self.status = STAT_INS
            return False
        
        # Update PC
        self.pc = next_pc
        self.instruction_count += 1
        self.cycle_count += 1
        
        return True
    
    def dump_registers(self) -> str:
        """
        Dump register contents as a formatted string.
        
        Returns:
            A string showing all register values
        """
        lines = []
        lines.append("Registers:")
        for i in range(0, 15, 3):
            row = []
            for j in range(3):
                if i + j < 15:
                    reg = i + j
                    name = REGISTER_NAMES[reg]
                    value = self.registers[reg]
                    row.append(f"{name:>5}: 0x{value & 0xFFFFFFFFFFFFFFFF:016x}")
            lines.append("  " + "  ".join(row))
        return "\n".join(lines)
    
    def dump_state(self) -> str:
        """
        Dump complete CPU state.
        
        Returns:
            A string showing PC, status, condition codes, and registers
        """
        lines = []
        lines.append(f"PC: 0x{self.pc:016x}")
        lines.append(f"Status: {STATUS_NAMES.get(self.status, 'UNKNOWN')}")
        lines.append(f"Condition Codes: ZF={int(self.zf)} SF={int(self.sf)} OF={int(self.of)}")
        lines.append(f"Instructions: {self.instruction_count}  Cycles: {self.cycle_count}")
        lines.append(self.dump_registers())
        return "\n".join(lines)
