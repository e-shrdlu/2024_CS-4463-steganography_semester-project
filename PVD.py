##################################
# Authors
##################################
# Nat Broyles
# Chelse Miles
# Aidan Kollar


import argparse
import textwrap
import os
import time
import math
from PIL import Image

# global vars / settings #
##########################

# placeholders for now, will update generator function to do more later
pixel_pair_mode = "horizontal"
pixel_iteration_mode = "standard"
color_mode = "grayscale"


# bitmap class #
################

class bitmap:
    def __init__(self, filename):
        self.read_from_file(filename)

    def read_from_file(self, filename):
        self.image = Image.open(filename) # use PIL / Pillow library to read bitmap
        # self.image.load()

    def write_to_file(self, filename):
        # TODO
        pass

# command line arguments #
##########################
def init_commandline_args():
    parser = argparse.ArgumentParser(prog="PVD", description="Pixel Value Differencing Steganography") #, epilog=textwrap.dedent("""
        # example usage:
        #     python3 PVD.py -c my-cover-image.bmp -m my-secret-message.txt -o my-new-image.bmp
        #      - hide file into cover image
        #
        #     python3 PVD.py -c my-cover-image.bmp -n
        #      - check capacity of my-cover-image.bmp
        #
        #     python3 PVD.py -e my-new-image.bmp -o my-recovered-message.txt
        #      - extract file from stego image"""))
        # ^ ^ ^ ^ ^ ^ ^ ^ tried to add to help text, but it wasn't working (argparse strips the newlines and it looks kinda bad

    parser.add_argument("-c", "--cover-image", help="cover image to hide message in")
    parser.add_argument("-m", "--message-file", help="file containing secret message to hide")
    parser.add_argument("-o", "--output-file", help="where to store output")
    parser.add_argument("-e", "--extract-image", help="extracts hidden data from this image")
    parser.add_argument("-n", "--dry-run", help="don't hide data, just find capacity for given cover image", action="store_true")
    args = parser.parse_args()
    return args

def validate_args(args): # ensures user has given the correct options, and the needed files exist
    if args.extract_image:
        if not os.path.exists(args.extract_image):
            exit("error: image to extract from does not exist")
        if not os.path.exists(args.output_file):
            exit("error: you need to provide an output file")
        else:
            return

    if not args.cover_image: # invalid bc no file given
        exit("error: no cover image specified")
    
    if not os.path.exists(args.cover_image): # invalid bc file given does not exist
        exit("error: cover image does not exist")

    if not args.dry_run:
        if not (args.output_file and args.message_file): # invalid becuase no files given
            exit("error: you must specify an output image and a message file")

        if not os.path.exists(args.message_file):
            exit("error: message file does not exist")

        if not os.path.exists(args.output_file):
            print("warning: output image", args.output_file, "already exists. You have 1s to cancel...")
            time.sleep(1)

# Image iterating generator thing #
###################################
# using pythons generators will allow us to write logic for iterating through pixel-pairs
# in different ways, allowing experimentation with different pairs (horizontal vs vertical)
# and different paths (left->right, top->bottom vs randomly determined with symmetric key, etc)
# stores pair as ((R,G,B), (R,G,B)) for color
# or as (brightness, brightness) for grayscale
def pixel_pairs(img): # takes PIL Image object as parameter
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
        print("TODO: implement vertical pixel pairs")
        #TODO
        exit()
    else:
        print("ERROR: pixel pair mode", pixel_pair_mode, "not recognized")
        exit()

def calculate_rgb_difference(pixel1, pixel2):
    # Calculate the difference between 2 RGB pixel values, will be used for determining range to hide in
    return (abs(pixel1[0] - pixel2[0]), abs(pixel1[1] - pixel2[1]), abs(pixel1[2] - pixel2[2]))

def calculate_gray_difference(pixel1, pixel2):
    return abs(pixel1-pixel2)

def get_embedding_capacity(diff):
    adiff = abs(diff)
    if 0 <= adiff <= 7:
        return 2
    elif 8 <= adiff <= 15:
        return 3
    elif 16 <= adiff <= 31:
        return 4
    elif 32 <= adiff <= 63:
        return 5
    elif 64 <= adiff <= 127:
        return 6
    elif 128 <= adiff <= 255:
        return 7
    else:
        return 0

def get_log2(val):
    if 0 <= val <= 7:
        return 2
    elif 8 <= val <= 15:
        return 3
    elif 16 <= val <= 31:
        return 4
    elif 32 <= val <= 63:
        return 5
    elif 64 <= val <= 127:
        return 6
    elif 128 <= val <= 255:
        return 7
    else:
        return 0

