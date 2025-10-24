import random
import time
import os

# === CONFIG ===
memory = [0] * 4096   # 4 KB memory
V = [0] * 16          # Registers V0–VF
I = 0                 # Index register
pc = 0x200            # Program counter starts at 0x200
stack = [0] * 16   # CHIP-8 has 16-level stack
stack_pointer = -1  # Means “no active calls yet”
delay_timer = 0
sound_timer = 0
# display = [0] * (64 * 32)
display = [[0] * 64 for _ in range(32)]
FONT_START = 0x50   

fontset = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80   # F
]


def load_ROM(ROM):
    """Loads ROM to memory starting at 0x200"""
    with open(ROM, "rb") as file:
        data = file.read()
    
    for i in range(len(data)):
        memory[0x200 + i] = data[i]

    print(f"[*] Loaded {len(data)} bytes into memory starting at 0x200.")


def load_fonts():
    """Load fontset into memory at FONT_START (conventional)"""
    for i, b in enumerate(fontset):
        memory[FONT_START + i] = b
    print("[*] Fonts loaded at 0x{0:03X}..0x{1:03X}".format(FONT_START, FONT_START + len(fontset) - 1))


def fetch_instruction():
    """Fetches and returns the next 2-byte opcode"""
    global pc
    high_byte = memory[pc]
    low_byte = memory[pc + 1]
    opcode = (high_byte << 8) | low_byte
    pc += 2
    return opcode


def decode_opcode(opcode):
    """Decode and print CHIP-8 opcode meaning (for debugging only)."""
    n1 = (opcode & 0xF000) >> 12
    n2 = (opcode & 0x0F00) >> 8
    n3 = (opcode & 0x00F0) >> 4
    n4 = opcode & 0x000F
    nnn = opcode & 0x0FFF
    kk = opcode & 0x00FF
    x = n2
    y = n3

    print(f"Opcode: {opcode:04X}", end=" → ")

    # --- System ---
    if opcode == 0x00E0:
        print("CLS (Clear the display)")
    elif opcode == 0x00EE:
        print("RET (Return from subroutine)")
    elif n1 == 0x0:
        print(f"SYS {nnn:03X} (Ignored; old jump to RCA 1802 program)")
    elif n1 == 0x0 and opcode not in (0x00E0, 0x00EE):
        print(f"SYS {nnn:03X} (Ignored on modern interpreters)")

    # --- Flow control ---
    elif n1 == 0x1:
        print(f"JP {nnn:03X} (Jump to address)")
    elif n1 == 0x2:
        print(f"CALL {nnn:03X} (Call subroutine at address)")
    elif n1 == 0x3:
        print(f"SE V{x:X}, {kk:02X} (Skip if V{x:X} == {kk:02X})")
    elif n1 == 0x4:
        print(f"SNE V{x:X}, {kk:02X} (Skip if V{x:X} != {kk:02X})")
    elif n1 == 0x5 and n4 == 0x0:
        print(f"SE V{x:X}, V{y:X} (Skip if V{x:X} == V{y:X})")
    elif n1 == 0x9 and n4 == 0x0:
        print(f"SNE V{x:X}, V{y:X} (Skip if V{x:X} != V{y:X})")
    elif n1 == 0xB:
        print(f"JP V0, {nnn:03X} (Jump to address {nnn:03X} + V0)")

    # --- Math / Logic ---
    elif n1 == 0x6:
        print(f"LD V{x:X}, {kk:02X} (Set V{x:X} = {kk:02X})")
    elif n1 == 0x7:
        print(f"ADD V{x:X}, {kk:02X} (Add {kk:02X} to V{x:X})")
    elif n1 == 0x8:
        if n4 == 0x0:
            print(f"LD V{x:X}, V{y:X} (Set V{x:X} = V{y:X})")
        elif n4 == 0x1:
            print(f"OR V{x:X}, V{y:X} (Set V{x:X} = V{x:X} | V{y:X})")
        elif n4 == 0x2:
            print(f"AND V{x:X}, V{y:X} (Set V{x:X} = V{x:X} & V{y:X})")
        elif n4 == 0x3:
            print(f"XOR V{x:X}, V{y:X} (Set V{x:X} = V{x:X} ^ V{y:X})")
        elif n4 == 0x4:
            print(f"ADD V{x:X}, V{y:X} (Set V{x:X} = V{x:X} + V{y:X}, set VF = carry)")
        elif n4 == 0x5:
            print(f"SUB V{x:X}, V{y:X} (Set V{x:X} = V{x:X} - V{y:X}, set VF = NOT borrow)")
        elif n4 == 0x6:
            print(f"SHR V{x:X} (Shift V{x:X} right by one, VF = LSB before shift)")
        elif n4 == 0x7:
            print(f"SUBN V{x:X}, V{y:X} (Set V{x:X} = V{y:X} - V{x:X}, set VF = NOT borrow)")
        elif n4 == 0xE:
            print(f"SHL V{x:X} (Shift V{x:X} left by one, VF = MSB before shift)")
        else:
            print("Unknown 8xy? opcode")

    # --- Random & Graphics ---
    elif n1 == 0xA:
        print(f"LD I, {nnn:03X} (Set I = {nnn:03X})")
    elif n1 == 0xC:
        print(f"RND V{x:X}, {kk:02X} (V{x:X} = random() & {kk:02X})")
    elif n1 == 0xD:
        print(f"DRW V{x:X}, V{y:X}, {n4:X} (Draw sprite at (V{x:X}, V{y:X}) height {n4})")

    # --- Key input ---
    elif n1 == 0xE:
        if kk == 0x9E:
            print(f"SKP V{x:X} (Skip next if key V{x:X} pressed)")
        elif kk == 0xA1:
            print(f"SKNP V{x:X} (Skip next if key V{x:X} NOT pressed)")
        else:
            print("Unknown EX?? opcode")

    # --- Timers / Memory / Fonts ---
    elif n1 == 0xF:
        if kk == 0x07:
            print(f"LD V{x:X}, DT (V{x:X} = delay timer)")
        elif kk == 0x0A:
            print(f"LD V{x:X}, K (Wait for key press, store in V{x:X})")
        elif kk == 0x15:
            print(f"LD DT, V{x:X} (Set delay timer = V{x:X})")
        elif kk == 0x18:
            print(f"LD ST, V{x:X} (Set sound timer = V{x:X})")
        elif kk == 0x1E:
            print(f"ADD I, V{x:X} (I += V{x:X})")
        elif kk == 0x29:
            print(f"LD F, V{x:X} (I = font for digit V{x:X})")
        elif kk == 0x33:
            print(f"LD B, V{x:X} (Store BCD of V{x:X} at [I], [I+1], [I+2])")
        elif kk == 0x55:
            print(f"LD [I], V0–V{x:X} (Store registers V0..V{x:X} in memory starting at I)")
        elif kk == 0x65:
            print(f"LD V0–V{x:X}, [I] (Read registers V0..V{x:X} from memory starting at I)")
        else:
            print("Unknown Fx?? opcode")
    else:
        print("Unknown opcode")


