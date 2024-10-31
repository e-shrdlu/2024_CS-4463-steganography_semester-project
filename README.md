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

## Examples
### Black and White embedded with `"A"`s
#### Original Image:
![black and white image with no data embedded](example-images/lena_bw_cover.png)

#### Image embedded with about 50,898 `"A"` characters:
![black and white image embedded with "A"s](example-images/lena_bw_embedded-with-As.png)

#### Difference between cover image and stego image (difference scaled up by 10):
![picture demonstrating difference between black and white cover image and one embedded with "A"s](example-images/lena_bw_emdedded-with-As-difference.png)
 - (ie, `this_img[1,1] = 10 * abs(cover_img[1,1] - stego_img[1,1])` )
 - you can see here that the entire capacity is maxed out

### Color embedded with Bee Movie script
#### Original Image:
![color image with no data embedded](example-images/lena_color_cover.png)

#### Image embedded with bee movie script:
![color image embded with the bee movie script](example-images/lena_color_embedded-with-bee-movie.png)

#### Difference between cover image and stego image (difference scaled up by 10):
![picture demonstrating difference between color cover image and one embedded with the bee movie script](example-images/lena_color_embedded-with-bee-movie-difference.png)
 - you can see here that only about 30% of the capacity is used
