import sys
import os
import re

import subprocess
import math

import inkex
import simpletransform
from PIL import Image, ImageStat, ImageDraw
import simplestyle
inkex.localize()

class newsprint_filter(inkex.Effect):

    def __init__(self):
        """Init the effect library and get options from gui."""
        inkex.Effect.__init__(self)

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
            attribs = {'style': simplestyle.formatStyle(style), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2),'transform': 'rotate(1.5)'}
        elif(transform == 3):
            attribs = {'style': simplestyle.formatStyle(style), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2),'transform': 'rotate(3)'}
        else:
            attribs = {'style': simplestyle.formatStyle(style), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2),'transform': 'rotate(0)'}

        if id_ is not None:
            attribs.update({'id': id_})
        obj = inkex.etree.SubElement(parent, inkex.addNS('ellipse', 'svg'), attribs)
        return obj

    def gcr(self,im, percentage):
        cmyk_im = im.convert('CMYK')
        if not percentage:
            return cmyk_im
        cmyk_im = cmyk_im.split()
        cmyk = []
        for i in xrange(4):
            cmyk.append(cmyk_im[i].load())
        for x in xrange(im.size[0]):
            for y in xrange(im.size[1]):
                gray = min(cmyk[0][x,y], cmyk[1][x,y], cmyk[2][x,y]) * percentage / 100
                for i in xrange(3):
                    cmyk[i][x,y] = cmyk[i][x,y] - gray
                cmyk[3][x,y] = gray
        return Image.merge('CMYK', cmyk_im)

    def halftone(self,parent,im, cmyk, sample, scale,):
        #inkex.errormsg(_("ykbh2"))


        dots = []
        angle = 0 
        count = 0
        cmyk = cmyk.split()
        for channel in cmyk:
            count=count+1

        #channel = channel.rotate(angle, expand=1)
            size = channel.size[0]*scale, channel.size[1]*scale
        #half_tone = Image.new('L', size)
        #draw = ImageDraw.Draw(half_tone)
            for x in xrange(0, channel.size[0], sample):
                for y in xrange(0, channel.size[1], sample):
                    box = channel.crop((x, y, x + sample, y + sample))
                    stat = ImageStat.Stat(box)
                    diameter = (stat.mean[0] / 255)**0.5
                    edge = 0.5*(1-diameter)
                    x_pos, y_pos = (x+edge)*scale, (y+edge)*scale
                    box_edge = sample*diameter*scale
                    if(count==1):
                        self.draw_ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),'cyan',parent,'id',0)
                        #dwg.add(dwg.ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),fill='cyan',style="mix-blend-mode: multiply;")) 
                    elif(count==2):
                        self.draw_ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),'magenta',parent,'id',1.5)
                        #dwg.add(dwg.ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),fill='magenta',style="mix-blend-mode: multiply;",transform = ("rotate(1.5)")))
                    elif(count==3):
                        self.draw_ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),'yellow',parent,'id',3)
                        #dwg.add(dwg.ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),fill='yellow',style="mix-blend-mode: multiply;",transform = ("rotate(3)")))
                
                
    def newsprint(self,node,image):
       
        

        if image:
            

            (width, height) = image.size
            if (1):

                
                nodeParent = node.getparent()
                nodeIndex = nodeParent.index(node)
                pixel2svg_group = inkex.etree.Element(inkex.addNS('g', 'svg'))
                pixel2svg_group.set('id', "%s_pixel2svg" % node.get('id'))
                nodeParent.insert(nodeIndex+1, pixel2svg_group)
                nodeParent.remove(node)

                
                
                self.draw_rectangle((0,0),(width,height),'white',pixel2svg_group,'id')
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


                cmyk = self.gcr(image,0)
                self.halftone(pixel2svg_group,image,cmyk,10,1)


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
                self.newsprint(node,img)
         
        
def main():
    e = newsprint_filter()
    e.affect()
    exit()

if __name__=="__main__":
    main()
