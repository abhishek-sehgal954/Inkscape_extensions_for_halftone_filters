#!/usr/bin/env python
"""
image_lib.common - Common utility functions and base classes for
                   image-modifying extensions

Copyright (C) 2015-2016, su_v <suv-sf@users.sf.net>

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
# pylint: disable=global-statement
# pylint: disable=unused-import
# pylint: disable=wrong-import-order
# pylint: disable=wrong-import-position
# pylint: disable=ungrouped-imports
# pylint: disable=too-many-lines

# standard library
import os
import sys
import base64
try:
    # Python 2
    import StringIO
    from urllib import url2pathname
    from urlparse import urlparse
except ImportError:
    # Python 3
    # pylint: disable=import-error
    # pylint: disable=no-name-in-module
    from io import BytesIO
    from urllib.request import url2pathname
    from urllib.parse import urlparse
import re

# compat
import six

# local library
import inkex
import cubicsuperpath
import image_lib.transform as mat


try:
    inkex.localize()
except AttributeError:
    import gettext
    _ = gettext.gettext


# Global "constants"
WAND_MIN_REQ = (0, 4, 1)
NO_MODULE = _("No suitable Python Imaging module found!")
SVG_SHAPES = ('rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon')
HAVE_WAND = False
HAVE_PIL = False
HAVE_NUMPY = False
PIL_EXIF_TAGS = {}
# FIXME: Globals which may change
DEBUG = False
USE_WAND = False
USE_PIL = False


def check_version(cur_ver, min_ver):
    """Check current version against min required version."""
    # TODO: simplify and generalize version check
    if len(cur_ver) >= 3 and len(min_ver) >= 3:
        if cur_ver[0] > min_ver[0]:
            return True
        elif cur_ver[0] == min_ver[0]:
            if cur_ver[1] > min_ver[1]:
                return True
            elif cur_ver[1] == min_ver[1]:
                if cur_ver[2] >= min_ver[2]:
                    return True
    return False


try:
    from wand.version import VERSION_INFO as WAND_VERSION_INFO
    if check_version(WAND_VERSION_INFO, WAND_MIN_REQ):
        from wand.image import Image as ImageWand
        from wand.color import Color as ColorWand
        HAVE_WAND = True
except ImportError as error_msg:
    pass


try:
    from PIL import Image as ImagePIL
    HAVE_PIL = True
except ImportError as error_msg:
    pass


if HAVE_PIL:
    try:
        from PIL.ExifTags import TAGS as PIL_EXIF_TAGS
    except ImportError as error_msg:
        pass


try:
    import numpy
    HAVE_NUMPY = True
except ImportError as error_msg:
    pass


if HAVE_WAND:
    USE_WAND = True
    USE_PIL = False
elif HAVE_PIL:
    USE_WAND = False
    USE_PIL = True
else:  # if not HAVE_PIL and not HAVE_WAND:
    raise RuntimeError(NO_MODULE)


def report_imaging_module(message):
    """Report currently used Python Imaging module."""
    if USE_PIL:
        inkex.errormsg('{}: using PIL.'.format(message))
    elif USE_WAND:
        inkex.errormsg('{}: using Wand.'.format(message))


def select_imaging_module(module):
    """Switch Python Imaging module based on argument.

    Verify availability of selected module and notify user if the
    selected module is not available.
    """
    global USE_WAND
    global USE_PIL
    not_available = _("Selected python imaging module is not available")
    if module == "wand" or module == "Wand":
        if HAVE_WAND:
            USE_WAND = True
            USE_PIL = False
            if DEBUG:
                inkex.debug('Setting imaging module to {}.'.format(module))
        else:
            inkex.errormsg('{0}: {1}'.format(not_available, module))
    elif module == 'pil' or module == 'PIL':
        if HAVE_PIL:
            USE_WAND = False
            USE_PIL = True
            if DEBUG:
                inkex.debug('Setting imaging module to {}.'.format(module))
        else:
            inkex.errormsg('{0}: {1}'.format(not_available, module))
    elif module == 'default':
        pass
    else:
        inkex.errormsg('{0}: {1}'.format(not_available, module))


def showme(msg):
    """Print debug output only if global DEBUG variable is set."""
    if DEBUG:
        inkex.debug(msg)


# Utiliy functions for selection checking

def zSort(inNode, idList):
    """Z-sort selected objects, return list of IDs."""
    # pylint: disable=invalid-name
    # TODO: include function in shared module simpletransform.py
    sortedList = []
    theid = inNode.get("id")
    if theid in idList:
        sortedList.append(theid)
    for child in inNode:
        if len(sortedList) == len(idList):
            break
        sortedList += zSort(child, idList)
    return sortedList


def is_group(node):
    """Check node for group tag."""
    return node.tag == inkex.addNS('g', 'svg')


def is_path(node):
    """Check node for path tag."""
    return node.tag == inkex.addNS('path', 'svg')


def is_basic_shape(node):
    """Check node for SVG basic shape tag."""
    return node.tag in (inkex.addNS(tag, 'svg') for tag in SVG_SHAPES)


def is_custom_shape(node):
    """Check node for Inkscape custom shape type."""
    return inkex.addNS('type', 'sodipodi') in node.attrib


def is_shape(node):
    """Check node for SVG basic shape tag or Inkscape custom shape type."""
    return is_basic_shape(node) or is_custom_shape(node)


def has_path_effect(node):
    """Check node for Inkscape path-effect attribute."""
    return inkex.addNS('path-effect', 'inkscape') in node.attrib


def is_modifiable_path(node):
    """Check node for editable path data."""
    return is_path(node) and not (has_path_effect(node) or
                                  is_custom_shape(node))


def is_rect(node):
    """Check node for rect tag."""
    return node.tag == inkex.addNS('rect', 'svg')


def is_image(node):
    """Check node for image tag."""
    return node.tag == inkex.addNS('image', 'svg')


def is_clipped(node):
    """Return value of clip-path attribute (fallback: None)."""
    clip_path = node.get('clip-path')
    return clip_path != 'none' and clip_path is not None


def is_clip_path(node):
    """Check node for clipPath tag."""
    return node.tag == inkex.addNS('clipPath', 'svg')


# Utiliy functions for image loading and saving

def create_img_node():
    """Create a new <image> node, without any data yet."""
    node = inkex.etree.Element(inkex.addNS('image', 'svg'))
    node.set('x', "0")
    node.set('y', "0")
    node.set('preserveAspectRatio', "none")
    node.set('image-rendering', "optimizeSpeed")
    return node


def create_img_placeholder(img_node):
    """Insert new path based on geometry of <image> node."""
    image_d = 'm {0},{1} h {2} v {3} h -{2} z'.format(img_node.get('x'),
                                                      img_node.get('y'),
                                                      img_node.get('width'),
                                                      img_node.get('height'))
    path = inkex.etree.Element(inkex.addNS('path', 'svg'))
    path.set('d', image_d)
    path.set('style', "fill:none;stroke:none")
    path.set('transform', img_node.get('transform', ""))
    index = img_node.getparent().index(img_node)
    img_node.getparent().insert(index, path)
    return path


def get_image_path(node, xlink):
    """Find image file, return path."""
    # pylint: disable=redefined-variable-type
    path = None
    absref = node.get(inkex.addNS('absref', 'sodipodi'))
    url = urlparse(xlink)
    href = url2pathname(url.path)
    if href is not None:
        path = os.path.realpath(href)
    if not os.path.isfile(path):
        if absref is not None:
            path = absref
    try:
        # FIXME (pylint): Redefinition of path type from str to unicode
        #                 (redefined-variable-type)
        if sys.version_info < (3,):
            path = unicode(path, "utf-8")                                       # pylint: disable=undefined-variable
        else:
            path = str(path, "utf-8")
    except TypeError:
        pass
    if not os.path.isfile(path):
        inkex.errormsg(_(
            "No xlink:href or sodipodi:absref attributes found, " +
            "or they do not point to an existing file! " +
            "Unable to find image file."))
        if path:
            inkex.errormsg(_("Sorry we could not locate %s") % str(path))
        return None
    else:  # if os.path.isfile(path)
        return path


def get_image_data(xlink):
    """Read, decode and return data of embedded image."""
    data = None
    comma = xlink.find(',')
    if comma > 0:
        if sys.version_info < (3,):
            data = base64.decodestring(xlink[comma:])                           # pylint: disable=deprecated-method
        else:
            data = base64.decodebytes(bytes(xlink[comma:], 'ascii'))            # pylint: disable=no-member
    else:
        inkex.errormsg(_("Failed to read embedded image data."))
    return data


def get_image_path_or_buffer(node):
    """Parse link attribute of node, return image path or buffer."""
    # pylint: disable=too-many-branches
    xlink = node.get(inkex.addNS('href', 'xlink'))
    if xlink is None or xlink[:5] != 'data:':
        return {'path': get_image_path(node, xlink)}
    elif xlink[:4] == 'data':
        return {'buf': get_image_data(xlink)}
    else:
        inkex.errormsg(_("Unsupported type of 'xlink:href'"))
        return {}


def get_image(node):
    """Parse link attribute of node and retrieve image data."""
    # pylint: disable=too-many-branches
    image = None
    xlink = node.get(inkex.addNS('href', 'xlink'))
    if xlink is None or xlink[:5] != 'data:':
        path = get_image_path(node, xlink)
        if path is not None:
            if USE_WAND:
                image = ImageWand(filename=path)
            elif USE_PIL:
                image = ImagePIL.open(path)
            else:
                raise RuntimeError(NO_MODULE)
    elif xlink[:4] == 'data':
        data = get_image_data(xlink)
        if data:
            if sys.version_info < (3,):
                img_data = StringIO.StringIO(data)
            else:
                img_data = BytesIO(data)
            if USE_WAND:
                image = ImageWand(blob=img_data)
            elif USE_PIL:
                image = ImagePIL.open(img_data)
            else:
                raise RuntimeError(NO_MODULE)
    else:
        inkex.errormsg(_("Unsupported type of 'xlink:href'"))
    return image


def prep_image(node, add_alpha=False):
    """Prepare bitmap image for modification (image data, image mode)."""
    # pylint: disable=no-member
    image = None
    if is_image(node):
        image = get_image(node)
        if add_alpha:
            if USE_WAND:
                image.alpha_channel = True
            elif USE_PIL:
                if image.mode is not 'RGBA':
                    image_rgba = ImagePIL.new('RGBA', image.size)
                    image_rgba.paste(image)
                    image = image_rgba.copy()
                    image_rgba.close()
            else:
                raise RuntimeError(NO_MODULE)
    return image


def save_image(img_node, image, img_format='PNG'):
    """Write image data as base64-encoded string to the href attribute."""
    if is_image(img_node):
        if sys.version_info < (3,):
            outstring = StringIO.StringIO()
        else:
            outstring = BytesIO()
        if USE_WAND:
            if img_format != "keep":
                image.format = img_format
            else:
                img_format = image.format
            image.save(file=outstring)
        elif USE_PIL:
            image.save(outstring, img_format)
        else:
            raise RuntimeError(NO_MODULE)
        if sys.version_info < (3,):
            outstring_base64 = base64.encodestring(outstring.getvalue())        # pylint: disable=deprecated-method
        else:
            outstring_base64 = str(                                             # pylint: disable=redefined-variable-type
                base64.encodebytes(outstring.getvalue()),                       # pylint: disable=no-member
                'ascii')
        href_head = 'data:image/{0};'.format(img_format.lower())
        href_data = 'base64,{0}'.format(outstring_base64)
        img_node.set(inkex.addNS('href', 'xlink'), href_head + href_data)
        outstring.close()


def get_image_scale(image, img_node):
    """Return image scale (image pixel size : <image> node size)."""
    scale_x = scale_y = 1.0
    if image is not None and is_image(img_node):
        scale_x = image.size[0] / float(img_node.get('width', image.size[0]))
        scale_y = image.size[1] / float(img_node.get('height', image.size[1]))
    return (scale_x, scale_y)


def check_req(img_node, path, nodes=4, subs=1, alpha=False):
    """Check helper path and image requirements, return csp path, image.

    Helper path:
        Check number of sub-paths
        Check node count (per sub-path)

    Image:
        Check if retrieving image data succeeded.
    """
    image = None
    dest = cubicsuperpath.parsePath(path.get('d'))
    req_nodes = _("Number of required nodes per sub-path for this method")
    req_len = _("All sub-paths must have the same number of nodes.")
    req_subs = _("Number of required sub-paths for this method")
    req_image = _("Failed to read image data.")
    if len(dest) == subs:
        dest_ok = True
        for i in range(subs):
            if len(dest[i]) < nodes:
                inkex.errormsg('{0}: {1}'.format(req_nodes, nodes))
                dest_ok = False
            elif len(dest[i]) != len(dest[0]):
                inkex.errormsg(req_len)
                dest_ok = False
        if not dest_ok:
            dest = None
    else:
        inkex.errormsg('{0}: {1}'.format(req_subs, subs))
        dest = None
    if dest is not None:
        image = prep_image(img_node, alpha)
    if image is None:
        if dest is not None:
            inkex.errormsg(req_image)
    return image, dest


def image_info(img):
    """Show information retrieved from image data."""
    # pylint: disable=protected-access
    if USE_WAND:
        inkex.debug('Size:\t\t\t{} x {}'.format(int(img.size[0]),
                                                int(img.size[1])))
        inkex.debug('Format:\t\t{}'.format(img.format))
        inkex.debug('Mimetype:\t\t{}'.format(img.mimetype))
        inkex.debug('Alpha channel:\t{}'.format(img.alpha_channel))
        inkex.debug('Background:\t{}'.format(img.background_color))
        inkex.debug('Matte color:\t{}'.format(img.matte_color))
        inkex.debug('VirtualPixel:\t{}'.format(img.virtual_pixel))
        inkex.debug('Colorspace:\t{}'.format(img.colorspace))
        inkex.debug('Depth:\t\t{}'.format(img.depth))
        inkex.debug('Orientation:\t{}'.format(img.orientation))
        inkex.debug('Resolution:\t{}'.format(img.resolution))
        inkex.debug('Type:\t\t{}'.format(img.type))
        inkex.debug('Units:\t\t{}'.format(img.units))
        if hasattr(img, 'metadata'):
            inkex.debug('\nMetadata:')
            for key, value in img.metadata.items():
                inkex.debug('\t{}: {}'.format(key, value))
    elif USE_PIL:
        inkex.debug('Size:\t\t\t{} x {}'.format(int(img.size[0]),
                                                int(img.size[1])))
        inkex.debug('Format:\t\t{}'.format(img.format))
        inkex.debug('Mode:\t\t{}'.format(img.mode))
        if hasattr(img, 'info'):
            inkex.debug('\nInfo:')
            for key, value in img.info.items():
                if key != "exif":
                    # TODO: strings need attention (e.g. icc_profile)
                    if isinstance(value, str):
                        tagval = tuple(ord(c) for c in value)
                    else:
                        tagval = value
                    inkex.debug('\t{}: {}'.format(key, tagval))
        if hasattr(img, '_getexif'):
            inkex.debug('\nExif:')
            exif = img._getexif()
            if exif is not None:
                for (key, value) in six.iteritems(exif):
                    if PIL_EXIF_TAGS and key in PIL_EXIF_TAGS.keys():
                        # TODO: more value formatting for PIL?
                        if isinstance(value, str):
                            tagval = tuple(ord(c) for c in value)
                        else:
                            tagval = value
                        inkex.debug('\t{}: {}'.format(PIL_EXIF_TAGS.get(key),
                                                      tagval))
    else:
        raise RuntimeError(NO_MODULE)


# Utiliy functions for wrapping the result

def wrap_group(node):
    """Wrap node in group, return group."""
    group = inkex.etree.Element(inkex.addNS('g', 'svg'))
    index = node.getparent().index(node)
    node.getparent().insert(index, group)
    group.append(node)
    return group


def group_with(node, path):
    """Put path into group wrapped around node, return group."""
    group = wrap_group(node)
    if group is not None:
        mat.apply_absolute_diff(node, path)
        group.append(path)
    return group


# Utility functions for transforms

def mat_path_to_img_node(path, img_node, fit=False):
    """Return mat which transforms from path to img_node coords."""
    # 1 apply path transform
    # 2 apply path parent transform
    # 3 reverse img_node parent transform
    mat1 = mat.copy_from(path) if not fit else mat.ident_mat()
    mat2 = mat.absolute(path.getparent())
    mat3 = mat.invert(mat.absolute(img_node.getparent()))
    return mat.compose_triplemat(mat1, mat2, mat3)


def mat_img_node_to_image(img_node, image, fit=False):
    """Return mat which transforms from img_node to image coords."""
    # 1 reverse img_node transform
    # 2 if not fit: reverse img_node offset
    # 3 scale
    mat1 = mat.invert(mat.copy_from(img_node))
    mat2 = mat.invert(mat.offset(img_node)) if not fit else mat.ident_mat()
    mat3 = mat.scale(*get_image_scale(image, img_node))
    return mat.compose_triplemat(mat1, mat2, mat3)


def mat_image_to_img_node(image, img_node, fit=False):
    """Return mat which transforms from image to img_node coords."""
    # 1 scale
    # 2 if not fit: apply img_node offset
    # 3 apply img_node transform
    mat1 = mat.invert(mat.scale(*get_image_scale(image, img_node)))
    mat2 = mat.offset(img_node) if not fit else mat.ident_mat()
    mat3 = mat.copy_from(img_node)
    return mat.compose_triplemat(mat1, mat2, mat3)


def mat_img_node_to_path(img_node, path, fit=False):
    """Return mat which transforms from img_node to path coords."""
    # 1 apply img_node parent transform
    # 2 reverse path parent transform
    # 3 ??? reverse path transform
    mat1 = mat.absolute(img_node.getparent())
    mat2 = mat.invert(mat.absolute(path.getparent()))
    # TODO: verify mat3 for fit option
    mat3 = mat.invert(mat.copy_from(path)) if not fit else mat.ident_mat()
    return mat.compose_triplemat(mat1, mat2, mat3)


# Compensate / apply preserved and parent transforms of helper paths and images
# Note: parameter 'fit' currently only used by image_perspective.py

def transform_path_to_image(path, img_node, image, fit=False):
    """Return mat which transforms from path to image coords."""
    # 1 path to img_node
    # 2 img_node to image
    mat1 = mat_path_to_img_node(path, img_node, fit)
    mat2 = mat_img_node_to_image(img_node, image, fit)
    return mat.compose_doublemat(mat2, mat1)


def transform_image_to_path(image, img_node, path, fit=False):
    """Return mat which transforms from image to path coords."""
    # 1 image to img_node
    # 2 img_node to path
    mat1 = mat_image_to_img_node(image, img_node, fit)
    mat2 = mat_img_node_to_path(img_node, path, fit)
    return mat.compose_doublemat(mat2, mat1)


# specific helper functions

def combine_two_paths(path0_path1):
    """Combine two paths into a new one.

    Combine the transformed csp representations as sub-paths, insert
    new path element with path data from csp path into document and
    return the etree element.
    """
    path0, path1 = path0_path1
    csp = []
    for path in (path0, path1):
        csp_path = cubicsuperpath.parsePath(path.get('d'))
        mat.apply_to(mat.copy_from(path), csp_path)
        csp.append(csp_path)
    # transform path1 into path0 coords
    mat.apply_to(mat.absolute_diff(path0, path1), csp[1])
    # compensate preserved transform of path0 in csp1
    mat.apply_to(mat.invert(mat.copy_from(path0)), csp[1])
    # combine the two csp paths (append csp1 as sub-path to csp0)
    csp[0].append(csp[1][0])
    # insert as new path into document
    path = inkex.etree.Element(inkex.addNS('path', 'svg'))
    path.set('d', cubicsuperpath.formatPath(csp[0]))
    # insert before source path
    index = path0.getparent().index(path0)
    path0.getparent().insert(index, path)
    # return new path
    return path


def combine_many_paths(path_list):
    """Combine paths in path_list to single compound path."""
    if len(path_list):
        csp = []
        first = path_list[0]
        for path in path_list:
            csp_path = cubicsuperpath.parsePath(path.get('d'))
            mat.apply_to(mat.copy_from(path), csp_path)
            if path == first:
                csp.append(csp_path)
            else:
                # transform csp_path into first coords
                mat.apply_to(mat.absolute_diff(first, path), csp_path)
                # compensate preserved transform of first in csp_path
                mat.apply_to(mat.invert(mat.copy_from(first)), csp_path)
                csp[0].append(csp_path[0])
        # insert as new path into document
        path = inkex.etree.Element(inkex.addNS('path', 'svg'))
        path.set('d', cubicsuperpath.formatPath(csp[0]))
        # insert before source path
        index = first.getparent().index(first)
        first.getparent().insert(index, path)
        # return new path
        return path
    else:
        return None


def rect_to_d(node):
    """Return 'd' path parameter for rect."""
    if is_rect(node):
        rect_x = float(node.get('x', 0))
        rect_y = float(node.get('y', 0))
        rect_w = float(node.get('width', 0))
        rect_h = float(node.get('height', 0))
        return 'M {0},{1} {2},{3} {4},{5} {6},{7}'.format(
            rect_x, rect_y,
            rect_x + rect_w, rect_y,
            rect_x + rect_w, rect_y + rect_h,
            rect_x, rect_y + rect_h)


def csp_to_path(csp, fill="blue", opacity=0.5):
    """Draw a path from csp and append to parent."""
    path = inkex.etree.Element(inkex.addNS('path', 'svg'))
    path.set('d', cubicsuperpath.formatPath(csp))
    path.set('style', 'fill:{0};opacity:{1}'.format(fill, str(opacity)))
    return path


def csp_to_bbox(csp, parent):
    """Return simpletransform geom bbox of csp path."""
    clip_path = inkex.etree.Element(inkex.addNS('path', 'svg'))
    parent.append(clip_path)
    clip_path.set('d', cubicsuperpath.formatPath(csp))
    clip_bbox = mat.st.computeBBox([clip_path])
    parent.remove(clip_path)
    return clip_bbox


def csp_to_points(dest, sub, points):
    """Convert csp path into a list of nodes without control points."""
    if points is None:
        points = len(dest[sub])
    return [[(csp[1][0], csp[1][1]) for csp in subs]
            for subs in dest][sub][:points]


def get_clip_bbox_csp(clip_path_def, cmat=None):
    """Return bbox of clipPath element in csp notation."""
    if cmat is None:
        cmat = mat.ident_mat()
    clip_bbox = None
    clip_path_csp = None
    if clip_path_def is not None:
        clip_bbox = mat.st.computeBBox(clip_path_def.getchildren(), cmat)
    if clip_bbox is not None:
        clip_path_csp = cubicsuperpath.parsePath(
            'm {0},{1} h {2} v {3} h -{2}'.format(
                clip_bbox[0], clip_bbox[2],
                clip_bbox[1] - clip_bbox[0],
                clip_bbox[3] - clip_bbox[2]))
        mat.apply_copy_from(clip_path_def, clip_path_csp)
    return clip_path_csp


def draw_cropbox(node, cropbox_csp):
    """Draw crop box and insert after cropped image."""
    cropbox = csp_to_path(cropbox_csp)
    index = node.getparent().index(node)
    node.getparent().insert(index+1, cropbox)
    mat.apply_copy_from(node, cropbox)
    return cropbox


def find_perspective_coeffs(pb, pa):
    """Calculate and return perspective coefficients.

    Based on formula from <http://stackoverflow.com/a/14178717>.
    """
    # pylint: disable=invalid-name
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
    A = numpy.matrix(matrix, dtype=numpy.float)
    B = numpy.array(pb).reshape(8)
    res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
    return numpy.array(res).reshape(8)


# Effect classes

class ImageModifier(inkex.Effect):
    """ImageModifier class for modifying the content of bitmap images."""

    def __init__(self):
        """Init base class, add default options for ImageModifier class."""
        inkex.Effect.__init__(self)
        # wand / ImageMagick
        
        # strings
        self.not_with_pil = _(
            "This operation is not available with PIL.")
        self.not_with_wand = _(
            "This operation is not available with Wand.")
        self.requires_numpy = _(
            "This image transformation with PIL requires numpy.")

    def get_defs(self):
        """Return <defs> element.

        Create node if not already present in self.document.
        """
        defs = self.document.getroot().find(inkex.addNS('defs', 'svg'))
        if defs is None:
            defs = inkex.etree.SubElement(self.document.getroot(),
                                          inkex.addNS('defs', 'svg'))
        return defs

    def get_clip_path(self, node):
        """Return clipPath element."""
        match = re.search(r'url\(\#(.*)\)', node.get('clip-path', ""))
        if match is not None:
            linked_node = self.getElementById(match.group(1))
            if linked_node is not None:
                if is_clip_path(linked_node):
                    return linked_node

    def get_clip_def(self, node, parents=False):
        """Return clip-path from node or node's ancestor(s)."""
        if is_clipped(node):
            return (node, self.get_clip_path(node))
        elif parents:
            if node.getparent() is not None:
                return self.get_clip_def(node.getparent(), parents)
        return (node, None)

    def get_clip_geom(self, node, parents=False):
        """Return clipped node and clip bbox as csp (quadrilateral)."""
        clip_base = node
        clip_path_csp = None
        clipped_node, clip_path_def = self.get_clip_def(node, parents)
        if clip_path_def is not None:
            clip_path_units = clip_path_def.get('clipPathUnits')
            if clipped_node == clip_base:
                if clip_path_units == 'objectBoundingBox':
                    # TODO: implement support for 'objectBoundingBox'
                    # 1. get geom box of clipped object (clip_base)
                    # 2. convert into a matrix transformation
                    # 3. pass matrix as cmat to get_clip_bbox_csp()
                    # until implemented, fall back to:
                    cmat = mat.ident_mat()
                else:
                    cmat = mat.ident_mat()
            else:
                if clip_path_units == 'objectBoundingBox':
                    # TODO: implement support for 'objectBoundingBox'
                    # 1. get geom box of clipped group (clipped_node)
                    # 2. convert into a matrix transformation
                    # 3. compose with cmat (see below)
                    # 4. pass cmat to get_clip_bbox_csp()
                    # until implemented, fall back to:
                    umat = mat.ident_mat()
                else:
                    umat = mat.ident_mat()
                # compensate preserved transforms on nested groups
                pmat = mat.compose_triplemat(
                    mat.copy_from(clipped_node),
                    mat.absolute_diff(clip_base, clipped_node),
                    mat.invert(mat.copy_from(clip_base)))
                # finally, compose with matrix for clipPathUnits
                # TODO: once we have real umat, check compose order!
                cmat = mat.compose_doublemat(umat, pmat)
            clip_path_csp = get_clip_bbox_csp(clip_path_def, cmat)
            mat.apply_to(mat.invert(cmat), clip_path_csp)
        return (clipped_node, clip_path_csp)

    def clip_release(self, node, keep=True):
        """Release clip applied to node."""
        clipped_node, clip_path_def = self.get_clip_def(node)
        if clip_path_def is not None:
            if keep:
                index = clipped_node.getparent().index(node)
                for i, child in enumerate(clip_path_def, start=index+1):
                    node.getparent().insert(i, child)
                    mat.apply_copy_from(clipped_node, child)
            clip_path_def.getparent().remove(clip_path_def)
            clipped_node.set('clip-path', "none")

    def clip_set(self, node, path):
        """Clip node with path.

        First, add clipPath definition with path to <defs>.
        Then clip node with new clipPath.
        """
        clip = inkex.etree.SubElement(self.get_defs(),
                                      inkex.addNS('clipPath', 'svg'))
        clip.append(path)
        clip_id = self.uniqueId('clipPath')
        clip.set('id', clip_id)
        node.set('clip-path', 'url(#{0})'.format(clip_id))

    def clip_wrap(self, img_node, path):
        """Wrap <image> node in group and clip group with path."""
        group = wrap_group(img_node)
        if group is not None:
            mat.apply_to_d(mat.absolute_diff(img_node, path), path)
            self.clip_set(group, path)

    def wrap_result(self, img_node, path, mode="other"):
        """Post-process (wrap) the result of the image modification."""
        if mode == "group":
            group_with(img_node, path)
        elif mode == "clip":
            self.clip_wrap(img_node, path)
        elif mode == "delete":
            if path.getparent() is not None:
                path.getparent().remove(path)

    def geom_from_input(self):
        """Get geometric parameters from numeric input."""
        img_node = self.selected[self.options.ids[0]]
        if is_image(img_node):
            helper_path = create_img_placeholder(img_node)
            if helper_path is not None:
                self.modify_image(img_node, helper_path)
                if helper_path.getparent() is not None:
                    helper_path.getparent().remove(helper_path)
            else:
                inkex.errormsg(_(
                    "Failed to create helper path from image node."))
        else:
            inkex.errormsg(_(
                "This mode requires a selection of one bitmap image."))

    def geom_from_path(self):
        """Get geometric parameters from one helper path."""
        img_node = None
        helper_path = None
        for node in self.selected.values():
            if is_image(node):
                img_node = node
            elif is_path(node):
                helper_path = node
        if img_node is not None and helper_path is not None:
            self.modify_image(img_node, helper_path)
        else:
            inkex.errormsg(_(
                "This extension requires a selection of " +
                "a bitmap image and a path."))

    def geom_from_two_paths(self):
        """Get geometric parameters from two helper paths."""
        img_node = None
        helper_paths = []
        # get z-sorted list of ids
        id_list = zSort(self.document.getroot(), self.options.ids)
        # image is bottom-most
        img_node = self.selected[id_list[0]]
        # the rest are helper paths
        for id_ in id_list[1:]:
            if is_path(self.selected[id_]):
                helper_paths.append(self.selected[id_])
        if is_image(img_node) and len(helper_paths) == 2:
            self.modify_image(img_node, combine_two_paths(helper_paths))
            # clean up
            if self.options.wrap != 'no':
                for path in helper_paths:
                    path.getparent().remove(path)
        else:
            inkex.errormsg(_(
                "This extension requires a selection of " +
                "a bitmap image and 2 paths."))

    def geom_from_many_paths(self):
        """Get geometric parameters from multiple helper paths."""
        img_node = None
        helper_paths = []
        # get z-sorted list of ids
        id_list = zSort(self.document.getroot(), self.options.ids)
        # image is bottom-most
        img_node = self.selected[id_list[0]]
        # the rest are helper paths
        for id_ in id_list[1:]:
            if is_path(self.selected[id_]):
                helper_paths.append(self.selected[id_])
        if is_image(img_node) and len(helper_paths):
            self.modify_image(img_node, combine_many_paths(helper_paths))
            # clean up
            if self.options.wrap != 'no':
                for path in helper_paths:
                    path.getparent().remove(path)
        else:
            inkex.errormsg(_(
                "This extension requires a selection of " +
                "a bitmap image and 1 or more paths."))

    def geom_from_guides(self):
        """Get geometric parameters from guides."""
        img_node = self.selected[self.options.ids[0]]
        if is_image(img_node):
            helper_path = create_img_placeholder(img_node)
            if helper_path is not None:
                self.modify_image(img_node, helper_path)
                if helper_path.getparent() is not None:
                    helper_path.getparent().remove(helper_path)
            else:
                inkex.errormsg(_(
                    "Failed to create helper path from image node."))
        else:
            inkex.errormsg(_(
                "This mode requires a selection of one bitmap image."))

    def modify_image(self, img_node, path, points=None, subs=None):
        """Core method defined in each image-modifying extension."""
        raise NotImplementedError

    def effect(self):
        """Process current document."""
        global DEBUG
        DEBUG = self.options.debug

        if DEBUG:
            report_imaging_module("Default imaging module")

        # FIXME (pylint): Too many branches (13/12) (too-many-branches)
        if len(self.selected) == 1:
            if hasattr(self.options, 'nb_geom'):
                if self.options.nb_geom == '"custom"':
                    self.geom_from_input()
                elif self.options.nb_geom == '"guides"':
                    self.geom_from_guides()
                elif self.options.nb_geom == '"paths"':
                    inkex.errormsg(_(
                        "This mode requires 2 or more selected objects."))
                else:
                    inkex.errormsg(_(
                        "Unsupported geometric input mode."))
            else:
                self.geom_from_input()
        elif len(self.selected) > 1 and hasattr(self.options, 'nb_geom'):
            if self.options.nb_geom == '"paths"':
                self.geom_from_many_paths()
            else:
                inkex.errormsg(_(
                    "This mode requires 1 selected object."))
        elif self.options.tab == '"debug"':
            self.modify_image(img_node=None, path=None)
        else:
            inkex.errormsg(_(
                "This extension requires 1 selected object."))


