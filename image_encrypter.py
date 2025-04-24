import os
from dotenv import load_dotenv
from PIL import Image
import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from metadata_saver import MetadataExtractor

load_dotenv()
password = os.getenv("PASSWORD")
target_image_name = os.getenv("TARGET_IMAGE")
cover_image_name = os.getenv("COVER_IMAGE")
stego_image_name = os.getenv("STEGO_IMAGE")
decrypted_image_name = os.getenv("DECRYPTED_IMAGE")

salt = get_random_bytes(16)
key = PBKDF2(password, salt, dkLen=32, count=100_000)

target = Image.open(target_image_name).convert('RGB')
target_bytes = target.tobytes()

metadata_extractor = MetadataExtractor()
metadata_extractor.load_image(target_image_name)
metadata = metadata_extractor.save_metadata_to_file()

# encryption
iv = get_random_bytes(16)
cipher = AES.new(key, AES.MODE_CBC, iv)
pad_len = 16 - (len(target_bytes) % 16)
ciphertext = cipher.encrypt(target_bytes + bytes([pad_len]) * pad_len)

# payload generation (salt + iv + ciphertext)
payload = salt + iv + ciphertext
header = len(payload).to_bytes(4, 'big')
full_payload = header + payload

# payload to bits
payload_bits = [((byte >> i) & 1) for byte in full_payload for i in range(7, -1, -1)]

# cover image embedding
cover = Image.open(cover_image_name).convert('RGB')

cover_arr = np.array(cover)
flat = cover_arr.flatten()

if len(payload_bits) > flat.size:
    raise ValueError("Payload too large for cover image!")

# cover image LSB embedding
for idx, bit in enumerate(payload_bits):
    flat[idx] = (flat[idx] & 0b11111110) | bit

# stego image saving
stego = Image.fromarray(flat.reshape(cover_arr.shape).astype('uint8'), 'RGB')
stego.save(stego_image_name)

print(f"✅ Stego image generation completed (hidden bytes: {len(payload)}B, total embedded bits: {len(payload_bits)})")