def read_message_file(filepath):
    with open(filepath, 'r') as file:
        message = file.read()
    # Convert message to binary string
    return ''.join(format(ord(char), '08b') for char in message)

def find_difference_range(pixel_pair):
    diff = abs(pixel_pair[0] - pixel_pair[1])
    # TODO: implement more ranges
    diff_ranges = [0,8,16,32,64,128,256]
    for i in range(1, len(diff_ranges)):
        if diff < diff_ranges[i]:
            diff_range = list(range(diff_ranges[i-1], diff_ranges[i]))
            return diff_range
    print("ERROR: for some reason did not calculate range for diff =", diff)


def grayscale_new_vals(pixel_pair, m): # m is new_difference - old_difference. I guess you could name it like "diffdiff", but I thought it'd be less confusing to just use the paper's variable
    # from the paper
    diff = calculate_gray_difference(pixel_pair[0], pixel_pair[1])
    if diff % 2 == 1: # diff is odd
        new_vals = (pixel_pair[0] - math.ceil(m/2), pixel_pair[1] + math.floor(m/2))
    else: # diff is even
        new_vals = (pixel_pair[0] - math.floor(m/2), pixel_pair[1] + math.ceil(m/2))
    return new_vals

def extract_data(steg_image):
    # THIS IS JUST COPY/PASTED FROM EMBED FUNC #
    # DOES NOT WORK YET #
    # CHANGE LATER #
    bits = []

    for pixel_coords_1, pixel_coords_2 in pixel_pairs(steg_image):
        pixel1=steg_image.getpixel(pixel_coords_1)
        pixel2=steg_image.getpixel(pixel_coords_2)
        if msg_index >= msg_length:
            break
        set
        if color_mode == "grayscale":
            # find difference range for pixel pair
            # and also check if valid pixel pair
            #######################################
            diff = calculate_gray_difference(pixel1, pixel2)
            diff_range = find_difference_range((pixel1, pixel2))
            pixel_pair_possible_vals = grayscale_new_vals((pixel1, pixel2), diff_range[1] - diff)
            # from the paper. determine if pixelpair should be skipped:
            if pixel_pair_possible_vals[0] < 0 or pixel_pair_possible_vals[0] > 255 or pixel_pair_possible_vals[1] < 0 or pixel_pair_possible_vals[1] > 255:
                # invalid pair
                print("skipping pair:", pixel1, pixel2, "diff =", diff, "range =", diff_range, "possible vals =", pixel_pair_possible_vals)
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
            print(f"[dbg] Embedding bits {bits_to_embed} as {bits_value} , value is {pixel1} and {pixel2} before mod")

            # find new difference / pixel vals
            ###################################
            new_diff = diff_range[bits_value]
            new_vals = grayscale_new_vals((pixel1, pixel2), new_diff - diff)
            print(f"[dbg] -> changing difference from {diff} to {new_diff}. New vals are {new_vals[0]} and {new_vals[1]}")

            # embed bits into output img
            #############################
            pixels[pixel_coords_1[0], pixel_coords_1[1]] = new_vals[0]
            pixels[pixel_coords_2[0], pixel_coords_2[1]] = new_vals[1]
            print("[dbg] embedded into image: pxl1", output_file.getpixel(pixel_coords_1), "pxl2", output_file.getpixel(pixel_coords_2))
    return data

