"""
Y86-64 Processor Simulator

A software simulation of the Y86-64 instruction set architecture
based on the textbook "Computer Systems: A Programmer's Perspective".
"""

from .cpu import CPU
from .memory import Memory
from .assembler import Assembler
from .simulator import Simulator

__version__ = "1.0.0"
__all__ = ["CPU", "Memory", "Assembler", "Simulator"]
