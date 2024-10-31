##################################
# Authors
##################################
# Nat Broyles
# Chelse Miles
# Aidan Kollar


import argparse
import os
import time
import math
from PIL import Image

# global vars / settings / default options #
############################################

# placeholders for now, will update generator function to do more later
pixel_pair_mode = "horizontal"
pixel_iteration_mode = "standard" # no other methods implemented yet
color_mode = "grayscale" # "grayscale" or "color" - defaults to "grayscale" but can be set in cmdline args
diff_ranges = [0,8,16,32,64,128,256] # hold indices of where ranges begin/end. First/Last elements should always be 0 and 256
num_bits_for_size=32 # this many bits will be used in the beginning of the image to determine how many bytes of data should be read
debug_mode = 0
quiet_mode = 0


# bitmap class #
################

class bitmap:
    def __init__(self, filename):
        self.read_from_file(filename)

    def read_from_file(self, filename):
        self.image = Image.open(filename) # use PIL / Pillow library to read bitmap
        if color_mode == "grayscale":
            self.image = self.image.convert("L")
        elif color_mode == "color":
            self.image = self.image.convert("RGB")

# command line arguments #
##########################

def init_commandline_args():
    parser = argparse.ArgumentParser(prog="PVD", description="Pixel Value Differencing Steganography")

    parser.add_argument("-c", "--cover-image", help="cover image to hide message in")
    parser.add_argument("-m", "--message-file", help="file containing secret message to hide")
    parser.add_argument("-o", "--output-file", help="file to write output to (defaults to stdout if none given in --extract-image mode)")
    parser.add_argument("-e", "--extract-image", help="extracts hidden data from this image")
    parser.add_argument("-n", "--dry-run", help="don't hide data, just find capacity for given cover image", action="store_true")
    parser.add_argument("-v", "--verbose", help="print out extra information", action="store_true")
    parser.add_argument("-q", "--quiet", help="don't print out anything", action="store_true")
    parser.add_argument("--rgb", help="hide in color components (defualts to --gray if unspecified)", action="store_true")
    parser.add_argument("--gray", help="convert to grayscale and hide only in luminance (defualts to --gray if unspecified)", action="store_true")
    parser.add_argument("--horizontal", help="use horizontal pixel pairs (defualts to --horizontal if unspecified)", action="store_true")
    parser.add_argument("--vertical", help="use vertical pixel pairs (defualts to --horizontal if unspecified)", action="store_true")
    parser.add_argument("--key", help="key for randomized hiding locations")

    args = parser.parse_args()
    return args

def validate_args(args): # ensures user has given the correct options, and the needed files exist
    if args.extract_image:
        if not os.path.exists(args.extract_image):
            exit("error: image to extract from does not exist")
        else:
            return

    if args.rgb and args.gray:
        exit("error: you must specify only --rgb or --gray, not both")

    if args.horizontal and args.vertical:
        exit("error: you must specify only --horizontal or --vertical, not both")

    if not args.cover_image: # invalid bc no file given
        exit("error: no cover image specified")

    if not os.path.exists(args.cover_image): # invalid bc file given does not exist
        exit("error: cover image does not exist")

    if not args.dry_run:
        if not (args.output_file and args.message_file): # invalid becuase no files given
            exit("error: you must specify an output image and a message file")

        if not os.path.exists(args.message_file):
            exit("error: message file does not exist")

        if os.path.exists(args.output_file):
            print("warning: output image", args.output_file, "already exists. You have 5s to cancel...")
            time.sleep(5)

def apply_settings_from_args(args):
    global color_mode
    global pixel_pair_mode
    global debug_mode
    global quiet_mode

    if args.verbose:
        debug_mode = 1

    if args.quiet:
        quiet_mode = 1

    if args.vertical:
        pixel_pair_mode = "vertical"
    if args.horizontal:
        pixel_pair_mode = "horizontal"

    if args.rgb:
        color_mode = "color"
    elif args.gray:
        color_mode = "grayscale"

