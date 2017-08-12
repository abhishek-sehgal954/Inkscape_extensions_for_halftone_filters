import numpy 
from PIL import Image, ImageDraw, ImageStat
import inkex
import simplestyle
import os
import common


def error_dispersion(image):
  arr = numpy.asarray(image)
  height = len(arr)
  width = len(arr[0])
  err = [[0]*len(arr[0]) for i in range(len(arr))]
  crr = numpy.zeros((len(arr),len(arr[0])))
  for i in range(height):
	for j in range(width):
	  if(arr[i][j] + err[i][j] < 128):
		crr[i][j] = 0 
	  else:
		crr[i][j] = 255
	  diff = arr[i][j] + err[i][j] - crr[i][j]
	  if(j+1 < width):
		err[i][j+1] = float(float(err[i][j+1]) + float(diff*float(float(7)/float(16))))
	  if(i+1 < height):
		err[i+1][j] = float(float(err[i+1][j]) + float(diff*float(float(5)/float(16))))
	  if(i+1 < height and j-1 >= 0):
		err[i+1][j-1] = float(float(err[i+1][j-1]) + float(diff*float(float(3)/float(16))))
	  if(i+1 < height and j+1 < width):
		err[i+1][j+1] = float(float(err[i+1][j+1]) + float(diff*float(float(1)/float(16))))
  return crr



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
				image = image.convert('L')
				data = error_dispersion(image)
				image = Image.fromarray(data)
				image = image.convert('RGB')
				common.save_image(image_node, image, img_format='PNG')

if __name__ == '__main__':
	obj = error_diffusion()
	obj.affect()

			