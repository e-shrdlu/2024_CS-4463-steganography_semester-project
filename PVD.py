##################################
# Authors
##################################
# Nat Broyles
# Chelse Miles
# Aidan Kollar


import argparse
import os
import time
from PIL import Image

# global vars / settings #
##########################

# placeholders for now, will update generator function to do more later
pixel_pair_mode = "horizontal"
pixel_iteration_mode = "standard"


# bitmap class #
################

class bitmap:
    def __init__(self, filename):
        self.read_from_file(filename)

    def read_from_file(self, filename):
        self.image = Image.open(filename) # use PIL / Pillow library to read bitmap
        self.image.load()

    def write_to_file(self, filename):
        # TODO
        pass

# command line arguments #
##########################
def init_commandline_args():
    parser = argparse.ArgumentParser(prog="PVD", description="Pixel Value Differencing Steganography", epilog="wheeeeee")
    parser.add_argument("-c", "--cover-image", help="cover image to hide message in")
    parser.add_argument("-m", "--message-file", help="file containing secret message to hide")
    parser.add_argument("-o", "--output-image", help="where to store output image")
    parser.add_argument("-n", "--dry-run", help="don't hide data, just find capacity for given cover image", action="store_true")
    args = parser.parse_args()
    return args

def validate_args(args): # ensures user has given the correct options, and the needed files exist
    if not args.cover_image: # invalid bc no file given
        exit("error: no cover image specified")
    
    if not os.path.exists(args.cover_image): # invalid bc file given does not exist
        exit("error: cover image does not exist")

    if not args.dry_run:
        if not (args.output_image and args.message_file): # invalid becuase no files given
            exit("error: you must specify an output image and a message file")

        if not os.path.exists(args.message_file):
            exit("error: message file does not exist")

        if not os.path.exists(args.output_image):
            print("warning: output image", args.output_image, "already exists. You have 1s to cancel...")
            time.sleep(1)

# Image iterating generator thing #
###################################
# using pythons generators will allow us to write logic for iterating through pixel-pairs
# in different ways, allowing experimentation with different pairs (horizontal vs vertical)
# and different paths (left->right, top->bottom vs randomly determined with symmetric key, etc)
# stores pair as ((R,G,B), (R,G,B))
def pixel_pairs(img): # takes PIL Image object as parameter
    size_x, size_y = img.size
    if pixel_pair_mode == "horizontal":
        if pixel_iteration_mode == "standard":
            # left to right first, then top to bottom (like reading)
            # only do odd number x values, then the pair of pixels is x-1,y  x,y
            for y in range(size_y):
                for x in range(1,size_x,2): # start with 1, go by twos. gives us only odd numbers.
                    yield (img.getpixel((x-1, y)), img.getpixel((x, y)))
        else:
            print("ERROR: pixel iteration mode", pixel_iteration_mode, "not recognized")
    elif pixel_pair_mode == "vertical":
        print("TODO: implement vertical pixel pairs")
        #TODO
        exit()
    else:
        print("ERROR: pixel pair mode", pixel_pair_mode, "not recognized")
        exit()

def calculate_difference(pixel1, pixel2):
    # Calculate the difference between 2 RGB pixel values, will be used for determining range to hide in
    return (abs(pixel1[0] - pixel2[0]), abs(pixel1[1] - pixel2[1]), abs(pixel1[2] - pixel2[2]))



def main():
    args = init_commandline_args()
    validate_args(args) # will exit if invalid args
    cover_image = bitmap(args.cover_image)
    for pixel_pair in pixel_pairs(cover_image.image):
        print(pixel_pair)
        diff = calculate_difference(*pixel_pair)
        print(diff)

if __name__=="__main__":
    main()
