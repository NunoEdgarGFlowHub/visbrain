#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from matplotlib.cm import ScalarMappable
import matplotlib.colors as mplcol
from warnings import warn

from .math import normalize

__all__ = ['color2vb', 'array2colormap', 'dynamic_color', 'color2faces', '_colormap']


def color2vb(color=None, default=(1,1,1), length=1, alpha=1.0):
    """Tranform a tuple of RGB, matplotlib color or an
    hexadecimal color to an array of RGBA colors

    Kargs:
        color: None, tuple, string (def: None)
            The color to use. Can either be None, or a tuple (R, G, B),
            a matplotlib color or an hexadecimal color '#...'

        default: tuple, (def: (1,1,1))
            The default color to use instead.

        length: int (def: 10)
            The length of the output

        alpha: float, (def: 1)
            The opacity

    Return:
        vcolor: array
            Array of RGBA colors of shape (length, 4)
    """
    # Default or static color :
    if (color is None) or isinstance(color, (str, tuple)):
        # Default color : 
        if color is None:
            coltuple = default
        # Static color :
        elif isinstance(color, (tuple, list)):
            if len(color) == 4:
                alpha = color[-1]
                color = color[0:-1]
            coltuple = color
        # Matplotlib color :
        elif isinstance(color, str) and (color[0] is not '#'):
            # Check if the name is in the Matplotlib database :
            if color in mplcol.cnames.keys():
                coltuple = mplcol.hex2color(mplcol.cnames[color])
            else:
                warn("The color name "+color+" is not in the matplotlib "
                     "database. Default color will be used instead.")
                coltuple = default
        # Hexadecimal colors :
        elif isinstance(color, str) and (color[0] is '#'):
            try:
                coltuple = mplcol.hex2color(color)
            except:
                warn("The hexadecimal color "+color+" is not valid. "
                     "Default color will be used instead.")
                coltuple = default
        # Set the color :
        vcolor = np.concatenate((np.array([list(coltuple)]*length),
                                 alpha*np.ones((length, 1), dtype=float)), axis=1)

        return vcolor
    else:
        raise ValueError(str(type(color))+" is not a recognized type of color. "
                         "Use None, tuple or string")



def array2colormap(x, clim=None, cmap='inferno', alpha=1.0, vmin=None, vmax=None,
                   under='dimgray', over='darkred', faces_render=False):
    """Transform an array of data to colormap (array of RGBA)

    Args:
        x: array
            Array of data

    Kargs:
        cmap: string (def: inferno)
            Matplotlib colormap

        alpha: float, (def: 1.0)
            The opacity

        vmin: float (def: None)
            Minimum of the colormap

        vmax: float (def: None)
            Maximum of the colormap

        under: tuple/string (def: 'dimgray')
            Matplotlib color under vmin

        over: tuple/string (def: 'darkred')
            Matplotlib color over vmax

        faces_render: boll, optional, (def: False)
            Precise if the render should be applied to faces
    Return:
        color: array
            Array of RGBA colors
    """
    # Default clim :
    colim = [None, None]

    # Check the limit of the colorbar:
    if clim is None:
        clim = (x.min(), x.max())
    else:
        if not isinstance(clim, list):
            clim = list(clim)
        if len(clim) is not 2:
            raise ValueError("The length of the climit must be 2 (min, max)")
        else:
            if clim[0] is None:
                clim[0] = x.min()
            if clim[1] is None:
                clim[1] = x.max()

    # Invert vmin/vmax if vmin > vmax :
    if (vmin is not None) and (vmax is not None) and (vmax < vmin):
        v = vmin
        vmax = vmin
        vmin = v

    # Case management :
    if vmin is None:
        colim[0] = clim[0]
    else:
        x = colorclip(x, clim[0], kind='under')
        colim[0] = vmin
    if vmax is None:
        colim[1] = clim[1]
    else:
        x = colorclip(x, clim[1], kind='over')
        colim[1] = vmax

    # Define the colormap :
    cm = ScalarMappable(cmap=cmap)
    cm.set_clim(vmin=colim[0], vmax=colim[1])

    # Under/over the colorbar :
    if under is not None:
        cm.cmap.set_under(color=under)
    if over is not None:
        cm.cmap.set_over(color=over)

    # Faces render :
    x_cmap = np.array(cm.to_rgba(x, alpha=alpha))
    if faces_render:
        x_cmap = np.transpose(np.tile(x_cmap[..., np.newaxis], (1, 1, 3)), (0, 2, 1))

    return x_cmap


def dynamic_color(color, x, dynamic=(0.0, 1.0)):
    """dynamic color changing

    Args:
        color: np.ndarray
            The color to dynamic change. color must have a shape
            of (N, 4) RGBA colors

        x: np.ndarray
            Dynamic values for color. x must have a shape of (N,)
    Kargs:
        dynamic: tuple, optional, (def: (0.0, 1.0))
            Control the dynamic of color. 
            
    Return
        colordyn: np.ndarray
            Dynamic color with a shape of (N, 4)
    """
    x = x.ravel()
    # Check inputs types :
    if color.shape[1] != 4:
        raise ValueError("Color must be RGBA")
    if color.shape[0] != len(x):
        raise ValueError("The lenght of color must be the same as x: "+str(len(x)))
    # Normalise x :
    if dynamic[0] < dynamic[1]:
        x_norm = normalize(x, tomin=dynamic[0], tomax=dynamic[1])
    else:
        x_norm = np.full((len(x),), dynamic[0], dtype=np.float)
    # Update color :
    color[:, 3] = x_norm
    return color


def color2faces(color, length):
    """Pass a simple color to faces shape

    Args:
        color: RGBA tuple
            Tuple of RGBA colors

        length: tuple
            Length of faces

    Return
        colorFace: the color adapted for faces
    """
    color = color.ravel()
    colorL = np.tile(np.array(color)[..., np.newaxis, np.newaxis], (1, length, 3))
    return np.transpose(colorL, (1, 2, 0))


class _colormap(object):

    """Colormap class
    """

    def __init__(self, cmap=None, clim=None, vmin=None, vmax=None, under=None, over=None, data=None):
        if data is None:
            clim, vmin, vmax, under, over = (None, None), None, None, None, None
        else:
            if clim is None:
                clim = [data.min(), data.max()]
        self._cb = {'cmap':cmap, 'clim':clim, 'vmin':vmin, 'vmax':vmax, 'under':under, 'over':over}

    def __getitem__(self, key):
        return self._cb[key]

    def __setitem__(self, key, item):
        self._cb[key] = item

    def cbUpdateFrom(self, obj):
        """
        """
        objkeys = obj._cb.keys()
        for k in self._cb.keys():
            if k in objkeys:
                self[k] = obj[k]

    
def colorclip(x, th, kind='under'):
    """Force an array to have clipping values

    :x: array of data
    :th: the threshold to use
    :kind: string, can be either 'under' or 'over'
    """
    if kind is 'under':
        idx = x < th
    elif kind is 'over':
        idx = x > th
    x[idx] = th
    return x