# Image iterating generator thing #
###################################
# using pythons generators will allow us to write logic for iterating through pixel-pairs
# in different ways, allowing experimentation with different pairs (horizontal vs vertical)
# and different paths (left->right, top->bottom vs randomly determined with symmetric key, etc)
def pixel_pairs(img, key=None): # takes PIL Image object as parameter
    if key:
        import random
        random.seed(key)
        coords = list(pixel_pairs(img, key=None))
        random.shuffle(coords)
        for c in coords:
            yield c

    size_x, size_y = img.size
    if pixel_pair_mode == "horizontal":
        if pixel_iteration_mode == "standard":
            # left to right first, then top to bottom (like reading)
            # only do odd number x values, then the pair of pixels is x-1,y  x,y
            for y in range(size_y):
                for x in range(1,size_x,2): # start with 1, go by twos. gives us only odd numbers.
                    yield ((x-1, y), (x, y))
        else:
            print("ERROR: pixel iteration mode", pixel_iteration_mode, "not recognized")
    elif pixel_pair_mode == "vertical":
        if pixel_iteration_mode == "standard":
            # left to right first, then top to bottom (like reading)
            # only do odd number x values, then the pair of pixels is x-1,y  x,y
            for y in range(1,size_y,2):
                for x in range(size_x): # start with 1, go by twos. gives us only odd numbers.
                    yield ((x, y-1), (x, y))
        else:
            print("ERROR: pixel iteration mode", pixel_iteration_mode, "not recognized")
    else:
        print("ERROR: pixel pair mode", pixel_pair_mode, "not recognized")
        exit()

# functions for calculating and applying difference #
#####################################################

def get_log2(val): # ended up doing this a lot so we made a function
    return math.floor(math.log2(val))

def calculate_difference(pixel1, pixel2):
    return abs(pixel1-pixel2)

def find_difference_range(pixel_pair): # this is the range the difference falls into, ie diff=5 -> [0,1,2,3,4,5,6,7]
    diff = abs(pixel_pair[0] - pixel_pair[1])
    for i in range(1, len(diff_ranges)):
        if diff < diff_ranges[i]:
            diff_range = list(range(diff_ranges[i-1], diff_ranges[i]))
            return diff_range
    print("ERROR: for some reason did not calculate range for diff =", diff)

def get_embedding_capacity(diff):
    # embedding capacity = log2(width of range)
    # ie log2 of the difference between the upper bound of the range and the lower bound of the range
    # so we find which range the difference belongs to, then take the log2 of the upperboud - lowerbound
    diff = abs(diff)
    if diff > 255:
        print("ERROR: diff is", diff, ". should be at most 255")
        return 0
    for i in range(1, len(diff_ranges)): # for each diff range
        if diff < diff_ranges[i]: # if this is the right diff range
            return get_log2(diff_ranges[i] - diff_ranges[i-1]) # capacity floor(log2(upper - lower))

# change pixel values to have correct difference, while minimizing and balancing change
# formula provided from the paper
def calculate_new_vals_from_difference(pixel_pair, new_diff, diff):
    m = new_diff - diff # m is new_difference - old_difference. I guess you could name it like "diffdiff", but I thought it'd be less confusing to just use the paper's variable

    # this part is weird, it was having trouble calculating it right, and would sometimes flip the signs of what to add
    # but not all the time. So I just added a check where if the difference was wrong, do it again but flip the sign
    while True:
        if debug_mode and not quiet_mode: print("[dbg] m =",m, "m/2 =", m/2, " diff =", diff)
        if diff % 2 == 1: # diff is odd
            if debug_mode and not quiet_mode: print("[dbg] diff is odd")
            new_vals = (pixel_pair[0] - math.ceil(m/2), pixel_pair[1] + math.floor(m/2))
            if debug_mode and not quiet_mode: print("[dbg]", "(",pixel_pair[0]," - (ceil)",math.ceil(m/2),", ",pixel_pair[1]," + (floor)",math.floor(m/2))
        else: # diff is even
            if debug_mode and not quiet_mode: print("[dbg] diff is even")
            new_vals = (pixel_pair[0] - math.floor(m/2), pixel_pair[1] + math.ceil(m/2))
            if debug_mode and not quiet_mode: print("[dbg]", "(",pixel_pair[0]," - (floor)",math.floor(m/2),", ",pixel_pair[1]," + (ceil)",math.ceil(m/2),")")

        # if difference is right, break and return. Else try again with flipped sign
        if calculate_difference(new_vals[0], new_vals[1]) == new_diff:
            break
        m = -m
    return new_vals


