import os
from dotenv import load_dotenv
from PIL import Image
import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from metadata_saver import MetadataExtractor
import sys

class ImageSteganographer:
    def __init__(self):
        load_dotenv()
        self.password = os.getenv("PASSWORD")
        self.cover_image_name = os.getenv("COVER_IMAGE")
        self.stego_image_name = os.getenv("STEGO_IMAGE")
        self.decrypted_image_name = os.getenv("DECRYPTED_IMAGE")
        
        self.salt = get_random_bytes(16)
        self.key = PBKDF2(self.password, self.salt, dkLen=32, count=100_000)
        
    def encrypt_image(self, target_image_path):
        target = Image.open(target_image_path).convert('RGB')
        target_bytes = target.tobytes()
        
        # Save metadata
        metadata_extractor = MetadataExtractor()
        metadata_extractor.load_image(target_image_path)
        metadata = metadata_extractor.save_metadata_to_file()
        
        # Encryption
        iv = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        pad_len = 16 - (len(target_bytes) % 16)
        ciphertext = cipher.encrypt(target_bytes + bytes([pad_len]) * pad_len)
        
        return iv, ciphertext, target.size
        
    def generate_payload(self, iv, ciphertext):
        payload = self.salt + iv + ciphertext
        header = len(payload).to_bytes(4, 'big')
        full_payload = header + payload
        
        # Convert payload to bits
        payload_bits = [((byte >> i) & 1) for byte in full_payload for i in range(7, -1, -1)]
        return payload_bits, len(payload)
        
    def embed_payload(self, payload_bits):
        cover = Image.open(self.cover_image_name).convert('RGB')
        cover_arr = np.array(cover)
        flat = cover_arr.flatten()
        
        print(f"Cover image dimensions: {cover.width}x{cover.height}, channels: {len(cover.getbands())}")
        print(f"Total pixels: {cover.width * cover.height * len(cover.getbands())}")
        print(f"Payload size in bits: {len(payload_bits)}")
        
        if len(payload_bits) > flat.size:
            raise ValueError("Payload too large for cover image!")
            
        # LSB embedding
        for idx, bit in enumerate(payload_bits):
            flat[idx] = (flat[idx] & 0b11111110) | bit
            
        return flat, cover_arr.shape
        
    def save_stego_image(self, flat, shape):
        stego = Image.fromarray(flat.reshape(shape).astype('uint8'), 'RGB')
        stego.save(self.stego_image_name)
        
    def extract_payload(self):
        stego = Image.open(self.stego_image_name).convert('RGB')
        stego_arr = np.array(stego)
        flat = stego_arr.flatten()
        
        extracted_bits = [(pixel & 1) for pixel in flat]
        
        # Extract header (32 bits = 4 bytes)
        header_bits = extracted_bits[:32]
        header_bytes = bytearray(sum(bit << (7 - i % 8) for i, bit in enumerate(header_bits[j:j+8])) 
                            for j in range(0, 32, 8))
        payload_length = int.from_bytes(header_bytes, 'big')
        
        print(f"▶ payload length to extract: {payload_length} bytes")
        
        # Calculate total bits needed
        total_bits_needed = 32 + (payload_length * 8)
        if total_bits_needed > len(extracted_bits):
            raise ValueError(f"Not enough bits extracted from stego image.")
            
        # Extract payload bits
        payload_bits = extracted_bits[32:total_bits_needed]
        
        # Convert bits to bytes
        data = bytearray()
        for i in range(0, len(payload_bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(payload_bits):
                    byte |= (payload_bits[i + j] << (7 - j))
            data.append(byte)
            
        return data, payload_length
        
    def decrypt_image(self, data, width, height):
        salt = data[0:16]
        iv = data[16:32]
        ciphertext = data[32:]
        
        if len(iv) != 16:
            raise ValueError(f"Invalid IV length: {len(iv)} (must be 16)")
            
        # Decryption
        key = PBKDF2(self.password, salt, dkLen=32, count=100_000)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        
        # Remove padding
        pad_len = decrypted[-1]
        if pad_len > 0 and pad_len <= 16:
            decrypted = decrypted[:-pad_len]
            
        decrypted_image = Image.frombytes('RGB', (width, height), decrypted)
        decrypted_image.save(self.decrypted_image_name)
        
    def encode(self, target_image_path):
        iv, ciphertext, image_size = self.encrypt_image(target_image_path)
        payload_bits, payload_size = self.generate_payload(iv, ciphertext)
        flat, shape = self.embed_payload(payload_bits)
        self.save_stego_image(flat, shape)
        
        print(f"✅ Stego image generation completed (hidden bytes: {payload_size}B, total embedded bits: {len(payload_bits)})")
        return self.stego_image_name
        
    def decode(self):
        data, payload_length = self.extract_payload()
        self.decrypt_image(data, int(os.getenv("WIDTH", "0")), int(os.getenv("HEIGHT", "0")))
        print("✅ Image decryption completed")
        return self.decrypted_image_name

if __name__ == "__main__":
    steganographer = ImageSteganographer()
    
    # Example usage
    if len(sys.argv) > 1 and sys.argv[1] == "encode":
        target_image = input("Enter the path of the image to encrypt: ")
        steganographer.encode(target_image)
    elif len(sys.argv) > 1 and sys.argv[1] == "decode":
        steganographer.decode()
    else:
        print("Usage: python image_encrypter.py [encode|decode]")