class ImageModifier1(ImageModifier):
    """ImageModifier class for modification based on 1 path."""

    def __init__(self):
        """Init base class for ImageModifier1 class."""
        ImageModifier.__init__(self)

    def effect(self):
        """Process current document."""
        global DEBUG
        DEBUG = self.options.debug

        if DEBUG:
            report_imaging_module("Default imaging module")

        if len(self.selected) == 2:
            self.geom_from_path()
        elif len(self.selected) == 1 and hasattr(self.options, 'nb_geom'):
            if self.options.nb_geom == '"custom"':
                self.geom_from_input()
            elif self.options.nb_geom == '"guides"':
                self.geom_from_guides()
            else:
                inkex.errormsg(_(
                    "This mode requires a bitmap image and a helper path."))
        elif self.options.tab == '"debug"':
            self.modify_image(img_node=None, path=None)
        else:
            inkex.errormsg(_(
                "This extension requires 2 selected objects."))


class ImageModifier2(ImageModifier):
    """ImageModifier-based class for modification based on 2 paths."""

    def __init__(self):
        """Init base class for ImageModifier2 class."""
        ImageModifier.__init__(self)

    def effect(self):
        """Process current document."""
        global DEBUG
        DEBUG = self.options.debug

        if DEBUG:
            report_imaging_module("Default imaging module")

        if len(self.selected) == 3:
            self.geom_from_two_paths()
        elif self.options.tab == '"debug"':
            self.modify_image(img_node=None, path=None)
        else:
            inkex.errormsg(_(
                "This extension requires 3 selected objects."))


