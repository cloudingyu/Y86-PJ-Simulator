"""
Y86-64 Assembler Module

Implements an assembler for Y86-64 assembly language.
"""

import re
from typing import Dict, List, Tuple, Optional
from .constants import (
    IHALT, INOP, IRRMOVQ, IIRMOVQ, IRMMOVQ, IMRMOVQ,
    IOPQ, IJXX, ICALL, IRET, IPUSHQ, IPOPQ,
    ALUADD, ALUSUB, ALUAND, ALUXOR,
    C_YES, C_LE, C_L, C_E, C_NE, C_GE, C_G,
    RRAX, RRCX, RRDX, RRBX, RRSP, RRBP, RRSI, RRDI,
    RR8, RR9, RR10, RR11, RR12, RR13, RR14, RNONE
)


class AssemblyError(Exception):
    """Exception raised for assembly errors."""
    
    def __init__(self, message: str, line_num: int = 0, line: str = ""):
        self.message = message
        self.line_num = line_num
        self.line = line
        super().__init__(f"Line {line_num}: {message}\n  {line}")


class Assembler:
    """
    Assembler for Y86-64 assembly language.
    
    Supports the full Y86-64 instruction set including:
    - halt, nop
    - rrmovq, cmovXX (conditional moves)
    - irmovq
    - rmmovq, mrmovq
    - OPq (addq, subq, andq, xorq)
    - jXX (jmp, jle, jl, je, jne, jge, jg)
    - call, ret
    - pushq, popq
    
    Directives:
    - .pos addr: Set current address
    - .align n: Align to n-byte boundary
    - .quad val: 8-byte value
    """
    
    # Register name to code mapping
    REGISTERS = {
        "%rax": RRAX, "%rcx": RRCX, "%rdx": RRDX, "%rbx": RRBX,
        "%rsp": RRSP, "%rbp": RRBP, "%rsi": RRSI, "%rdi": RRDI,
        "%r8": RR8, "%r9": RR9, "%r10": RR10, "%r11": RR11,
        "%r12": RR12, "%r13": RR13, "%r14": RR14,
    }
    
    # Instruction patterns
    INSTRUCTIONS = {
        "halt": (IHALT, 0),
        "nop": (INOP, 0),
        "ret": (IRET, 0),
        "rrmovq": (IRRMOVQ, C_YES),
        "cmovle": (IRRMOVQ, C_LE),
        "cmovl": (IRRMOVQ, C_L),
        "cmove": (IRRMOVQ, C_E),
        "cmovne": (IRRMOVQ, C_NE),
        "cmovge": (IRRMOVQ, C_GE),
        "cmovg": (IRRMOVQ, C_G),
        "irmovq": (IIRMOVQ, 0),
        "rmmovq": (IRMMOVQ, 0),
        "mrmovq": (IMRMOVQ, 0),
        "addq": (IOPQ, ALUADD),
        "subq": (IOPQ, ALUSUB),
        "andq": (IOPQ, ALUAND),
        "xorq": (IOPQ, ALUXOR),
        "jmp": (IJXX, C_YES),
        "jle": (IJXX, C_LE),
        "jl": (IJXX, C_L),
        "je": (IJXX, C_E),
        "jne": (IJXX, C_NE),
        "jge": (IJXX, C_GE),
        "jg": (IJXX, C_G),
        "call": (ICALL, 0),
        "pushq": (IPUSHQ, 0),
        "popq": (IPOPQ, 0),
    }
    
    def __init__(self):
        """Initialize the assembler."""
        self.labels: Dict[str, int] = {}
        self.output: bytearray = bytearray()
        self.address = 0
        self.pending_labels: List[Tuple[int, str, int]] = []  # (output_pos, label, line_num)
    
    def reset(self) -> None:
        """Reset assembler state."""
        self.labels = {}
        self.output = bytearray()
        self.address = 0
        self.pending_labels = []
    
    def parse_register(self, reg_str: str) -> int:
        """
        Parse a register name.
        
        Args:
            reg_str: Register name string (e.g., "%rax")
            
        Returns:
            Register code
            
        Raises:
            AssemblyError: If register name is invalid
        """
        reg_str = reg_str.strip().lower()
        if reg_str in self.REGISTERS:
            return self.REGISTERS[reg_str]
        raise AssemblyError(f"Invalid register: {reg_str}")
    
    def parse_immediate(self, imm_str: str) -> int:
        """
        Parse an immediate value.
        
        Args:
            imm_str: Immediate value string (e.g., "$10" or "$0x10")
            
        Returns:
            Integer value
        """
        imm_str = imm_str.strip()
        if imm_str.startswith("$"):
            imm_str = imm_str[1:]
        
        if imm_str.startswith("0x") or imm_str.startswith("0X"):
            return int(imm_str, 16)
        elif imm_str.startswith("-0x") or imm_str.startswith("-0X"):
            return -int(imm_str[1:], 16)
        else:
            return int(imm_str)
    
    def parse_memory(self, mem_str: str) -> Tuple[int, int]:
        """
        Parse a memory operand.
        
        Args:
            mem_str: Memory operand string (e.g., "8(%rsp)" or "(%rbp)")
            
        Returns:
            Tuple of (displacement, register_code)
        """
        mem_str = mem_str.strip()
        
        # Pattern: displacement(register) or (register)
        match = re.match(r'^(-?\d+|-?0x[0-9a-fA-F]+)?\((%r\w+)\)$', mem_str)
        if not match:
            raise AssemblyError(f"Invalid memory operand: {mem_str}")
        
        disp_str = match.group(1)
        reg_str = match.group(2)
        
        disp = 0 if disp_str is None else self.parse_immediate(disp_str)
        reg = self.parse_register(reg_str)
        
        return (disp, reg)
    
    def encode_quad(self, value: int) -> bytes:
        """
        Encode a 64-bit value in little-endian format.
        
        Args:
            value: The value to encode
            
        Returns:
            8-byte little-endian representation
        """
        if value < 0:
            value += (1 << 64)
        return bytes([(value >> (i * 8)) & 0xFF for i in range(8)])
    
    def emit_byte(self, byte: int) -> None:
        """Emit a single byte to output."""
        # Extend output if necessary
        while len(self.output) < self.address:
            self.output.append(0)
        
        if len(self.output) == self.address:
            self.output.append(byte & 0xFF)
        else:
            self.output[self.address] = byte & 0xFF
        self.address += 1
    
    def emit_quad(self, value: int) -> None:
        """Emit an 8-byte value to output."""
        for byte in self.encode_quad(value):
            self.emit_byte(byte)
    
    def emit_label_reference(self, label: str, line_num: int) -> None:
        """
        Emit a label reference (to be resolved later).
        
        Args:
            label: The label name
            line_num: Line number for error reporting
        """
        self.pending_labels.append((self.address, label, line_num))
        self.emit_quad(0)  # Placeholder
    
    def assemble_line(self, line: str, line_num: int) -> None:
        """
        Assemble a single line of code.
        
        Args:
            line: The line of assembly code
            line_num: Line number for error reporting
        """
        # Remove comments
        if "#" in line:
            line = line[:line.index("#")]
        if "//" in line:
            line = line[:line.index("//")]
        
        line = line.strip()
        if not line:
            return
        
        # Check for labels
        if ":" in line:
            parts = line.split(":", 1)
            label = parts[0].strip()
            self.labels[label] = self.address
            line = parts[1].strip()
            if not line:
                return
        
        # Split into tokens
        tokens = line.split(None, 1)
        if not tokens:
            return
        
        mnemonic = tokens[0].lower()
        operands = tokens[1] if len(tokens) > 1 else ""
        
        # Handle directives
        if mnemonic == ".pos":
            self.address = self.parse_immediate(operands)
            return
        
        if mnemonic == ".align":
            alignment = self.parse_immediate(operands)
            while self.address % alignment != 0:
                self.emit_byte(0)
            return
        
        if mnemonic == ".quad":
            operands = operands.strip()
            if operands in self.labels:
                self.emit_quad(self.labels[operands])
            elif operands.isidentifier() or (operands and operands[0].isalpha()):
                # Forward reference
                self.emit_label_reference(operands, line_num)
            else:
                self.emit_quad(self.parse_immediate(operands))
            return
        
        # Handle instructions
        if mnemonic not in self.INSTRUCTIONS:
            raise AssemblyError(f"Unknown instruction: {mnemonic}", line_num, line)
        
        icode, ifun = self.INSTRUCTIONS[mnemonic]
        
        # Encode instruction
        self.emit_byte((icode << 4) | ifun)
        
        if icode == IHALT or icode == INOP or icode == IRET:
            # 1-byte instruction, already done
            pass
        
        elif icode == IRRMOVQ:
            # rrmovq rA, rB (including cmovXX)
            ops = [op.strip() for op in operands.split(",")]
            if len(ops) != 2:
                raise AssemblyError(f"Expected 2 operands for {mnemonic}", line_num, line)
            rA = self.parse_register(ops[0])
            rB = self.parse_register(ops[1])
            self.emit_byte((rA << 4) | rB)
        
        elif icode == IIRMOVQ:
            # irmovq V, rB
            ops = [op.strip() for op in operands.split(",")]
            if len(ops) != 2:
                raise AssemblyError(f"Expected 2 operands for {mnemonic}", line_num, line)
            rB = self.parse_register(ops[1])
            self.emit_byte((RNONE << 4) | rB)
            
            # Value can be immediate or label
            val_str = ops[0].strip()
            if val_str.startswith("$"):
                val_str = val_str[1:]
            
            if val_str in self.labels:
                self.emit_quad(self.labels[val_str])
            elif val_str.isidentifier() or (val_str and val_str[0].isalpha()):
                self.emit_label_reference(val_str, line_num)
            else:
                self.emit_quad(self.parse_immediate(ops[0]))
        
        elif icode == IRMMOVQ:
            # rmmovq rA, D(rB)
            ops = [op.strip() for op in operands.split(",")]
            if len(ops) != 2:
                raise AssemblyError(f"Expected 2 operands for {mnemonic}", line_num, line)
            rA = self.parse_register(ops[0])
            disp, rB = self.parse_memory(ops[1])
            self.emit_byte((rA << 4) | rB)
            self.emit_quad(disp)
        
        elif icode == IMRMOVQ:
            # mrmovq D(rB), rA
            ops = [op.strip() for op in operands.split(",")]
            if len(ops) != 2:
                raise AssemblyError(f"Expected 2 operands for {mnemonic}", line_num, line)
            disp, rB = self.parse_memory(ops[0])
            rA = self.parse_register(ops[1])
            self.emit_byte((rA << 4) | rB)
            self.emit_quad(disp)
        
        elif icode == IOPQ:
            # addq/subq/andq/xorq rA, rB
            ops = [op.strip() for op in operands.split(",")]
            if len(ops) != 2:
                raise AssemblyError(f"Expected 2 operands for {mnemonic}", line_num, line)
            rA = self.parse_register(ops[0])
            rB = self.parse_register(ops[1])
            self.emit_byte((rA << 4) | rB)
        
        elif icode == IJXX:
            # jXX Dest
            dest = operands.strip()
            if dest in self.labels:
                self.emit_quad(self.labels[dest])
            elif dest.isidentifier() or (dest and dest[0].isalpha()):
                self.emit_label_reference(dest, line_num)
            else:
                self.emit_quad(self.parse_immediate(dest))
        
        elif icode == ICALL:
            # call Dest
            dest = operands.strip()
            if dest in self.labels:
                self.emit_quad(self.labels[dest])
            elif dest.isidentifier() or (dest and dest[0].isalpha()):
                self.emit_label_reference(dest, line_num)
            else:
                self.emit_quad(self.parse_immediate(dest))
        
        elif icode == IPUSHQ:
            # pushq rA
            rA = self.parse_register(operands)
            self.emit_byte((rA << 4) | RNONE)
        
        elif icode == IPOPQ:
            # popq rA
            rA = self.parse_register(operands)
            self.emit_byte((rA << 4) | RNONE)
    
    def resolve_labels(self) -> None:
        """Resolve all pending label references."""
        for pos, label, line_num in self.pending_labels:
            if label not in self.labels:
                raise AssemblyError(f"Undefined label: {label}", line_num, "")
            
            address = self.labels[label]
            encoded = self.encode_quad(address)
            for i, byte in enumerate(encoded):
                self.output[pos + i] = byte
    
    def assemble(self, source: str) -> bytes:
        """
        Assemble Y86-64 source code.
        
        Args:
            source: Y86-64 assembly source code
            
        Returns:
            The assembled machine code as bytes
        """
        self.reset()
        
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            try:
                self.assemble_line(line, line_num)
            except AssemblyError:
                raise
            except Exception as e:
                raise AssemblyError(str(e), line_num, line)
        
        self.resolve_labels()
        
        return bytes(self.output)
    
    def assemble_file(self, filename: str) -> bytes:
        """
        Assemble a Y86-64 source file.
        
        Args:
            filename: Path to the source file
            
        Returns:
            The assembled machine code as bytes
        """
        with open(filename, "r") as f:
            source = f.read()
        return self.assemble(source)
    
    def get_labels(self) -> Dict[str, int]:
        """
        Get the symbol table (labels and their addresses).
        
        Returns:
            Dictionary mapping label names to addresses
        """
        return dict(self.labels)
