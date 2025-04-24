## Installation 

1. Clone this repository
```
git clone https://github.com/kninami/def-ipv.git
```

2. Create and activate a virtual environment (in root folder)
```
python -m venv venv
source venv/bin/activate
```

3. Install dependencies using pip
```
pip install -r requirements.txt
```

4. Generate and edit .env file
```
TARGET_IMAGE= 'target_image_file_name'
COVER_IMAGE= 'cover_image_file_name'
STEGO_IMAGE= 'stego_image_file_name'
DECRYPTED_IMAGE= 'decrypted_image_file_name'
```

5. Image file should be in the same folder as the program

5. Run the program
```
python image_encrypter.py
```

6. Decrypt the image
```
python image_decrypter.py
```