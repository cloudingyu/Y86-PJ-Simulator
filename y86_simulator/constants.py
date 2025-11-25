"""
Y86-64 Constants and Definitions

Defines instruction codes, register names, condition codes, and status codes
for the Y86-64 instruction set architecture.
"""

# Instruction codes (icode)
IHALT = 0x0    # halt
INOP = 0x1     # nop
IRRMOVQ = 0x2  # rrmovq (and cmovXX)
IIRMOVQ = 0x3  # irmovq
IRMMOVQ = 0x4  # rmmovq
IMRMOVQ = 0x5  # mrmovq
IOPQ = 0x6     # OPq (addq, subq, andq, xorq)
IJXX = 0x7     # jXX (jmp, jle, jl, je, jne, jge, jg)
ICALL = 0x8    # call
IRET = 0x9     # ret
IPUSHQ = 0xA   # pushq
IPOPQ = 0xB    # popq

# Function codes (ifun) for OPq instructions
ALUADD = 0x0   # addq
ALUSUB = 0x1   # subq
ALUAND = 0x2   # andq
ALUXOR = 0x3   # xorq

# Function codes for conditional moves and jumps
C_YES = 0x0    # unconditional
C_LE = 0x1     # less or equal
C_L = 0x2      # less
C_E = 0x3      # equal
C_NE = 0x4     # not equal
C_GE = 0x5     # greater or equal
C_G = 0x6      # greater

# Register encoding
RRAX = 0x0
RRCX = 0x1
RRDX = 0x2
RRBX = 0x3
RRSP = 0x4
RRBP = 0x5
RRSI = 0x6
RRDI = 0x7
RR8 = 0x8
RR9 = 0x9
RR10 = 0xA
RR11 = 0xB
RR12 = 0xC
RR13 = 0xD
RR14 = 0xE
RNONE = 0xF  # No register

# Register names for display
REGISTER_NAMES = {
    RRAX: "%rax",
    RRCX: "%rcx",
    RRDX: "%rdx",
    RRBX: "%rbx",
    RRSP: "%rsp",
    RRBP: "%rbp",
    RRSI: "%rsi",
    RRDI: "%rdi",
    RR8: "%r8",
    RR9: "%r9",
    RR10: "%r10",
    RR11: "%r11",
    RR12: "%r12",
    RR13: "%r13",
    RR14: "%r14",
    RNONE: "NONE",
}

# Status codes
STAT_AOK = 1   # Normal operation
STAT_HLT = 2   # Halt instruction encountered
STAT_ADR = 3   # Invalid address
STAT_INS = 4   # Invalid instruction

# Status names for display
STATUS_NAMES = {
    STAT_AOK: "AOK",
    STAT_HLT: "HLT",
    STAT_ADR: "ADR",
    STAT_INS: "INS",
}

# Instruction names for display
INSTRUCTION_NAMES = {
    IHALT: "halt",
    INOP: "nop",
    IRRMOVQ: "rrmovq",
    IIRMOVQ: "irmovq",
    IRMMOVQ: "rmmovq",
    IMRMOVQ: "mrmovq",
    IOPQ: "OPq",
    IJXX: "jXX",
    ICALL: "call",
    IRET: "ret",
    IPUSHQ: "pushq",
    IPOPQ: "popq",
}

# ALU operation names
ALU_NAMES = {
    ALUADD: "addq",
    ALUSUB: "subq",
    ALUAND: "andq",
    ALUXOR: "xorq",
}

# Condition names
CONDITION_NAMES = {
    C_YES: "",      # unconditional (no suffix)
    C_LE: "le",
    C_L: "l",
    C_E: "e",
    C_NE: "ne",
    C_GE: "ge",
    C_G: "g",
}

# Memory size (default: 4KB)
DEFAULT_MEM_SIZE = 4096
