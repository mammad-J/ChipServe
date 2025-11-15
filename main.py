from CHIP8 import CHIP8
import time

CHIP8 = CHIP8("ROMs/Airplane.ch8")

while True:
    try:
        # input()  # wait for Enter to fetch next
        opcode = CHIP8.fetch_instruction()
        #CHIP8.decode_opcode(opcode) #debug
        CHIP8.execute_opcode(opcode)
        if CHIP8.Draw == True:
            CHIP8.print_display()
            CHIP8.Draw = False
        CHIP8.update_timers()
        time.sleep(1/700)

        
    except KeyboardInterrupt:
        print("\nExiting.")
        break