class ImageModifierMany(ImageModifier):
    """ImageModifier-based class for modification based on several paths."""

    def __init__(self):
        """Init base class for ImageModifierMany class."""
        ImageModifier.__init__(self)

    def effect(self):
        """Process current document."""
        global DEBUG
        DEBUG = self.options.debug

        if DEBUG:
            report_imaging_module("Default imaging module")

        if len(self.selected) > 1:
            self.geom_from_many_paths()
        elif self.options.tab == '"debug"':
            self.modify_image(img_node=None, path=None)
        else:
            inkex.errormsg(_(
                "This extension requires 2 or more selected objects."))


class ImageMassModifier(ImageModifier):
    """ImageModifier-based class for modification of multiple images."""

    def __init__(self):
        """Init base class for ImageModifier2 class."""
        ImageModifier.__init__(self)
        self.OptionParser.add_option("--scope",
                                     action="store",
                                     type="string",
                                     dest="scope",
                                     default="selected_only",
                                     help="Command scope")

    def change_image(self, img_node, params):
        """Prepare parameters for indiviual image to be modified."""
        if params == 'placeholder':
            helper_path = create_img_placeholder(img_node)
            if helper_path is not None:
                self.modify_image(img_node, helper_path)
                helper_path.getparent().remove(helper_path)
        else:
            self.modify_image(img_node, params)

    def change_all_images(self, node, params):
        """Iterate through all <image> elements in node."""
        path = 'descendant-or-self::svg:image'
        for img_node in node.xpath(path, namespaces=inkex.NSS):
            self.change_image(img_node, params)

    def change_selected_only(self, selected, params):
        """Iterate through all <image> elements among selected objects."""
        if selected:
            for node in selected.values():
                if is_image(node):
                    self.change_image(node, params)

    def change_in_selection(self, selected, params):
        """Change all <image> elements within selected nodes."""
        if selected:
            for node in selected.values():
                self.change_all_images(node, params)

    def change_in_document(self, _, params):
        """Change all <image> elements in current document."""
        self.change_all_images(self.document.getroot(), params)

    def get_params(self):
        """Return parameter values valid for all image changes."""
        pass

    def effect(self):
        """Process current document."""
        global DEBUG
        DEBUG = self.options.debug

        if DEBUG:
            report_imaging_module("Default imaging module")

        if self.options.tab == '"help"':
            pass
        else:
            cmd_scope = self.options.scope

        params = self.get_params()

        if cmd_scope is not None:
            try:
                change_cmd = getattr(self, 'change_{0}'.format(cmd_scope))
            except AttributeError as error_msg:
                inkex.debug('Scope "{0}" not supported'.format(cmd_scope))
                inkex.debug('Technical details:\n{0}'.format(error_msg))
            else:
                change_cmd(self.selected, params)