# embed data #
##############
# this is the main logic for embedding data
def embed_data_into_image(cover_image, message_bits, output_filename, key=None):
    output_file = cover_image.copy()
    msg_index = 0
    msg_length = len(message_bits)
    pixels = output_file.load()

    old_msg_index = 0

    for pixel_coords_1, pixel_coords_2 in pixel_pairs(cover_image, key=key):
        pixel1=cover_image.getpixel(pixel_coords_1)
        pixel2=cover_image.getpixel(pixel_coords_2)
        if msg_index >= msg_length:
            break
        if color_mode == "grayscale":
            pixel_components = [[cover_image.getpixel(pixel_coords_1),cover_image.getpixel(pixel_coords_2)]]
        elif color_mode == "color":
            pixel_components = [[cover_image.getpixel(pixel_coords_1)[0],cover_image.getpixel(pixel_coords_2)[0]], [cover_image.getpixel(pixel_coords_1)[1],cover_image.getpixel(pixel_coords_2)[1]], [cover_image.getpixel(pixel_coords_1)[2],cover_image.getpixel(pixel_coords_2)[2]]]
        
        new_vals = []
        for pixel1, pixel2 in pixel_components:
            # find difference range for pixel pair
            # and also check if valid pixel pair
            #######################################
            diff = calculate_difference(pixel1, pixel2)
            diff_range = find_difference_range((pixel1, pixel2))
            pixel_pair_possible_vals = calculate_new_vals_from_difference((pixel1, pixel2), diff_range[-1], diff)
            # from the paper. determine if pixelpair should be skipped:
            if pixel_pair_possible_vals[0] < 0 or pixel_pair_possible_vals[0] > 255 or pixel_pair_possible_vals[1] < 0 or pixel_pair_possible_vals[1] > 255:
                # invalid pair
                if not quiet_mode: print("skipping pair:", pixel1, pixel2, "diff =", diff, "possible vals =", pixel_pair_possible_vals, "(not in [0..255])")
                new_vals.append([pixel1,pixel2])
                continue
 
            # find capacity and get msg bits
            #################################
 
            capacity = get_embedding_capacity(diff)
            old_msg_index = msg_index # set lower boundary as last time's upper boundary+1
            msg_index += capacity # set upper boundary as lower boundary + capacity
            if msg_index > msg_length: # if no more bits, just get the rest of them
                msg_index = msg_length + 1
 
            bits_to_embed = message_bits[old_msg_index:msg_index]
            if len(bits_to_embed) < capacity: # if not enough bits, add zeros
                bits_to_embed = bits_to_embed.ljust(capacity, '0')
 
            bits_value = int(bits_to_embed, 2)
            if debug_mode and not quiet_mode: print(f"[dbg] coords are {pixel_coords_1}, {pixel_coords_2}")
            if debug_mode and not quiet_mode: print(f"[dbg] old_msg_index={old_msg_index} - Embedding bits {bits_to_embed} as {bits_value} , value is {pixel1} and {pixel2} before mod")
 
            # find new difference / pixel vals
            ###################################
            new_diff = diff_range[bits_value]
            new_vals.append(calculate_new_vals_from_difference((pixel1, pixel2), new_diff, diff))
            if debug_mode and not quiet_mode: print(f"[dbg] -> changing difference from {diff} to {new_diff}. New vals are {new_vals[-1][0]} and {new_vals[-1][1]}")


 
        # embed bits into output img
        #############################
        if color_mode == "grayscale":
            new_vals = new_vals[0]
        elif color_mode == "color":
            new_vals = (tuple([x[0] for x in new_vals]), tuple([x[1] for x in new_vals]))
        pixels[pixel_coords_1[0], pixel_coords_1[1]] = new_vals[0]
        pixels[pixel_coords_2[0], pixel_coords_2[1]] = new_vals[1]
        if debug_mode and not quiet_mode: print("[dbg] embedded into image: pxl1", output_file.getpixel(pixel_coords_1), "pxl2", output_file.getpixel(pixel_coords_2), end="\n\n")

    if msg_index < msg_length:
        print(f"Warning: Could not embed the full message. Only part of the message was embedded. Embedded {msg_index / msg_length * 100}% = {msg_index} bits = {msg_index / 8} bytes")

    # Save the modified image
    output_file.save(output_filename, "bmp")
    if not quiet_mode: print(f"Output image saved as {output_filename}")

