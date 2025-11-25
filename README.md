# Y86-64 Processor Simulator

A software simulation of the Y86-64 instruction set architecture based on the textbook "Computer Systems: A Programmer's Perspective" by Bryant and O'Hallaron.

PJ of ICS-25Fal-FDU

## Overview

This project implements a complete Y86-64 processor simulator in Python, including:

- **CPU Simulation**: Full implementation of the Y86-64 CPU with 15 registers, condition codes, and status handling
- **Memory System**: Byte-addressable memory with little-endian 64-bit value support
- **Assembler**: Complete Y86-64 assembler supporting all instructions and directives
- **Command-line Interface**: Run Y86-64 programs from the terminal

## Y86-64 Instruction Set

### Supported Instructions

| Instruction | Description |
|-------------|-------------|
| `halt` | Stop execution |
| `nop` | No operation |
| `rrmovq rA, rB` | Register to register move |
| `irmovq V, rB` | Immediate to register move |
| `rmmovq rA, D(rB)` | Register to memory move |
| `mrmovq D(rB), rA` | Memory to register move |
| `addq rA, rB` | Add: rB = rB + rA |
| `subq rA, rB` | Subtract: rB = rB - rA |
| `andq rA, rB` | Bitwise AND: rB = rB & rA |
| `xorq rA, rB` | Bitwise XOR: rB = rB ^ rA |
| `jmp Dest` | Unconditional jump |
| `jle Dest` | Jump if less or equal |
| `jl Dest` | Jump if less |
| `je Dest` | Jump if equal |
| `jne Dest` | Jump if not equal |
| `jge Dest` | Jump if greater or equal |
| `jg Dest` | Jump if greater |
| `cmovle rA, rB` | Conditional move if less or equal |
| `cmovl rA, rB` | Conditional move if less |
| `cmove rA, rB` | Conditional move if equal |
| `cmovne rA, rB` | Conditional move if not equal |
| `cmovge rA, rB` | Conditional move if greater or equal |
| `cmovg rA, rB` | Conditional move if greater |
| `call Dest` | Push return address and jump |
| `ret` | Pop return address and jump |
| `pushq rA` | Push register onto stack |
| `popq rA` | Pop from stack to register |

### Registers

| Register | Code | Register | Code |
|----------|------|----------|------|
| %rax | 0 | %r8 | 8 |
| %rcx | 1 | %r9 | 9 |
| %rdx | 2 | %r10 | 10 |
| %rbx | 3 | %r11 | 11 |
| %rsp | 4 | %r12 | 12 |
| %rbp | 5 | %r13 | 13 |
| %rsi | 6 | %r14 | 14 |
| %rdi | 7 | | |

### Assembler Directives

| Directive | Description |
|-----------|-------------|
| `.pos addr` | Set current address |
| `.align n` | Align to n-byte boundary |
| `.quad val` | 8-byte value |

## Installation

```bash
# Clone the repository
git clone https://github.com/cloudingyu/Y86-PJ-Simulator.git
cd Y86-PJ-Simulator

# Install dependencies (optional, for development)
pip install pytest
```

## Usage

### Command Line

```bash
# Run a Y86-64 assembly file
python -m y86_simulator program.ys

# Run with execution trace
python -m y86_simulator program.ys --trace

# Specify memory size
python -m y86_simulator program.ys --mem-size 8192

# Dump memory after execution
python -m y86_simulator program.ys --dump-memory
```

### Python API

```python
from y86_simulator import Simulator

# Create simulator
sim = Simulator()

# Load and run a program
sim.load_assembly("""
    irmovq $100, %rax
    irmovq $200, %rbx
    addq %rax, %rbx
    halt
""")

sim.run()

# Check results
print(sim.get_register("rbx"))  # Outputs: 300
print(sim.dump_state())
```

## Example Programs

### Sum of Array

```assembly
# Sum an array of numbers
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
```

### Fibonacci

```assembly
# Calculate Fibonacci number
    irmovq $10, %rdi     # n = 10
    call fib
    halt

fib:
    pushq %rbx
    irmovq $2, %r8
    rrmovq %rdi, %rax
    subq %r8, %rdi
    jl fib_base
    
    pushq %rdi
    irmovq $1, %r9
    subq %r9, %rdi
    call fib
    rrmovq %rax, %rbx
    popq %rdi
    
    irmovq $2, %r9
    subq %r9, %rdi
    call fib
    addq %rbx, %rax
    
fib_base:
    popq %rbx
    ret
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_cpu.py -v

# Run with coverage
python -m pytest tests/ --cov=y86_simulator
```

## Project Structure

```
Y86-PJ-Simulator/
├── README.md
├── y86_simulator/
│   ├── __init__.py      # Package initialization
│   ├── __main__.py      # CLI entry point
│   ├── constants.py     # Instruction codes and constants
│   ├── memory.py        # Memory subsystem
│   ├── cpu.py           # CPU implementation
│   ├── assembler.py     # Y86-64 assembler
│   └── simulator.py     # Main simulator class
├── tests/
│   ├── __init__.py
│   ├── test_memory.py
│   ├── test_cpu.py
│   ├── test_assembler.py
│   └── test_simulator.py
└── examples/
    └── *.ys             # Example programs
```

## License

This project is for educational purposes as part of the ICS-25Fal-FDU course.

## References

- "Computer Systems: A Programmer's Perspective" by Bryant and O'Hallaron
- Y86-64 Instruction Set Architecture specification
