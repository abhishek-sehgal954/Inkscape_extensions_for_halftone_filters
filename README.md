# Google/PSU Summer of Code 2017 project:

# Inkscape extensions for halftone filters

Mentoring Organization: Portland State University

Mentor: Bart Massey

Student: Abhishek Sehgal

This repository includes Inkscape extensions for some halftone filters.

# Submenu: Raster to Raster halftone 

How to run?

1. Copy all the files under extension folder of inkscape. 
2. Open Inkscape
3. Open a raster image and select it.
4. Under Extensions menu, find Raster to Raster submenu and select the desired algorithm.

Currently four extensions are added under Raster to Raster Halftone
1. Patterning
2. Ordered dithering
3. Error Diffusion
4. Newsprint filter.

More extensions will be added under submenu named Raster to SVG halftone and SVG to SVG halftone.

File common.py is a utility file which provides helper functions for raster images. It was developed under the terms of the GNU General Public License by su_v <suv-sf@users.sf.net>. Original file and other very helpful raster extension for inkscape can be found here: https://gitlab.com/su-v/inx-modifyimage/blob/master/src/image_lib/common.py




