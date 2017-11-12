"""Base class for objects of type connectivity."""
import numpy as np

from vispy import scene
import vispy.visuals.transforms as vist

from .visbrain_obj import VisbrainObject, CombineObjects
from ..utils import wrap_properties
from ..visuals import PicMesh, CbarArgs


class PictureObj(VisbrainObject, CbarArgs):
    """Create a connectivity object.

    Parameters
    ----------
    name : string
        The name of the connectivity object.
    data : array_like
        Array of data pictures of shape (n_sources, n_rows, n_columns).
    xyz : array_like
        The 3-d position of each picture of shape (n_sources, 3).
    select : array_like | None
        Select the pictures to display. Should be a vector of bolean values
        of shape (n_sources,).
    width : float | 7.
        Width of each picture.
    height : float | 7.
        Height of each picture.
    alpha : float | 1.
        Image transparency.
    cmap : string | 'viridis'
        Colormap to use.
    vmin : float | None
        Lower threshold of the colormap.
    under : string | None
        Color to use for values under vmin.
    vmin : float | None
        Higher threshold of the colormap.
    over : string | None
        Color to use for values over vmax.
    translate : tuple | (0., 0., 1.)
        Translation over the (x, y, z) axis.
    transform : VisPy.visuals.transforms | None
        VisPy transformation to set to the parent node.
    parent : VisPy.parent | None
        Line object parent.
    verbose : string
        Verbosity level.
    _z : float | 10.
        In case of (n_sources, 2) use _z to specify the elevation.

    Examples
    --------
    >>> import numpy as np
    >>> from visbrain.objects import PictureObj
    >>> n_rows, n_cols, n_pic = 10, 20, 5
    >>> data = np.random.rand(n_pic, n_rows, n_cols)
    >>> xyz = np.random.uniform(-10, 10, (n_pic, 3))
    >>> pic = PictureObj('Pic', data, xyz, cmap='plasma')
    >>> pic.preview(axis=True)
    """

    ###########################################################################
    ###########################################################################
    #                                BUILT IN
    ###########################################################################
    ###########################################################################

    def __init__(self, name, data, xyz, select=None, width=7., height=7.,
                 alpha=1., cmap='viridis', clim=None, vmin=None, vmax=None,
                 under='gray', over='red', translate=(0., 0., 1.),
                 transform=None, parent=None, verbose=None, _z=-10.):
        """Init."""
        VisbrainObject.__init__(self, name, parent, transform, verbose)
        isvmin, isvmax = vmin is not None, vmax is not None
        CbarArgs.__init__(self, cmap, clim, isvmin, vmin, isvmax, vmax, under,
                          over)

        # _______________________ CHECKING _______________________
        # Data :
        assert isinstance(data, np.ndarray) and data.ndim == 3.
        self._n_nodes = data.shape[0]
        self._minmax = (data.min(), data.max())
        # XYZ :
        sh = xyz.shape
        assert (sh[1] in [2, 3]) and (sh[0] == len(self))
        xyz = xyz if sh[1] == 3 else np.c_[xyz, np.full((len(self),), _z)]
        self._xyz = xyz.astype(np.float32)
        # Select :
        assert (select is None) or isinstance(select, (list, np.ndarray))
        # Width, height :
        assert all([isinstance(k, (int, float)) for k in (height, width)])
        self._width, self._height = width, height
        # Translate :
        assert len(translate) == 3
        tr = vist.STTransform(translate=translate)
        self._translate = translate
        # Alpha :
        assert isinstance(alpha, (int, float)) and (0. <= alpha <= 1.)
        self._alpha = alpha

        # _______________________ IMAGE _______________________
        self._pic = PicMesh(data, xyz, width, height, translate, select)
        self._pic.transform = tr
        self._pic.parent = self._node

    def __len__(self):
        """Get the number of pictures."""
        return self._n_nodes

    def _get_camera(self):
        """Get the most adapted camera."""
        d_mean = self._xyz.mean(0)
        dist = np.linalg.norm(self._xyz, axis=1).max()
        return scene.cameras.TurntableCamera(center=d_mean, scale_factor=dist)

    def update(self):
        """Update image."""
        self._pic.update()

    ###########################################################################
    ###########################################################################
    #                             PROPERTIES
    ###########################################################################
    ###########################################################################

    # ----------- WIDTH -----------
    @property
    def width(self):
        """Get the width value."""
        return self._width

    @width.setter
    @wrap_properties
    def width(self, value):
        """Set width value."""
        assert isinstance(value, (int, float))
        self._width = value
        self._pic.set_data(width=value)

    # ----------- HEIGHT -----------
    @property
    def height(self):
        """Get the height value."""
        return self._height

    @height.setter
    @wrap_properties
    def height(self, value):
        """Set height value."""
        assert isinstance(value, (int, float))
        self._height = value
        self._pic.set_data(height=value)

    # ----------- TRANSLATE -----------
    @property
    def translate(self):
        """Get the translate value."""
        return self._translate

    @translate.setter
    @wrap_properties
    def translate(self, value):
        """Set translate value."""
        assert len(value) == 3
        self._pic.transform.translate = value
        self._translate = value
        self.update()

    # ----------- ALPHA -----------
    @property
    def alpha(self):
        """Get the alpha value."""
        return self._alpha

    @alpha.setter
    @wrap_properties
    def alpha(self, value):
        """Set alpha value."""
        assert isinstance(value, (int, float)) and (0. <= value <= 1.)
        self._pic.alpha = value
        self._alpha = value


class CombinePictures(CombineObjects):
    """Combine pictures objects.

    Parameters
    ----------
    pobjs : PictureObj/list | None
        List of picture objects.
    select : string | None
        The name of the picture object to select.
    parent : VisPy.parent | None
        Images object parent.
    """

    def __init__(self, pobjs=None, select=None, parent=None):
        """Init."""
        CombineObjects.__init__(self, PictureObj, pobjs, select, parent)