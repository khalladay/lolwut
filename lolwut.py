import argparse
import os
import sys
import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

MAX_LINES = 2
X_PADDING = 0
Y_PADDING = 10
LINE_PADDING = 5

def parse_args():
    parser = argparse.ArgumentParser(description = "Intended usage: lolwut <image_dir> <string_src> <output_dir>")
    parser.add_argument('image_dir', type=str, help="path to a directory containing images to overlay text on")
    parser.add_argument('string_src', type=str, help="a .txt file containing strings to overlay on images")
    parser.add_argument('font', type=str, help="a .ttf file containing font to use")
    parser.add_argument('output_dir', type=str, help="output dir of script")
    parser.add_argument('-width', type=int, help="optional - force image resize to use this width")
    parser.add_argument('-height', type=int, help="optional - force image resize to use this height")
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

            trimmed_line = line.replace("\r", "").replace("\n", "").upper()
            
            if trimmed_line == "_":
                trimmed_line = " "

            if len(top_line) == 0:
                top_line = trimmed_line
            elif len(bottom_line) == 0:
                bottom_line = trimmed_line
                string_pairs.append((top_line, bottom_line))
                bottom_line = top_line = ""
            line = strings_file.readline()

        if len(top_line) > 0 or len(bottom_line) > 0:
            string_pairs.append((top_line, bottom_line))

    return string_pairs

def draw_outlined_text(x,y, text, img_draw, font):
    img_draw.text((x-2, y-2), text, (0,0,0),font=font)
    img_draw.text((x+2,y+2), text, (0,0,0),font=font)
    img_draw.text((x-2, y+2), text, (0,0,0),font=font)
    img_draw.text((x+2, y-2), text, (0,0,0),font=font)
    img_draw.text((x,y), text, font=font)

def get_raw_linecount(string, imagedraw, image, font):
    w, _ = imagedraw.textsize(string, font) # measure the size the text will take
    lc = int(round((w / (image.width-X_PADDING*2)) + 1))
    return lc

def get_linecount(string, imagedraw, image, font):
    chars_remaining = len(string)
    cur_cut = 1
    last_cut = 0
    lc = 0
    while chars_remaining > 0:
        while cur_cut-last_cut < chars_remaining and get_raw_linecount(string[last_cut:cur_cut], imagedraw, image, font) < 2:
            cur_cut+=1

        while(cur_cut != len(string) and string[cur_cut] != " "):
            cur_cut -= 1

        chars_remaining -= cur_cut-last_cut
        last_cut = cur_cut
        lc+=1
    return lc        

def main():
    args = parse_args()

    source_images = os.listdir(args.image_dir)
    source_images = [x for x in source_images if x.endswith(".jpg") or x.endswith(".jpeg")]

    source_strings = parse_strings(args.string_src)
    out_count = 0

    #build a list of images to use that ensures that no image is duplicated until all have been used at least once
    image_indices = []
    for i in range(0, len(source_strings)):
        if i < len(source_images)-1:
            image_indices.append(i)
        else:
            image_indices.append(random.randint(0,len(source_images)-1))

    random.shuffle(image_indices)
    random.shuffle(source_strings)

    for i in range(0, len(source_strings)):
        font_size = 52
        img = Image.open(args.image_dir+"/"+source_images[image_indices[i]])
        font = ImageFont.truetype(args.font, font_size)
        string_pair = source_strings[i]

        #handle image resize here - it's not optimal since we'll be resizing unnecessarily, but it's easy
        if (args.width != None or args.height != None):
            target_w = img.width if args.width == None else args.width
            target_h = img.height if args.height == None else args.height

            if target_h < img.height or target_w < img.width:
                img = img.resize((target_w, target_h), Image.LANCZOS)
            else:
                img = img.resize((target_w, target_h), Image.BILINEAR)

        draw = ImageDraw.Draw(img)

        #draw top line, centered, wrap centered if string is too long. 
        #shrink text if string won't fit on two lines
        line_counts = [get_linecount(string_pair[0], draw, img, font), get_linecount(string_pair[1], draw, img, font)]

        while max(line_counts[0], line_counts[1]) > MAX_LINES:
            font_size-=1
            font = ImageFont.truetype(args.font, font_size)
            line_counts[0] = get_linecount(string_pair[0], draw, img, font)
            line_counts[1] = get_linecount(string_pair[1], draw, img, font)


        #split strings into MAX_LINES strings if needed
        for s in range(0, 2 if len(string_pair[1]) > 0 else 1):
            last_cut = 0
            for i in range(0, line_counts[s]):
                #figure out where to split string, first get num chars in line
                # we already know how many lines a string _should_ take, so to get
                # the cut point we can start by trying to divide by linecount
                cut_point = 1
                while (cut_point < len(string_pair[s]) and get_linecount(string_pair[s][last_cut:cut_point], draw, img, font) < 2):
                    cut_point+=1

                #then we need to back up from the cut point to the first whitespace char
                #to avoid cutting words in half
                while(cut_point != len(string_pair[s]) and string_pair[s][cut_point] != " "):
                    cut_point -= 1

                #if this isn't the first cut, we need to advance the last_cut by 1 to avoid starting a new line
                #with a space 
                if last_cut != 0:
                    last_cut +=1

                w, h = draw.textsize(string_pair[s][last_cut:cut_point], font)
                y_val = 0

                if s == 0:
                    y_val = Y_PADDING+(h+LINE_PADDING)*i
                else: # for bottom text, the first line has to be the highest on the image
                    y_val = img.height - Y_PADDING - (h+LINE_PADDING)*(line_counts[s]-i)


                x_val = (img.width/2)-(X_PADDING*2)-(w/2)
                draw_outlined_text(x_val,y_val, string_pair[s][last_cut:cut_point], draw, font)
                last_cut = cut_point
        
        img.save(args.output_dir+"/"+"manatee"+str(out_count)+".jpg")
        out_count+=1
    

if __name__ == "__main__":
    main()