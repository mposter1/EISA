ADD R1, R1, 0x14
ADD R2, R2, 0xa
SUB R3, R1, R2
B 0x8
POP R1
POP R2
POP R3
END
PUSH R3
PUSH R2
PUSH R1
B 0x4
SUB R3, R3, R2