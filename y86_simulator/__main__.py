#!/usr/bin/env python3
"""
Y86-64 Simulator - Command Line Interface

Usage:
    python -m y86_simulator <filename.ys>
    python -m y86_simulator <filename.ys> --trace
"""

import sys
import argparse
from .simulator import Simulator
from .constants import STATUS_NAMES


def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Y86-64 Processor Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m y86_simulator program.ys
    python -m y86_simulator program.ys --trace
    python -m y86_simulator program.ys --mem-size 8192
        """
    )
    
    parser.add_argument(
        "filename",
        help="Y86-64 assembly source file (.ys)"
    )
    
    parser.add_argument(
        "--trace", "-t",
        action="store_true",
        help="Enable execution trace output"
    )
    
    parser.add_argument(
        "--mem-size", "-m",
        type=int,
        default=4096,
        help="Memory size in bytes (default: 4096)"
    )
    
    parser.add_argument(
        "--stack", "-s",
        type=lambda x: int(x, 0),
        default=None,
        help="Initial stack pointer value (default: end of memory)"
    )
    
    parser.add_argument(
        "--dump-memory", "-d",
        action="store_true",
        help="Dump memory contents after execution"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Y86-64 Simulator v1.0.0"
    )
    
    args = parser.parse_args()
    
    try:
        # Create simulator
        sim = Simulator(mem_size=args.mem_size)
        
        # Load program
        sim.load_assembly_file(args.filename, args.stack)
        
        print(f"Loaded: {args.filename}")
        print(f"Memory size: {args.mem_size} bytes")
        if args.stack:
            print(f"Stack pointer: 0x{args.stack:x}")
        print()
        
        # Run program
        status = sim.run(trace=args.trace)
        
        # Print final state
        print("\n" + "=" * 50)
        print("Execution completed")
        print(f"Status: {STATUS_NAMES.get(status, 'UNKNOWN')}")
        print(f"Instructions executed: {sim.cpu.instruction_count}")
        print()
        print(sim.dump_state())
        
        if args.dump_memory:
            print("\nMemory dump:")
            print(sim.dump_memory(0, 256))
        
        # Return appropriate exit code
        return 0 if status in (1, 2) else 1  # AOK or HLT = success
        
    except FileNotFoundError:
        print(f"Error: File not found: {args.filename}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
