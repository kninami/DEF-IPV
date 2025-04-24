import os
from dotenv import load_dotenv
from PIL import Image
import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

load_dotenv()

password = os.getenv("PASSWORD") # from initial guide
width =  int(os.getenv("WIDTH", "0"))  # from _metadata.xml
height = int(os.getenv("HEIGHT", "0")) # from _metadata.xml

stego_image_name = os.getenv("STEGO_IMAGE")
decrypted_image_name = os.getenv("DECRYPTED_IMAGE")

stego = Image.open(stego_image_name).convert('RGB')
stego_arr = np.array(stego)
flat = stego_arr.flatten()

extracted_bits = [(pixel & 1) for pixel in flat]

# first 32 bits (4 bytes) are payload length header
header_bits = extracted_bits[:32]
header_bytes = bytearray(sum(bit << (7 - i % 8) for i, bit in enumerate(header_bits[j:j+8])) 
                        for j in range(0, 32, 8))
payload_length = int.from_bytes(header_bytes, 'big')

print(f"▶ payload length to extract: {payload_length} bytes")

# calculate the number of bits needed (header 32 bits + payload bits)
total_bits_needed = 32 + (payload_length * 8)

if total_bits_needed > len(extracted_bits):
    raise ValueError(f"Not enough bits extracted from stego image.")

# extract payload bits (from header)
payload_bits = extracted_bits[32:total_bits_needed]

# convert bits to bytes
data = bytearray()
for i in range(0, len(payload_bits), 8):
    byte = 0
    for j in range(8):
        if i + j < len(payload_bits):
            byte |= (payload_bits[i + j] << (7 - j))
    data.append(byte)

salt = data[0:16]
iv = data[16:32]
ciphertext = data[32:]

if len(iv) != 16:
    raise ValueError(f"Invalid IV length: {len(iv)} (must be 16)")

# decryption
key = PBKDF2(password, salt, dkLen=32, count=100_000)
cipher = AES.new(key, AES.MODE_CBC, iv)
decrypted = cipher.decrypt(ciphertext)

# remove padding
pad_len = decrypted[-1]
if pad_len > 0 and pad_len <= 16:
    decrypted = decrypted[:-pad_len]

decrypted_image = Image.frombytes('RGB', (width, height), decrypted)
decrypted_image.save(decrypted_image_name)

print("✅ image decryption completed")