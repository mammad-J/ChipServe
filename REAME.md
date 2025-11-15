# Python CHIP-8 Emulator 🕹️

A simple CHIP-8 emulator written in Python.  
It can load classic CHIP-8 ROMs.

---

## Features

- Load and run CHIP-8 ROMs.
- Supports all standard CHIP-8 instructions:
  - Flow control: JP, CALL, RET, SE, SNE
  - Math & logic: ADD, SUB, AND, OR, XOR, SHL, SHR
  - Graphics: DRW sprites with collision detection
  - Timers: Delay timer & sound timer (60Hz)
  - Memory & registers operations (Fx** opcodes)
- Display rendered in terminal using ASCII blocks (`█`).
- Debugging helper: opcode decoding and display.

---

## Requirements

- Python 3.x

---

## Usage

```bash
python main.py
