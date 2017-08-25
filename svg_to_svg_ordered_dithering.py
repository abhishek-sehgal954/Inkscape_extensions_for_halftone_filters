import sys
import os
import re

import subprocess
import math
import numpy as np 

import inkex
import simpletransform
from PIL import Image, ImageStat, ImageDraw
import simplestyle
inkex.localize()

class ordered_dithering(inkex.Effect):

    def __init__(self):
        """Init the effect library and get options from gui."""
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-t", "--width",
                                     action="store", type="int",
                                     dest="width", default=200,
                                     help="this variable will be used to resize the original selected image to a width of whatever \
                                     you enter and height proportional to the new width, thus maintaining the aspect ratio")

    def effect(self):
        outfile = "/home/cic/Desktop/temp.png"
        curfile = self.args[-1]
        self.exportPage(curfile,outfile)

    def draw_rectangle(self,(x, y), (l,b), color, parent, id_):
        
        style = {'stroke': 'none', 'stroke-width': '1', 'fill': color,"mix-blend-mode" : "multiply"}
        attribs = {'style': simplestyle.formatStyle(style), 'x': str(x), 'y': str(y), 'width': str(l), 'height':str(b)}
        if id_ is not None:
            attribs.update({'id': id_})
        obj = inkex.etree.SubElement(parent, inkex.addNS('rect', 'svg'), attribs)
        return obj

    def draw_circle(self,(x, y), r, color, parent, id_):
        
        style = {'stroke': 'none', 'stroke-width': '1', 'fill': color,"mix-blend-mode" : "multiply"}
        attribs = {'style': simplestyle.formatStyle(style), 'cx': str(x), 'cy': str(y), 'r': str(r)}
        if id_ is not None:
            attribs.update({'id': id_})
        obj = inkex.etree.SubElement(parent, inkex.addNS('circle', 'svg'), attribs)
        return obj

    def draw_ellipse(self,(x, y), (r1,r2), color, parent, id_,transform):
        
        style = {'stroke': 'none', 'stroke-width': '1', 'fill': color,"mix-blend-mode" : "multiply"}
        if(transform == 1.5):
            attribs = {'style': simplestyle.formatStyle(style), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2)}
        elif(transform == 3):
            attribs = {'style': simplestyle.formatStyle(style), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2)}
        else:
            attribs = {'style': simplestyle.formatStyle(style), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2)}

        if id_ is not None:
            attribs.update({'id': id_})
        obj = inkex.etree.SubElement(parent, inkex.addNS('ellipse', 'svg'), attribs)
        return obj

    def draw_svg(self,output,parent):
        startu = 0
        endu = 0
        for i in range(len(output)):
            for j in range(len(output[i])):
                if (output[i][j]==0):
                    self.draw_circle((int((startu+startu+1)/2),int((endu+endu+1)/2)),1,'black',parent,'id')
                    #dwg.add(dwg.circle((int((startu+startu+1)/2),int((endu+endu+1)/2)),1,fill='black'))        
                startu = startu+2                                                                               
            endu = endu+2
            startu = 0

  #dwg.save() 
    def intensity(self,arr):
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

    def order_dither(self,image):
        arr = np.asarray(image)
        brr = self.intensity(arr)
        crr = [[8, 3, 4], [6, 1, 2], [7, 5, 9]]
        drr = np.zeros((len(arr),len(arr[0])))
        for i in range(len(arr)):
            for j in range(len(arr[0])):
                if(brr[i][j] > crr[i%3][j%3]):
                    drr[i][j] = 255
            else:
                drr[i][j] = 0
        return drr




   

                
                
    def dithering(self,node,image):
       
        

        if image:

            basewidth = self.options.width
            wpercent = (basewidth/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((basewidth,hsize), Image.ANTIALIAS)
            (width, height) = image.size
            if (1):

                
                nodeParent = node.getparent()
                nodeIndex = nodeParent.index(node)
                pixel2svg_group = inkex.etree.Element(inkex.addNS('g', 'svg'))
                pixel2svg_group.set('id', "%s_pixel2svg" % node.get('id'))
                nodeParent.insert(nodeIndex+1, pixel2svg_group)
                nodeParent.remove(node)

                
                
                
                image = image.convert("RGBA") # Convert this to RGBA if possible

                pixel_data = image.load()

                if image.mode == "RGBA":
 
                    for y in xrange(image.size[1]): # For each row ...
                        for x in xrange(image.size[0]): # Iterate through each column ...
      # Check if it's opaque
                            if pixel_data[x, y][3] < 255:
        # Replace the pixel data with the colour white
                                pixel_data[x, y] = (255, 255, 255, 255)


                image.thumbnail([image.size[0], image.size[1]], Image.ANTIALIAS)
                image = image.convert('L')
                self.draw_rectangle((0,0),(width,height),'white',pixel2svg_group,'id')
                output = self.order_dither(image)
                self.draw_svg(output,pixel2svg_group)


                

        else:
            inkex.errormsg(_("Bailing out: No supported image file or data found"))
            sys.exit(1)

    
        
    def exportPage(self, curfile, outfile):

        
        command = "/usr/bin/inkscape %s --export-png %s" %(curfile,outfile)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = p.wait()
        f = p.stdout
        err = p.stderr
        img = Image.open(outfile)
        

        if (self.options.ids):
            for node in self.selected.itervalues():
                found_image = True
                self.dithering(node,img)
         
        
def main():
    e = ordered_dithering()
    e.affect()
    exit()

if __name__=="__main__":
    main()