class ImageAttributer(ImageMassModifier):
    """ImageModifier-based class for attribute changes of many images.

    This sub-class supports methods to iterate through all <image>
    elements in the chosen scope (drawing content, selection), or
    to apply a modification to each selected object's parent container
    or to SVGRoot (this scope is relevant when modifying a style
    property which is inherited by all children of the container
    element).
    """

    def __init__(self):
        """Init base class, add default option for ImageAttributer class."""
        ImageMassModifier.__init__(self)
        self.OptionParser.add_option("--scope_attribute",
                                     action="store",
                                     type="string",
                                     dest="scope_attribute",
                                     default="selected_only",
                                     help="Command scope")
        self.OptionParser.add_option("--scope_property",
                                     action="store",
                                     type="string",
                                     dest="scope_property",
                                     default="selected_only",
                                     help="Command scope")

    def change_on_parent_group(self, selected, params):
        """Change attribute for parent container of selected node(s)."""
        if selected:
            for node in selected.values():
                self.change_image(node.getparent(), params)

    def change_on_root_only(self, _, params):
        """Change attribute for SVGRoot node."""
        self.change_image(self.document.getroot(), params)

    def effect(self):
        """Process current document."""
        global DEBUG
        DEBUG = self.options.debug

        if DEBUG:
            report_imaging_module("Default imaging module")

        if self.options.tab == '"tab_basic"':
            cmd_scope = "in_document"
        elif self.options.tab == '"tab_attribute"':
            cmd_scope = self.options.scope_attribute
        elif self.options.tab == '"tab_property"':
            cmd_scope = self.options.scope_property
        elif self.options.tab == '"help"':
            pass
        else:
            cmd_scope = self.options.scope

        params = self.get_params()

        if cmd_scope is not None:
            try:
                change_cmd = getattr(self, 'change_{0}'.format(cmd_scope))
            except AttributeError as error_msg:
                inkex.debug('Scope "{0}" not supported'.format(cmd_scope))
                inkex.debug('Technical details:\n{0}'.format(error_msg))
            else:
                change_cmd(self.selected, params)


# vim: et shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=79
