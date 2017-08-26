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

class error_diffusion(inkex.Effect):

    def __init__(self):
        """Init the effect library and get options from gui."""
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-t", "--width",
                                     action="store", type="int",
                                     dest="width", default=200,
                                     help="this variable will be used to resize the original selected image to a width of whatever \
                                     you enter and height proportional to the new width, thus maintaining the aspect ratio")
        self.OptionParser.add_option("--inkscape_path",    action="store", type="string",  dest="inkscape_path",    default="",        help="")
        self.OptionParser.add_option("--temp_path",    action="store", type="string",  dest="temp_path",    default="",        help="")

    def effect(self):
        outfile = self.options.temp_path
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

    def draw_svg(self,output,color,parent):
        startu = 0
        endu = 0
        for i in range(len(output)):
            for j in range(len(output[i])):
                if (output[i][j]==0):
                    self.draw_circle((int((startu+startu+1)/2),int((endu+endu+1)/2)),1,color,parent,'id')
                    #dwg.add(dwg.circle((int((startu+startu+1)/2),int((endu+endu+1)/2)),1,fill=color,style="mix-blend-mode: multiply;"))        
                startu = startu+2                                                                               
            endu = endu+2
            startu = 0

    def error_dispersion(self,image):
        arr = np.asarray(image)
        height = len(arr)
        width = len(arr[0])
        err = [[0]*len(arr[0]) for i in range(len(arr))]
        crr = np.zeros((len(arr),len(arr[0])))
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

                
                
    def diffusion(self,node,image):
        if image:
            basewidth = self.options.width
            wpercent = (basewidth/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((basewidth,hsize), Image.ANTIALIAS)
            (width, height) = image.size
            nodeParent = node.getparent()
            nodeIndex = nodeParent.index(node)
            pixel2svg_group = inkex.etree.Element(inkex.addNS('g', 'svg'))
            pixel2svg_group.set('id', "%s_pixel2svg" % node.get('id'))
            nodeParent.insert(nodeIndex+1, pixel2svg_group)
            nodeParent.remove(node)
            self.draw_rectangle((0,0),(width,height),'white',pixel2svg_group,'id')
            image = image.convert("RGBA") 
            pixel_data = image.load()
            if image.mode == "RGBA":
             for y in xrange(image.size[1]):                         
                for x in xrange(image.size[0]): 
                    if pixel_data[x, y][3] < 255:
                        pixel_data[x, y] = (255, 255, 255, 255)
            image.thumbnail([image.size[0], image.size[1]], Image.ANTIALIAS)
            cmyk = image.split()  
            output_cyan = self.error_dispersion(cmyk[0])
            output_magenta = self.error_dispersion(cmyk[1])
            output_yellow = self.error_dispersion(cmyk[2])
            self.draw_svg(output_cyan,'cyan',pixel2svg_group)
            self.draw_svg(output_magenta,'magenta',pixel2svg_group)
            self.draw_svg(output_yellow,'yellow',pixel2svg_group)
        else:
            inkex.errormsg(_("Bailing out: No supported image file or data found"))
            sys.exit(1)

    
        
    def exportPage(self, curfile, outfile):
        command = "%s %s --export-png %s" %(self.options.inkscape_path,curfile,outfile)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = p.wait()
        f = p.stdout
        err = p.stderr
        img = Image.open(outfile)
        

        if (self.options.ids):
            for node in self.selected.itervalues():
                found_image = True
                self.diffusion(node,img)
         
        
def main():
    e = error_diffusion()
    e.affect()
    exit()

if __name__=="__main__":
    main()
