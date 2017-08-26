# Google/PSU Summer of Code 2017 project:

# Inkscape extensions for halftone filters

Copyright (c) 2017 abhishek-sehgal954

Mentoring Organization: Portland State University

Mentor: Bart Massey

Student: Abhishek Sehgal

This repository includes Inkscape extensions for some halftone filters.

How to run?

1. Copy .inx and .py file of the extension you want to use and paste it under the extension folder of inkscape. (Make sure you have also pasted common.py if you are using any Raster to Raster extension.) 
2. Open Inkscape
3. Open an image and select it.
4. Under Extensions menu, find desired submenu and select the desired algorithm.

![image1](https://user-images.githubusercontent.com/10050718/29738454-8a78ff76-8a40-11e7-918c-705d1067a91e.png)


## Submenu: Raster to Raster halftone 

1. Patterning
2. Ordered dithering
3. Error Diffusion
4. Newsprint filter

![image2](https://user-images.githubusercontent.com/10050718/29738469-c050773c-8a40-11e7-8cab-3c02f1c42f18.png)

## Submenu: Raster to vector(SVG) halftone

1. Clustered dot
2. Newsprint filter
3. Ordered dithering
4. Error diffusion

![image3](https://user-images.githubusercontent.com/10050718/29738474-dc3cc496-8a40-11e7-915a-c67506375ad4.png)

## Submenu : SVG to SVG halftone

1. Clustered dot
2. Newsprint filter
3. Ordered dithering
4. Error diffusion

![image4](https://user-images.githubusercontent.com/10050718/29738479-ec96c8fa-8a40-11e7-85e0-f543fcd70210.png)

## Halftone effect

### Original Image

![scenery](https://user-images.githubusercontent.com/10050718/29738486-1ac5d932-8a41-11e7-9675-8d50e1ceed35.jpg)

### Patterning

![patterning](https://user-images.githubusercontent.com/10050718/29738490-2f608432-8a41-11e7-982f-b0da47f5ca67.png)

### Ordered dithering

![ordered_dithering](https://user-images.githubusercontent.com/10050718/29738497-4549ba20-8a41-11e7-8023-755bc9cd6592.png)

### Error diffusion

![error_diffusion](https://user-images.githubusercontent.com/10050718/29738503-5e27fa52-8a41-11e7-9947-71dcd7ebb932.png)

### Clustered dot

![clustered_dot](https://user-images.githubusercontent.com/10050718/29738506-734f9cf0-8a41-11e7-9112-d58478f3f3f0.png)

### Newsprint filter

![newsprint_filter](https://user-images.githubusercontent.com/10050718/29738510-8588c3d8-8a41-11e7-8a25-6e0b8c784da0.png)


* Extension error diffusion and ordered dithering asks for desired width of the halftone image because of the size issue, and   height is calculated according to that width thus maintaining the aspect ratio.
* Make sure to change path in SVG to SVG extensions (both of inkscape location and a temporary location to save temporary png   file).


File common.py is a utility file which provides helper functions for raster images. It was developed under the terms of the GNU General Public License by su_v <suv-sf@users.sf.net>. Original file and other very helpful raster extension for inkscape can be found here: https://gitlab.com/su-v/inx-modifyimage/blob/master/src/image_lib/common.py

## License

This work is licensed under the "GNU General Public License v2.0". Please see the file LICENSE in the source distribution for license terms.




