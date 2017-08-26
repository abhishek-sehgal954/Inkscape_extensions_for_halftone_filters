import os
import sys
import base64
import StringIO
from urllib import url2pathname
from urlparse import urlparse
from PIL import Image, ImageDraw, ImageStat
import numpy as np


import inkex
import simplestyle


try:
    inkex.localize()
except:
    import gettext
    _ = gettext.gettext

try:
    from PIL import Image
except:
    inkex.errormsg(_(
        "The python module PIL is required for this extension.\n\n" +
        "Technical details:\n%s" % (e,)))
    sys.exit()


class raster_to_svg_error_diffusion(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

        self.OptionParser.add_option("-t", "--width",
                                     action="store", type="int",
                                     dest="width", default=200,
                                     help="this variable will be used to resize the original selected image to a width of whatever \
                                     you enter and height proportional to the new width, thus maintaining the aspect ratio")
        

    def getImagePath(self, node, xlink):
        
        absref = node.get(inkex.addNS('absref', 'sodipodi'))
        url = urlparse(xlink)
        href = url2pathname(url.path)

        path = ''
       
        if href is not None:
            path = os.path.realpath(href)
        if (not os.path.isfile(path)):
            if absref is not None:
                path = absref

        try:
            path = unicode(path, "utf-8")
        except TypeError:
            path = path

        if (not os.path.isfile(path)):
            inkex.errormsg(_(
                "No xlink:href or sodipodi:absref attributes found, " +
                "or they do not point to an existing file! Unable to find image file."))
            if path:
                inkex.errormsg(_("Sorry we could not locate %s") % str(path))
            return False

        if (os.path.isfile(path)):
            return path

    def getImageData(self, xlink):
        """
        Read, decode and return data of embedded image
        """
        comma = xlink.find(',')
        data = ''

        if comma > 0:
            data = base64.decodestring(xlink[comma:])
        else:
            inkex.errormsg(_("Failed to read embedded image data."))

        return data

    def getImage(self, node):
        """
        Parse link attribute of node and retrieve image data
        """
        xlink = node.get(inkex.addNS('href', 'xlink'))
        image = ''

        if xlink is None or xlink[:5] != 'data:':
            # linked bitmap image
            path = self.getImagePath(node, xlink)
            if path:
                image = Image.open(path)
        elif xlink[:4] == 'data':
            # embedded bitmap image
            data = self.getImageData(xlink)
            if data:
                image = Image.open(StringIO.StringIO(data))
        else:
            # unsupported type of link detected
            inkex.errormsg(_("Unsupported type of 'xlink:href'"))

        return image


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

    def draw_ellipse(self,(x, y), (r1,r2), color, parent, id_):
        
        style = {'stroke': 'none', 'stroke-width': '1', 'fill': color,"mix-blend-mode" : "multiply"}
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

    def diffusion(self, node):
        image = self.getImage(node)
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
            self.draw_rectangle((0,0),(basewidth,hsize),'white',pixel2svg_group,'id')
            cmyk = image.split()  
            output_cyan = self.error_dispersion(cmyk[0])
            output_magenta = self.error_dispersion(cmyk[1])
            output_yellow = self.error_dispersion(cmyk[2])
            self.draw_svg(output_cyan,'cyan',pixel2svg_group)
            self.draw_svg(output_magenta,'magenta',pixel2svg_group)
            self.draw_svg(output_yellow,'yellow',pixel2svg_group)
            nodeParent.remove(node)
        else:
            inkex.errormsg(_("Bailing out: No supported image file or data found"))
            sys.exit(1)

    def effect(self):
        found_image = False
        if (self.options.ids):
            for node in self.selected.itervalues():
                if node.tag == inkex.addNS('image', 'svg'):
                    found_image = True
                    self.diffusion(node)

        if not found_image:
            inkex.errormsg(_("Please select one or more bitmap image(s)"))
            sys.exit(0)
        


if __name__ =='__main__':
    e = raster_to_svg_error_diffusion()
    e.affect()
