import argparse
import os
import time
from PIL import Image


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

def main():
    args = init_commandline_args()
    validate_args(args) # will exit if invalid args
    cover_image = bitmap(args.cover_image)

if __name__=="__main__":
    main()
