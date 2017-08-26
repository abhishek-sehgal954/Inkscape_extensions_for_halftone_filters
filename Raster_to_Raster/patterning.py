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

def intensity(arr):
  #  calcluates intensity of a pixel from 0 to 9
  mini = 999
  maxi = 0
  for i in range(len(arr)):
    for j in range(len(arr[0])):
      maxi = max(arr[i][j],maxi)
      mini = min(arr[i][j],mini)
  level = float(float(maxi-mini)/float(10));
  brr = [[0]*len(arr[0]) for i in range(len(arr))]
  for i in range(10):
    l1 = mini+level*i
    l2 = l1+level
    for j in range(len(arr)):
      for k in range(len(arr[0])):
        if(arr[j][k] >= l1 and arr[j][k] <= l2):
          brr[j][k]=i
  return brr


def pattern(image):
    # based on the intensity maps pixel to the corresponding block of 3*3  
    #  ---   ---   ---   -X-   -XX   -XX   -XX   -XX   XXX   XXX
    #  ---   -X-   -XX   -XX   -XX   -XX   XXX   XXX   XXX   XXX
    #  ---   ---   ---   ---   ---   -X-   -X-   XX-   XX-   XXX
    #  9     8     7     6     5     4     3     2     1     0  
    #  X = 0
    #  - = 255
    #  Therefore intensity 0 being the blackest block.
  arr = numpy.asarray(image)
  brr=intensity(arr)
  gray_level = [[[0,0,0],[0,0,0],[0,0,0]] for i in range(10)]

  gray_level[0] = [[0,0,0],[0,0,0],[0,0,0]];
  gray_level[1] = [[0,255,0],[0,0,0],[0,0,0]];
  gray_level[2] = [[0,255,0],[0,0,0],[0,0,255]];
  gray_level[3] = [[255,255,0],[0,0,0],[0,0,255]];
  gray_level[4] = [[255,255,0],[0,0,0],[255,0,255]];
  gray_level[5] = [[255,255,255],[0,0,0],[255,0,255]];
  gray_level[6] = [[255,255,255],[0,0,255],[255,0,255]];
  gray_level[7] = [[255,255,255],[0,0,255],[255,255,255]];
  gray_level[8] = [[255,255,255],[255,0,255],[255,255,255]];
  gray_level[9] = [[255,255,255],[255,255,255],[255,255,255]];
  crr = numpy.zeros((len(arr)*3,len(arr[0])*3))
  cnt=0
  for i in range(len(brr)):
    cnt+=1
    for j in range(len(brr[i])):
      new_i = i+2*(i-1)
      new_j = j+2*(j-1)
      for k in range(3):
        for l in range(3):
          crr[new_i+k][new_j+l] = gray_level[brr[i][j]][k][l]
  return crr




class patterning(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
	def effect(self):
		image_node = None
		for node in self.selected.values():
			if(common.is_image(node)):
				image_node = node
			if image_node is not None:
				image = common.prep_image(image_node)
				image = image.convert('L')
				data = pattern(image)
				image = Image.fromarray(data)
				image = image.convert('RGB')
				common.save_image(image_node, image, img_format='PNG')

if __name__ == '__main__':
	obj = patterning()
	obj.affect()

			
