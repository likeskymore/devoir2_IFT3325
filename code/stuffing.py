import random 

FLAG = "01111110"

def bit_stuff(bits: str) -> str:
    stuffed = []
    count = 0
    for b in bits:
        stuffed.append(b)
        if b == "1":
            count += 1
        else:
            count = 0
        if count == 5:
            stuffed.append("0")
            count = 0
    return "".join(stuffed)


def bit_destuff(bits: str) -> str:
    destuffed = []
    count = 0
    i = 0
    while i < len(bits):
        b = bits[i]
        destuffed.append(b)
        if b == "1":
            count += 1
        else:
            count = 0
        if count == 5:
            i += 1  
            count = 0
        i += 1
    return "".join(destuffed)

def crc16(bits: str) -> str:
    poly = 0x1021
    crc = 0x0000  # initial value

    for bit in bits:
        # Shift in the next bit
        crc <<= 1
        if (int(bit) ^ ((crc >> 16) & 1)): 
            crc ^= poly
        crc &= 0xFFFF  

    return f"{crc:016b}"

# def test_stuffing():
#     def test1():
#         test_bits = "011111101111101111110111110"   

#         print("Original bits:     ", test_bits)

#         # Stuff
#         stuffed = bit_stuff(test_bits)
#         print("After stuffing:    ", stuffed)

#         # Destuff
#         destuffed = bit_destuff(stuffed)
#         print("After destuffing:  ", destuffed)

#         assert destuffed == test_bits, (
#             f"error destuffed != original.\n"
#             f"Original:  {test_bits}\n"
#             f"Destuffed: {destuffed}"
#         )

#         crc_original = crc16(test_bits)
#         crc_destuffed = crc16(destuffed)

#         print("CRC(original):     ", crc_original)
#         print("CRC(destuffed):    ", crc_destuffed)

#         assert crc_original == crc_destuffed, (
#             "crc mismatch"
#         )

#         print("test 1 passed: Everything works accordingly")
    
#     def test2():
#         test_bits = "011111101111101111110111110"   

#         print(f"\nOriginal bits:     ", test_bits)

#         # Stuff
#         stuffed = bit_stuff(test_bits)
#         print("After stuffing:    ", stuffed)

#         # Destuff
#         destuffed = bit_destuff(stuffed)
        
#         print("After destuffing:  ", destuffed)
  
#         i = random.randint(0, len(destuffed) - 1)
#         flipped_bit = '1' if destuffed[i] == '0' else '0'
#         destuffed = destuffed[:i] + flipped_bit + destuffed[i+1:]
        
#         print("After corruption:  ", destuffed, "(in destuffed seq)")


#         crc_original = crc16(test_bits)
#         crc_destuffed = crc16(destuffed)

#         print("CRC(original):     ", crc_original)
#         print("CRC(destuffed):    ", crc_destuffed)

#         assert crc_original != crc_destuffed, "CRC failed to detect error"
#         print("test 2 passed: CRC detected bit flip")
        
        
#     test1()
#     test2()
        

# test_stuffing()