def embed_data_into_image(cover_image, message_bits, output_filename):
    output_file = cover_image.copy()
    msg_index = 0
    msg_length = len(message_bits)
    pixels = output_file.load()

    old_msg_index = 0

    for pixel_coords_1, pixel_coords_2 in pixel_pairs(cover_image):
        pixel1=cover_image.getpixel(pixel_coords_1)
        pixel2=cover_image.getpixel(pixel_coords_2)
        if msg_index >= msg_length:
            break
        set
        if color_mode == "grayscale":
            # find difference range for pixel pair
            # and also check if valid pixel pair
            #######################################
            diff = calculate_gray_difference(pixel1, pixel2)
            diff_range = find_difference_range((pixel1, pixel2))
            pixel_pair_possible_vals = grayscale_new_vals((pixel1, pixel2), diff_range[1] - diff)
            # from the paper. determine if pixelpair should be skipped:
            if pixel_pair_possible_vals[0] < 0 or pixel_pair_possible_vals[0] > 255 or pixel_pair_possible_vals[1] < 0 or pixel_pair_possible_vals[1] > 255:
                # invalid pair
                print("skipping pair:", pixel1, pixel2, "diff =", diff, "range =", diff_range, "possible vals =", pixel_pair_possible_vals)
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
            print(f"[dbg] Embedding bits {bits_to_embed} as {bits_value} , value is {pixel1} and {pixel2} before mod")

            # find new difference / pixel vals
            ###################################
            new_diff = diff_range[bits_value]
            new_vals = grayscale_new_vals((pixel1, pixel2), new_diff - diff)
            print(f"[dbg] -> changing difference from {diff} to {new_diff}. New vals are {new_vals[0]} and {new_vals[1]}")

            # embed bits into output img
            #############################
            pixels[pixel_coords_1[0], pixel_coords_1[1]] = new_vals[0]
            pixels[pixel_coords_2[0], pixel_coords_2[1]] = new_vals[1]
            print("[dbg] embedded into image: pxl1", output_file.getpixel(pixel_coords_1), "pxl2", output_file.getpixel(pixel_coords_2))

        else: # not grayscale
            # Calculate differences for each color channel
            diff_r = (pixel1[0] - pixel2[0])
            diff_g = (pixel1[1] - pixel2[1])
            diff_b = (pixel1[2] - pixel2[2])
            
            # Determine embedding capacity based on the difference
            capacity_r = get_embedding_capacity(diff_r)
            capacity_g = get_embedding_capacity(diff_g)
            capacity_b = get_embedding_capacity(diff_b)
            
            # Embed data into the differences sequentially
            # pixels have their dif
            if msg_index < msg_length and capacity_r > 0:
                bits_to_embed = message_bits[msg_index:msg_index + capacity_r]
                if len(bits_to_embed) < capacity_r:
                    bits_to_embed = bits_to_embed.ljust(capacity_r, '0')
                bits_value = int(bits_to_embed, 2)
                msg_index += capacity_r
                print(f"[dbg] Embedding bits {bits_to_embed} as {bits_value} into R-channel, value is {pixel1[0]} and {pixel2[0]} before mod")
                
    
                x = get_log2(abs(diff_r))
                new_abs_diff = (2 ** x) + bits_value
                total_change = new_abs_diff - abs(diff_r)
                print(f"Log index is {x} at 2^x = {2 ** x} and diff goes from {abs(diff_r)} to {new_abs_diff} for a total change of {total_change}")
    
                # If total_change is positive then the difference between the 2 channel values needs to go up.
                while total_change >= 1:
                    
                    if total_change % 2 == 0: 
                        if pixel1[0] >= pixel2[0]:
                            if pixel1[0] < 255: 
                                pixel1 = (pixel1[0] + 1, pixel1[1], pixel1[2])
                            elif pixel2[0] > 0:
                                pixel2 = (pixel2[0] - 1, pixel2[1], pixel2[2])
                        else:
                            if pixel2[0] < 255: 
                                pixel2 = (pixel2[0] + 1, pixel2[1], pixel2[2])
                            elif pixel1[0] > 0: 
                                    pixel1 = (pixel1[0] - 1, pixel1[1], pixel1[2])
                    else: 
                        if pixel1[0] >= pixel2[0]:
                            if pixel2[0] > 0: 
                                pixel2 = (pixel2[0] - 1, pixel2[1], pixel2[2])
                            elif pixel1[0] < 255:
                                    pixel1 = (pixel1[0] + 1, pixel1[1], pixel1[2])
                        else:
                            if pixel1[0] > 0: 
                                pixel1 = (pixel1[0] - 1, pixel1[1], pixel1[2])
                            elif pixel2[0] < 255: 
                                    pixel2 = (pixel2[0] + 1, pixel2[1], pixel2[2])
    
                    total_change -= 1
                    
                while total_change <= -1:
    
                    if total_change % 2 == 0:
                        if pixel1[0] > pixel2[0]:
                            if pixel1[0] > 0:
                                pixel1 = (pixel1[0] - 1, pixel1[1], pixel1[2])
                            elif pixel2[0] < 255:
                                pixel2 = (pixel2[0] + 1, pixel2[1], pixel2[2])
                        else:
                            if pixel2[0] > 0:
                                pixel2 = (pixel2[0] - 1, pixel2[1], pixel2[2])
                            elif pixel1[0] < 255:
                                pixel1 = (pixel1[0] + 1, pixel1[1], pixel1[2])
                    else:
                        if pixel1[0] > pixel2[0]:
                            if pixel2[0] < 255:
                                pixel2 = (pixel2[0] + 1, pixel2[1], pixel2[2])
                            elif pixel1[0] > 0:
                                pixel1 = (pixel1[0] - 1, pixel1[1], pixel1[2])
                        else:
                            if pixel1[0] < 255:
                                pixel1 = (pixel1[0] + 1, pixel1[1], pixel1[2])
                            elif pixel2[0] > 0:
                                pixel2 = (pixel2[0] - 1, pixel2[1], pixel2[2])
    
                    total_change += 1
    
                print(f"value is {pixel1[0]} and {pixel2[0]} after mod")
    
            if msg_index < msg_length and capacity_g > 0:
                bits_to_embed = message_bits[msg_index:msg_index + capacity_g]
                if len(bits_to_embed) < capacity_g:
                    bits_to_embed = bits_to_embed.ljust(capacity_g, '0')
                bits_value = int(bits_to_embed, 2)
                msg_index += capacity_g
    
                print(f"[dbg] Embedding bits {bits_to_embed} as {bits_value} into G-channel, value is {pixel1[1]} and {pixel2[1]} before mod")
    
                x = get_log2(abs(diff_g))
                new_abs_diff = (2 ** x) + bits_value
                total_change = new_abs_diff - abs(diff_g)
                print(f"[dbg] Log index is {x} at 2^x = {2 ** x} and diff goes from {abs(diff_g)} to {new_abs_diff} for a total change of {total_change}")
    
                while total_change >= 1:
                    if total_change % 2 == 0:
                        if pixel1[1] >= pixel2[1]:
                            if pixel1[1] < 255:
                                pixel1 = (pixel1[0], pixel1[1] + 1, pixel1[2])
                            elif pixel2[1] > 0:
                                pixel2 = (pixel2[0], pixel2[1] - 1, pixel2[2])
                        else:
                            if pixel2[1] < 255:
                                pixel2 = (pixel2[0], pixel2[1] + 1, pixel2[2])
                            elif pixel1[1] > 0:
                                    pixel1 = (pixel1[0], pixel1[1] - 1, pixel1[2])
                    else:
                        if pixel1[1] >= pixel2[1]:
                            if pixel2[1] > 0:
                                pixel2 = (pixel2[0], pixel2[1] - 1, pixel2[2])
                            elif pixel1[1] < 255:
                                    pixel1 = (pixel1[0], pixel1[1] + 1, pixel1[2])
                        else:
                            if pixel1[1] > 0:
                                pixel1 = (pixel1[0], pixel1[1] - 1, pixel1[2])
                            elif pixel2[1] < 255:
                                    pixel2 = (pixel2[0], pixel2[1] + 1, pixel2[2])
    
                    total_change -= 1
    
                while total_change <= -1:
    
                    if total_change % 2 == 0:
                        if pixel1[1] > pixel2[1]:
                            if pixel1[1] > 0:
                                pixel1 = (pixel1[0], pixel1[1] - 1, pixel1[2])
                            elif pixel2[1] < 255:
                                pixel2 = (pixel2[0], pixel2[1] + 1, pixel2[2])
                        else:
                            if pixel2[1] > 0:
                                pixel2 = (pixel2[0], pixel2[1] - 1, pixel2[2])
                            elif pixel1[1] < 255:
                                pixel1 = (pixel1[0], pixel1[1] + 1, pixel1[2])
                    else:
                        if pixel1[1] > pixel2[1]:
                            if pixel2[1] < 255:
                                pixel2 = (pixel2[0], pixel2[1] + 1, pixel2[2])
                            elif pixel1[1] > 0:
                                pixel1 = (pixel1[0], pixel1[1] - 1, pixel1[2])
                        else:
                            if pixel1[1] < 255:
                                pixel1 = (pixel1[0], pixel1[1] + 1, pixel1[2])
                            elif pixel2[1] > 0:
                                pixel2 = (pixel2[0], pixel2[1] - 1, pixel2[2])
                    
                    total_change += 1
                print(f"value is {pixel1[1]} and {pixel2[1]} after mod")
    
            if msg_index < msg_length and capacity_b > 0:
                bits_to_embed = message_bits[msg_index:msg_index + capacity_b]
                if len(bits_to_embed) < capacity_b:
                    bits_to_embed = bits_to_embed.ljust(capacity_b, '0')
                bits_value = int(bits_to_embed, 2)
                msg_index += capacity_b
    
                print(f"[dbg] Embedding bits {bits_to_embed} as {bits_value} into B-channel, value is {pixel1[2]} and {pixel2[2]} before mod")
        
                x = get_log2(abs(diff_b))
                new_abs_diff = (2 ** x) + bits_value
                total_change = new_abs_diff - abs(diff_b)
                print(f"[dbg] Log index is {x} at 2^x = {2 ** x} and diff goes from {abs(diff_b)} to {new_abs_diff} for a total change of {total_change}")
    
                while total_change >= 1:
                    if total_change % 2 == 0: 
                        if pixel1[2] >= pixel2[2]:
                            if pixel1[2] < 255: 
                                pixel1 = (pixel1[0], pixel1[1], pixel1[2] + 1)
                            elif pixel2[2] > 0:
                                pixel2 = (pixel2[0], pixel2[1], pixel2[2] - 1)
                        else:
                            if pixel2[2] < 255: 
                                pixel2 = (pixel2[0], pixel2[1], pixel2[2] + 1)
                            elif pixel1[2] > 0: 
                                pixel1 = (pixel1[0], pixel1[1], pixel1[2] - 1)
                    else: 
                        if pixel1[2] >= pixel2[2]:
                            if pixel2[2] > 0: 
                                pixel2 = (pixel2[0], pixel2[1], pixel2[2] - 1)
                            elif pixel1[2] < 255:
                                pixel1 = (pixel1[0], pixel1[1], pixel1[2] + 1)
                        else:
                            if pixel1[2] > 0: 
                                pixel1 = (pixel1[0], pixel1[1], pixel1[2] - 1)
                            elif pixel2[2] < 255: 
                                pixel2 = (pixel2[0], pixel2[1], pixel2[2] + 1)
    
                    total_change -= 1
                    
                while total_change <= -1:
    
                    if total_change % 2 == 0:
                        if pixel1[2] > pixel2[2]:
                            if pixel1[2] > 0:
                                pixel1 = (pixel1[0], pixel1[1], pixel1[2] - 1)
                            elif pixel2[2] < 255:
                                pixel2 = (pixel2[0], pixel2[1], pixel2[2] + 1)
                        else:
                            if pixel2[2] > 0:
                                pixel2 = (pixel2[0], pixel2[1], pixel2[2] - 1)
                            elif pixel1[2] < 255:
                                pixel1 = (pixel1[0], pixel1[1], pixel1[2] + 1)
                    else:
                        if pixel1[2] > pixel2[2]:
                            if pixel2[2] < 255:
                                pixel2 = (pixel2[0], pixel2[1], pixel2[2] + 1)
                            elif pixel1[2] > 0:
                                pixel1 = (pixel1[0], pixel1[1], pixel1[2] - 1)
                        else:
                            if pixel1[2] < 255:
                                pixel1 = (pixel1[0], pixel1[1], pixel1[2] + 1)
                            elif pixel2[2] > 0:
                                pixel2 = (pixel2[0], pixel2[1], pixel2[2] - 1)
    
                    total_change += 1
                print(f"value is {pixel1[2]} and {pixel2[2]} after mod")
                print("")
    
    if msg_index < msg_length:
        print("Warning: Could not embed the full message. Only part of the message was embedded.")

    # Save the modified image
    output_file.save(output_filename)
    print(f"Output image saved as {output_file}")