# extract data from stego image #
#################################
# this is the main logic for extraction

def extract_data(steg_image, key=None):
    bits = ""
    bytes_to_read = 0 # will change later

    for pixel_coords_1, pixel_coords_2 in pixel_pairs(steg_image, key=key):
        # break when we've read all the message bits #
        ##############################################
        if len(bits) > num_bits_for_size and not bytes_to_read: # wait to determine msg size until we've read enough bits
            bytes_to_read = int(bits[0:num_bits_for_size],2)
        if bytes_to_read and len(bits) >= (8*bytes_to_read + num_bits_for_size): #
            break

        if debug_mode and not quiet_mode: print(f"[dbg] in extract_data(), color_mode is {color_mode}")
        if color_mode == "grayscale":
            pixel_components = [[steg_image.getpixel(pixel_coords_1),steg_image.getpixel(pixel_coords_2)]]
        elif color_mode == "color":
            pixel_components = [[steg_image.getpixel(pixel_coords_1)[0],steg_image.getpixel(pixel_coords_2)[0]], [steg_image.getpixel(pixel_coords_1)[1],steg_image.getpixel(pixel_coords_2)[1]], [steg_image.getpixel(pixel_coords_1)[2],steg_image.getpixel(pixel_coords_2)[2]]]
        else:
            print("ERROR: color mode unrecognized:", color_mode)
            exit()
        
        for pixel1, pixel2 in pixel_components:
            # find difference range for pixel pair
            # and also check if valid pixel pair
            #######################################
            diff = calculate_difference(pixel1, pixel2)
            diff_range = find_difference_range((pixel1, pixel2))
            pixel_pair_possible_vals = calculate_new_vals_from_difference((pixel1, pixel2), diff_range[-1], diff)
            # from the paper. determine if pixelpair should be skipped:
            if pixel_pair_possible_vals[0] < 0 or pixel_pair_possible_vals[0] > 255 or pixel_pair_possible_vals[1] < 0 or pixel_pair_possible_vals[1] > 255:
                # invalid pair
                if not quiet_mode: print("skipping pair:", pixel1, pixel2, "diff =", diff, "possible vals =", pixel_pair_possible_vals, "(not in [0..255])")
                continue

            # find capacity and get msg bits
            #################################

            capacity = get_embedding_capacity(diff)

            bits_value = format(diff_range.index(diff), '0'+str(capacity)+'b')

            if debug_mode and not quiet_mode: print(f"[dbg] coords are {pixel_coords_1}, {pixel_coords_2}")
            if debug_mode and not quiet_mode: print(f"[dbg] extracted bits {bits_value}, pixel values: {pixel1}, {pixel2}, diff is {diff}, range is {diff_range}")

            bits = bits + bits_value

    bits = bits[num_bits_for_size:] # remove size of message before returning
    return bits