def execute_opcode(opcode):
    global pc, I, V, stack, stack_pointer, delay_timer, sound_timer, display

    n1 = (opcode & 0xF000) >> 12
    n2 = (opcode & 0x0F00) >> 8
    n3 = (opcode & 0x00F0) >> 4
    n4 = opcode & 0x000F
    nnn = opcode & 0x0FFF
    kk = opcode & 0x00FF
    x = n2
    y = n3


    if opcode == 0x00E0:  # CLS
        #  Clear the display.
        display = [[0]*64 for _ in range(32)]


    elif opcode ==  0x00EE: # RET
        #Return from a subroutine.
        pc = stack[stack_pointer]
        stack_pointer -= 1


    elif n1 == 0x1:  #  1nnn - JP addr
        #  Jump to location nnn.
        pc = nnn

    
    elif n1 == 0x2:  #  2nnn - CALL addr
        #  Call subroutine at nnn.
        stack_pointer += 1
        stack[stack_pointer] = pc
        pc = nnn
    
    elif n1 == 0x3:  # 3xkk - SE Vx, byte
        #  Skip next instruction if Vx = kk.
        if V[x] == kk:
            pc += 2

    elif n1 == 0x4: #  4xkk - SNE Vx, byte
        # Skip next instruction if Vx != kk.
        if V[x] != kk:
            pc += 2


    elif n1 == 0x5: # 5xy0 - SE Vx, Vy
        #  Skip next instruction if Vx = Vy.
        if V[x] == V[y]:
            pc += 2
    
    elif n1 == 0x6: #  6xkk - LD Vx, byte
        #  Set Vx = kk.
        V[x] = kk
    

    elif n1 == 0x7: # 7xkk - ADD Vx, byte
        # Set Vx = Vx + kk.
        V[x] = (V[x] + kk) & 0xFF

    elif n1 == 0x8: 
        if n4 == 0x0: # 8xy0 - LD Vx, Vy
            # Set Vx = Vy.
            V[x] = V[y]
        elif n4 == 0x1: # 8xy1 - OR Vx, Vy
            # Set Vx = Vx OR Vy.
            V[x] |= V[y]
        elif n4 == 0x2: # 8xy2 - AND Vx, Vy
            # Set Vx = Vx AND Vy.
            V[x] &= V[y]
        elif n4 == 0x3: # 8xy3 - XOR Vx, Vy
            # Set Vx = Vx XOR Vy.
            V[x] ^= V[y]
        elif n4 == 0x4:  # 8xy4 - ADD Vx, Vy (with carry)
            # Set Vx = Vx + Vy, set VF = carry.
            result = V[x] + V[y]
            V[0xF] = 1 if result > 0xFF else 0
            V[x] = result & 0xFF
        elif n4 == 0x5:  # 8xy5 - SUB Vx, Vy (with borrow)
            # Set Vx = Vx - Vy, set VF = NOT borrow.
            V[0xF] = 1 if V[x] > V[y] else 0
            V[x] = (V[x] - V[y]) & 0xFF
        elif n4 == 0x6: # 8xy6 - SHR Vx {, Vy}
            # Set Vx = Vx SHR 1.
            V[0xF] = V[x] & 0x1
            V[x] >>= 1
        elif n4 == 0x7:  # 8xy7 - SUBN Vx, Vy
            #  Set Vx = Vy - Vx, set VF = NOT borrow.
            V[0xF] = 1 if V[y] > V[x] else 0
            V[x] = (V[y] - V[x]) & 0xFF
        elif n4 == 0x8: # 8xyE - SHL Vx {, Vy}
            # Set Vx = Vx SHL 1.
            V[0xF] = (V[x] >> 7) & 0x1
            V[x] = (V[x] << 1) & 0xFF 
        elif n4 == 0xE: # SHL
            V[0xF] = (V[y] >> 7) & 1
            V[x] = (V[y] << 1) & 0xFF


    elif n1 == 0x9 and n4 == 0x0: # 9xy0 - SNE Vx, Vy
        # Skip next instruction if Vx != Vy.
        if V[x] != V[y]:
            pc += 2
    

    elif n1 == 0xA:
        I = nnn


    elif n1 == 0xB: # Bnnn - JP V0, addr
        # Jump to location nnn + V0.
        pc = nnn + V[0]
    

    elif n1 == 0xC: # Cxkk - RND Vx, byte
        rand = random.randint(0, 255)
        V[n2] = rand & kk
    
        
    elif n1 == 0xD: # Dxyn - DRW Vx, Vy, nibble
        # Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
        # VF = 1 if any pixels are flipped from set to unset (collision)

        x_coord = V[x] % 64
        y_coord = V[y] % 32
        height = n4
        V[0xF] = 0

        for row in range(height):
            if I + row >= len(memory):  # safety check
                break

            sprite_byte = memory[I + row]

            for col in range(8):
                if sprite_byte & (0x80 >> col):
                    pixel_x = (x_coord + col) % 64
                    pixel_y = (y_coord + row) % 32

                    if display[pixel_y][pixel_x] == 1:
                        V[0xF] = 1  # collision

                    # XOR pixel toggle
                    display[pixel_y][pixel_x] ^= 1

    
    elif n1 == 0xE:
        if kk == 0x9E: # Ex9E - SKP Vx
            # Skip next instruction if key with the value of Vx is pressed.
            return
        elif kk == 0xA1: # ExA1 - SKNP Vx
            # Skip next instruction if key with the value of Vx is not pressed.
            return

    
    elif n1 == 0xF:
        if kk == 0x07: # Fx07 - LD Vx, DT    
            # Set Vx = delay timer value.
            V[x] = delay_timer
        
        elif kk == 0x0A: # Fx0A - LD Vx, K
            # Wait for a key press, store the value of the key in Vx.
            return

        elif kk == 0x15: # Fx15 - LD DT, Vx
            # Set delay timer = Vx.
            delay_timer = V[x]
        
        elif kk == 0x18: # Fx18 - LD ST, Vx
            # Set sound timer = Vx.
            sound_timer = V[x]
        
        elif kk == 0x1E: # Fx1E - ADD I, Vx
            # Set I = I + Vx.
            I = I + V[x]
        
        elif kk == 0x29: # Fx29 - LD F, Vx
            # Set I = location of sprite for digit Vx.
            digit = V[x] & 0xF
            I = FONT_START + (digit * 5)
        
        elif kk == 0x33: # Fx33 - LD B, Vx
            # Store BCD representation of Vx in memory locations I, I+1, and I+2.
            value = V[x]
            memory[I]     =  value // 100          # Hundreds digit
            memory[I + 1] = (value // 10) % 10    # Tens digit
            memory[I + 2] =  value % 10

        elif kk == 0x55: # Fx55 - LD [I], Vx
            # Store registers V0 through Vx in memory starting at location I.
            for i in range(x + 1):
                memory[I+i] = V[i]   

        elif kk == 0x65: # Fx65 - LD Vx, [I]
            # Read registers V0 through Vx from memory starting at location I.
            for i in range(x + 1):
                V[i] = memory[I + i]

def DRW(Vx, Vy, n, memory, I, display):
    VF = 0  # Collision flag
    for row in range(n):
        if I + row >= len(memory):
            break
        sprite_byte = memory[I + row]
        for col in range(8):
            pixel = (sprite_byte >> (7 - col)) & 1
            x = (Vx + col) % 64
            y = (Vy + row) % 32
            if pixel:
                if display[y][x] == 1:
                    VF = 1
                display[y][x] ^= 1
    return VF


def print_display():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear terminal
    for row in display:
        print("".join("█" if pixel else " " for pixel in row))
    print("-" * 64)



# === Main Loop ===
load_fonts()
load_ROM("snake.ch8")

while True:
    try:
        # input()  # wait for Enter to fetch next
        opcode = fetch_instruction()
        decode_opcode(opcode) #debug
        execute_opcode(opcode)
        print_display()
        time.sleep(0.01)
        
    except KeyboardInterrupt:
        print("\nExiting.")
        break