def main():
    args = init_commandline_args()
    validate_args(args) # will exit if invalid args
    
    if args.extract_image:
        steg_image = bitmap(args.extract_image)
        data = extract_data(steg_image.image)
        print("your data is: ", data)
        # TODO probably find way to write this to output file
    
    elif args.dry_run:
        cover_image = bitmap(args.cover_image)
        total_capacity = 0
        for pixel_pair_coords in pixel_pairs(cover_image.image):
            pixel_pair = [cover_image.image.getpixel(pixel_pair_coords[z]) for z in [0,1]]
            if color_mode == "grayscale":
                total_capacity += get_embedding_capacity(pixel_pair[0] - pixel_pair[1])
            else:
                print("Error: color mode not implemented yet")
                # TODO: implement color for testing purposes
                diff = calculate_rgb_difference(pixel_pair[0], pixel_pair[1])
        print("total capacity is:", total_capacity, "bits =", total_capacity // 8, "bytes =", total_capacity // 64, "MB")

    else:
        # Embed message into image
        # Example command line input I used to run this
        # python3 PVD.py -c ../tunnel.bmp -m smallPi.txt -o firstImg.bmp
        cover_image = bitmap(args.cover_image)
        message_bits = read_message_file(args.message_file)
        embed_data_into_image(cover_image.image, message_bits, args.output_file)
        #cover_image.write_to_file(args.output_file)
        print(f"Data embedded successfully into {args.output_file}")


if __name__=="__main__":
    main()