# Add filesize to data #
########################
# this function will prepend a 32-bit
# number to the data, which contains
# the size of the data to extract
def add_filesize_bits(bitstring):
    if debug_mode and not quiet_mode: print(f"Bitstring: {bitstring}")

    # Ensure the bitstring consists of '0's and '1's
    if not all(c in '01' for c in bitstring):
        raise ValueError("Bitstring should only contain '0's and '1's.")

    # Calculate the size of the bitstring in bytes
    bitstring_size = len(bitstring) // 8
    if len(bitstring) % 8 != 0:
        bitstring_size += 1  # Account for incomplete byte

    if not quiet_mode: print(f"Size of message in bytes: {bitstring_size} bytes")

    # Convert the size to a 32-bit binary string
    size_bits = ("{:0" + str(num_bits_for_size) + "b}").format(bitstring_size) # this is kinda weird, but basically it'll just turn the number into a binary string of num_bits_for_size size, this way its dynamic with the variable and we don't have to change it
    if debug_mode and not quiet_mode: print(f"Size as {num_bits_for_size}-bit binary string: {size_bits}")

    # Prepend the size bits to the original bitstring
    combined_data = size_bits + bitstring
    if debug_mode and not quiet_mode: print(f"Combined data: {combined_data}")

    return combined_data

# read message file #
#####################
# this will read in a message file and
# convert the data to binary to be written
def read_message_file(filepath):
    with open(filepath, 'r') as file:
        message = file.read()
    # Convert message to binary string
    return ''.join(format(ord(char), '08b') for char in message)

# main function #
#################
def main():
    args = init_commandline_args()
    validate_args(args) # will exit if invalid args
    apply_settings_from_args(args)


    key=None
    if args.key:
        key = args.key

    if args.extract_image:
        steg_image = bitmap(args.extract_image)
        data = extract_data(steg_image.image, key=key)
        if debug_mode and not quiet_mode: print("your data is: ", data)

        if not args.output_file: # default to stdout if no output file given
            for i in range(0, len(data), 8):
                byte = data[i:i+8]
                byte = int(byte, 2)
                print(chr(byte),end="")
        else:
            with open(args.output_file, "wb") as f:
                data_bytes = []
                for i in range(0, len(data), 8):
                    byte = data[i:i+8]
                    byte = int(byte, 2)
                    data_bytes.append(byte)
                data_bytes = [x & 255 for x in data_bytes] # ensure all values are between 0-255 (they should be, but just a sanity check)
                data_bytes = bytes(data_bytes)
                f.write(data_bytes)

    elif args.dry_run:
        cover_image = bitmap(args.cover_image)
        total_capacity = 0
        for pixel_pair_coords in pixel_pairs(cover_image.image, key=key):
            pixel_pair = [cover_image.image.getpixel(pixel_pair_coords[z]) for z in [0,1]]
            if color_mode == "grayscale":
                total_capacity += get_embedding_capacity(pixel_pair[0] - pixel_pair[1])
            elif color_mode == "color":
                total_capacity += get_embedding_capacity(pixel_pair[0][0] - pixel_pair[0][1])
                total_capacity += get_embedding_capacity(pixel_pair[1][0] - pixel_pair[1][1])
                total_capacity += get_embedding_capacity(pixel_pair[2][0] - pixel_pair[2][1])
        print("total capacity is:", total_capacity, "bits =", total_capacity // 8, "bytes =", total_capacity // 64, "MB")

    else:
        # Embed message into image
        # Example command line input I used to run this
        # python3 PVD.py -c ../tunnel.bmp -m smallPi.txt -o firstImg.bmp
        cover_image = bitmap(args.cover_image)
        message_bits = read_message_file(args.message_file)
        full_bits = add_filesize_bits(message_bits)
        embed_data_into_image(cover_image.image, full_bits, args.output_file, key=key)
        if not quiet_mode: print(f"Data embedded successfully into {args.output_file}")


if __name__=="__main__":
    main()
