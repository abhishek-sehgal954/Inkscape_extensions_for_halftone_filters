"""Copyright (c) 2017 abhishek-sehgal954
    
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    """
import numpy 
from PIL import Image, ImageDraw, ImageStat
import inkex
import simplestyle
import os
import common


def error_dispersion(image_index, size):
   for y in range(0, size[1]-1):
    for x in range(1, size[0]-1):
      neighbour_index = image_index[x, y]
      if(neighbour_index>127) :
        image_index[x,y] = 255
      else :
        image_index[x,y] = 0
      diffused_error = neighbour_index - image_index[x, y]
      image_index[x+1, y] = int(image_index[x+1, y] + 7/16.0 * diffused_error)
      image_index[x-1, y+1] = int(image_index[x-1, y+1] + 3/16.0 * diffused_error)
      image_index[x,y+1] = int(image_index[x,   y+1] + 5/16.0 * diffused_error)
      image_index[x+1, y+1] =int(image_index[x+1, y+1] + 1/16.0 * diffused_error)

class error_diffusion(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
	def effect(self):
		image_node = None
		for node in self.selected.values():
			if(common.is_image(node)):
				image_node = node
			if image_node is not None:
				image = common.prep_image(image_node)
				image = image.convert('CMYK')
				image = image.split()
				for channel in image:
					error_dispersion(channel.load(), channel.size)
				image = Image.merge("CMYK", image).convert("RGB")
				common.save_image(image_node, image, img_format='PNG')
  
if __name__ == '__main__':
	obj = error_diffusion()
	obj.affect()
