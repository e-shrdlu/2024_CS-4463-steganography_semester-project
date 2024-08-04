# 2024_CS-4463-steganography_semester-project

## Overview
Pixel Value Differencing steganography project, using "A steganographic method for images by pixel-value differencing" by Da-Chun Wua and Wen-Hsiang Tsai (2002) as a guide

## Installation

```bash
python3 -m pip install -r requirements.txt
```
 - Currently the only requirement is Pillow 10.4 for reading / writing the image file

## Usage

embed data into image:
```bash
python3 PVD.py -c ./test-images/lena_gray.bmp -m ./test-messages/small-msg.txt -o PVD_encoded-image.bmp
```

extract data from image:
```bash
python3 PVD.py -e PVD_encoded-image.bmp
```

hide data using randomized key, vertical pixel pairings, and color components:
```bash
python3 PVD.py -c ./test-images/lena.bmp --rgb -m ./test-messages/small-msg.txt -o PVD_encoded-image.bmp --key "mysecretkey" --vertical
```
