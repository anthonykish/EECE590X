from PIL import Image, ImageDraw, ImageFont
import os
import subprocess

def apply_labels(input_filename, output_filename, labels, coords, font_size=25, color="black"):

    """
    Function to more easily put labels on an image in mass. Uses PIL
    Arguments:
    input_filename
    output_filename
    labels: list of strings to write
    coords: list of tuples of (X, Y) coordinates, where top left is (0, 0)
    font_size: default 25
    color: default "black"
    """

    pic = Image.open(input_filename)
    drawer = ImageDraw.Draw(pic)
    font = ImageFont.truetype("calibri.ttf", font_size)
    image_copy_name = output_filename

    for label, coord in zip(labels, coords):
        # Draw centered
        drawer.text(coord, label, anchor="mm", align="center", font=font, fill=color)
    
    pic.save(output_filename)

def paste_images(input_filename, output_filename, images, coords, scale = 1):
    """
    Function to more easily paste smaller images on a bigger one in mass. Uses PIL
    Arguments:
    input_filename
    output_filename
    images: list of filenames of smaller images (can also just use 1 string)
    coords: list of tuples of (X, Y) coordinates, where top left is (0, 0). These
    will be the MIDDLE coordinates of where the small images go
    scale (int): Scale to resize the small image, default 1
    """

    # If a string is passed in, just duplicate it into a list
    if isinstance(images, str):
        images = [images for _ in range(len(coords))]

    bg = Image.open(input_filename)

    for image, coord in zip(images, coords):
        small = Image.open(image)

        # Scale up/down if needed
        if scale != 1:
            scale_w = int(scale * small.width)
            scale_h = int(scale * small.height)
            small = small.resize((scale_w, scale_h), Image.Resampling.NEAREST)

        # Derive top left coords from middle coords and small image size
        left_x = coord[0] - (small.width // 2)
        top_y = coord[1] - (small.height // 2)
        new_coord = (left_x, top_y)

        # Paste with transparency
        small = Image.alpha_composite(Image.new("RGBA", small.size), small.convert('RGBA'))
        bg.paste(small, new_coord, small)

    bg.save(output_filename)

def image_concat(image_list, output_filename, mode="v", bg_color = "white", cleanup = False):
    
    """
    Horizontally or vertically concatenates images

    images: list of image filenames
    output_filename: figure it out
    mode: either "v" for vertical or "h" for horizontal
    bg_color: string for valid HTML color like "white" or "black"
              (or RGB color tuple)
    cleanup: whether to delete the old images
    """
    images = [Image.open(i) for i in image_list]
    widths = [i.width for i in images]
    heights = [i.height for i in images]

    if mode == "v":
        bg_width = max(widths)
        bg_height = sum(heights)

        bg = Image.new("RGB", (bg_width, bg_height), bg_color)

        x_left, y_top = 0, 0
        for image in images:
            # Set x to be centered
            x_left = (bg_width - image.width) // 2
            # Paste w/ transparency
            image = Image.alpha_composite(Image.new("RGBA", image.size), image.convert('RGBA'))
            bg.paste(image, (x_left, y_top), image)
            # Accumulate y
            y_top = y_top + image.height

    elif mode == "h":
        bg_width = sum(widths)
        bg_height = max(heights)

        bg = Image.new("RGB", (bg_width, bg_height))

        x_left, y_top = 0, 0
        for image in images:
            # set y to be centered
            y_top = (bg_height - image.height) // 2
            # Paste w/ transparency
            image = Image.alpha_composite(Image.new("RGBA", image.size), image.convert('RGBA'))
            bg.paste(image, (x_left, y_top), image)
            # Accumulate x
            x_left = x_left + image.width

    else:
        raise ValueError("Invalid mode specified")
    
    bg.save(output_filename)
    if cleanup:
        for i in image_list:
            os.remove(i)
    
    print(f"Concatenated {image_list} into {output_filename}")

def upscale(in_name, out_name, factor = 2):

    image = Image.open(in_name)

    w = int(factor * image.width)
    h = int(factor * image.height)

    image = image.resize((w, h), Image.Resampling.BICUBIC)

    image.save(out_name)
    print(f"Upscaled {in_name} to {out_name}")

def svg2png(input_filename, output_filename, dpi=96):
    """
    Uses inkscape as a backend, requires it in PATH :/
    """

    print(f"Converting {input_filename} to {output_filename}...", end=" ")

    subprocess.run(["inkscape", 
                    '--export-type=png',
                    f'--export-dpi={dpi}',
                    f"--export-filename={output_filename}",
                    input_filename])
    os.remove(input_filename)
    
    print("Done")
