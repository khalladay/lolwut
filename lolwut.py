import argparse
import os
import sys
import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

MAX_LINES = 2

def parse_args():
    parser = argparse.ArgumentParser(description = "Intended usage: lolwut <image_dir> <string_src> <output_dir>")
    parser.add_argument('image_dir', type=str, help="path to a directory containing images to overlay text on")
    parser.add_argument('string_src', type=str, help="a .txt file containing strings to overlay on images")
    parser.add_argument('font', type=str, help="a .ttf file containing font to use")
    parser.add_argument('output_dir', type=str, help="output dir of script")
    parser.parse_args()

    args = parser.parse_args()
    if os.path.isdir(args.image_dir) == False:
        print("Error: Directory "+args.image_dir+" provided for image_dir arg does not exist",file=sys.stderr)
        exit()
    
    if len(os.listdir(args.image_dir)) == 0:
        print("Error: Directory "+args.image_dir+" provided for image_dir arg is empty", file=sys.stderr)
        exit()
    
    if os.path.isfile(args.string_src) == False:
        print("Error: "+args.string_src+" provided for string_src arg does not exist.", file=sys.stderr)
        exit()

    if os.path.isdir(args.output_dir) == False:
        print("Error: "+args.output_dir+" provided for output_dir arg does not exist", file=sys.stderr)
        exit()

    if os.path.isfile(args.font) == False:
        print("Error: "+args.font+" provided for font arg does not exist.", file=sys.stderr)
        exit()

    return args

def parse_strings(strings_filepath):
    string_pairs = []
    
    top_line = ""
    bottom_line = ""

    with open(strings_filepath, "r") as strings_file:
        #strings_file.seek(0)
        line = strings_file.readline()
        while line:
            if line == "\r" or line == "\n":
                top_line = bottom_line = ""
                line = strings_file.readline()
                continue

            trimmed_line = line.replace("\r", "").replace("\n", "")
            
            if len(top_line) == 0:
                top_line = trimmed_line
            elif len(bottom_line) == 0:
                bottom_line = trimmed_line
                string_pairs.append((top_line, bottom_line))
            
            line = strings_file.readline()
    
    return string_pairs

def draw_outlined_text(x,y, text, img_draw, font):
    img_draw.text((x-2, y-2), text, (0,0,0),font=font)
    img_draw.text((x+2,y+2), text, (0,0,0),font=font)
    img_draw.text((x-2, y+2), text, (0,0,0),font=font)
    img_draw.text((x+2, y-2), text, (0,0,0),font=font)
    img_draw.text((x,y), text, font=font)

def get_linecount(string, imagedraw, image, font):
    w, h = imagedraw.textsize(string, font) # measure the size the text will take
    lc = int(round((w / image.width) + 1))
    return lc


def main():
    args = parse_args()

    source_images = os.listdir(args.image_dir);
    source_images = [x for x in source_images if x.endswith(".jpg") or x.endswith(".jpeg")]

    source_strings = parse_strings(args.string_src)
    out_count = 0

    font_size = 52

    for i in range(0, len(source_strings)):
        img_idx = random.randint(0,len(source_images)-1)
        img = Image.open(args.image_dir+"/"+source_images[img_idx])
        font = ImageFont.truetype(args.font, font_size)
        string_pair = source_strings[i]
        draw = ImageDraw.Draw(img)
        
        #draw top line, centered, wrap centered if string is too long. 
        #shrink text if string won't fit on two lines
        top_line_count = get_linecount(string_pair[0], draw, img, font)
        bottom_line_count = get_linecount(string_pair[1], draw, img, font)

        while max(top_line_count, bottom_line_count) > MAX_LINES:
            font_size-=1
            font = ImageFont.truetype(args.font, font_size)
            top_line_count = get_linecount(string_pair[0], draw, img, font)
            bottom_line_count = get_linecount(string_pair[1], draw, img, font)


        #split strings into MAX_LINES strings if needed
        top_lines = []
        bottom_lines = []

        
        w, h = draw.textsize(string_pair[0], font)
        draw_outlined_text(10,10, string_pair[0].upper(), draw, font)

        w, h = draw.textsize(string_pair[1], font)
        draw_outlined_text(10, img.height-h-10, string_pair[1].upper(), draw, font)
        img.save(args.output_dir+"/"+"output"+str(out_count)+".jpg")
        out_count+=1
    



if __name__ == "__main__":
    main()