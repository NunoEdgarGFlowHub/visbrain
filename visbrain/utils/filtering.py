"""Set of tools to filter data."""

import numpy as np
from scipy.signal import butter, filtfilt, lfilter, bessel, welch

__all__ = ('filt', 'morlet', 'ndmorlet', 'morlet_power', 'welch_power')

#############################################################################
# FILTERING
#############################################################################


def filt(sf, f, x, btype='bandpass', order=3, method='butterworth',
         way='filtfilt', axis=0):
    """Filt data.

    Parameters
    ----------
    sf : float
        The sampling frequency
    f : array_like
        Frequency vector (2,)
    x : array_like
        The data to filt.
    btype : {'bandpass', 'bandstop', 'highpass', 'lowpass'}
        If highpass, the first value of f will be used. If lowpass
        the second value of f will be used.
    order : int | 3
        The filter order.
    method : {'butterworth', 'bessel'}
        Filter type to use.
    way : {'filtfilt', 'lfilter'}
        Specify if the filter has to be one way ('lfilter') or two ways
        ('filtfilt').
    axis : int | 0
        The axis along which the filter is applied.

    Returns
    -------
    xfilt : array_like
        Filtered data.
    """
    # Normalize frequency vector according to btype :
    if btype in ['bandpass', 'bandstop']:
        fnorm = np.divide(f, .5 * sf)
    elif btype == 'lowpass':
        fnorm = np.array(f[-1] / (.5 * sf))
    elif btype == 'highpass':
        fnorm = np.array(f[0] / (.5 * sf))

    # Get filter coefficients :
    if method == 'butterworth':
        b, a = butter(order, fnorm, btype=btype)
    elif method == 'bessel':
        b, a = bessel(order, fnorm, btype=btype)

    # Apply filter :
    if way == 'filtfilt':
        return filtfilt(b, a, x, axis=axis)
    elif way == 'lfilter':
        return lfilter(b, a, x, axis=axis)

#############################################################################
# WAVELET
#############################################################################


def _morlet_wlt(sf, f, width=7.0):
    """Get a Morlet's wavelet.

    Parameters
    ----------
    sf : float
        Sampling frequency.
    f : array_like
        Frequency vector of shape (2,).
    width : float | 7.0
        Width of the wavelet.
    wlt: array_like
        Morlet wavelet.
    """
    sf, f, width = float(sf), float(f), float(width)
    dt = 1 / sf
    sf = f / width
    st = 1 / (2 * np.pi * sf)

    # Build morlet wavelet :
    t = np.arange(-width * st / 2, width * st / 2, dt)
    a = 1 / np.sqrt((st * np.sqrt(np.pi)))
    wlt = a * np.exp(-np.square(t) / (2 * np.square(st))) * np.exp(
        1j * 2 * np.pi * f * t)

    return wlt


def morlet(x, sf, f, width=7.0):
    """Complex decomposition of a signal x using the morlet wavelet.

    Parameters
    ----------
    x : array_like
        The signal to use for the complex decomposition. Must be
        a vector of length N.
    sf : float
        Sampling frequency
    f : array_like, shape (2,)
        Frequency vector
    width : float | 7.0
        Width of the wavelet

    Returns
    -------
    xout: array_like
        The complex decomposition of the signal x.
    """
    # Get the wavelet :
    m = _morlet_wlt(sf, f, width)

    # Compute morlet :
    y = np.convolve(x, m)
    xout = y[int(np.ceil(len(m) / 2)) - 1:int(len(y) - np.floor(len(m) / 2))]

    return xout


def ndmorlet(x, sf, f, axis=0, get=None, width=7.0):
    """Complex decomposition using Morlet's wlt for a multi-dimentional array.

    Parameters
    ----------
    x : array_like
        The signal to use for the complex decomposition.
    sf : float
        Sampling frequency
    f : array_like
        Frequency vector of shape (2,)
    axis : integer | 0
        Specify the axis where is located the time dimension
    width : float | 7.0
        Width of the wavelet

    Returns
    -------
        xout: array, same shape as x
            Complex decomposition of x.
    """
    # Get the wavelet :
    m = _morlet_wlt(sf, f, width)

    # Define a morlet function :
    def morlet_fcn(xt):
        # Compute morlet :
        y = np.convolve(xt, m)
        return y[int(np.ceil(len(m) / 2)) - 1:int(len(y) - np.floor(
            len(m) / 2))]

    xf = np.apply_along_axis(morlet_fcn, axis, x)
    # Get amplitude / power / phase :
    if get == 'amplitude':
        return np.abs(xf)
    elif get == 'power':
        return np.square(np.abs(xf))
    elif get == 'phase':
        return np.angle(xf)


def morlet_power(x, freqs, sf, norm=True):
    """Compute bandwise-normalized power of data using morlet wavelet.

    Parameters
    ----------
    x : array_like
        Row vector signal.
    freqs : array_like
        Frequency bands for power computation. The power will be computed
        using successive frequency band (e.g freqs=(1., 2, .3)).
    sf : float
        Sampling frequency.
    norm : bool | True
        If True, return bandwise normalized band power
        (For each time point, the sum of power in the 4 band equals 1)

    Returns
    -------
    xpow : array_like
        The power in the specified frequency bands of shape
        (len(freqs)-1, npts).
    """
    # Build frequency vector :
    f = np.c_[freqs[0:-1], freqs[1::]].mean(1)
    # Get wavelet transform :
    xpow = np.zeros((len(f), len(x)), dtype=np.float)
    for num, k in enumerate(f):
        xpow[num, :] = np.abs(morlet(x, sf, k))
    # Compute inplace power :
    np.power(xpow, 2, out=xpow)
    # Normalize by the band sum :
    if norm:
        sum_pow = xpow.sum(0).reshape(1, -1)
        np.divide(xpow, sum_pow, out=xpow)
    return xpow


def welch_power(x, fmin, fmax, sf, window_s=30, norm=True):
    """Compute bandwise-normalized power of data using welch.

    Parameters
    ----------
    x : array_like
        Signal
    sf : int
        Downsampling frequency
    window_s : int, optional (def 30)
        Time resolution (sec) of Welch's periodogram. Must be > 10 seconds.
    norm : boolean, optional (def True)
        If True, return normalized band power
    """
    sf = int(sf)
    freq_spacing = 0.1
    f_vector = np.arange(0, sf / 2 + freq_spacing, freq_spacing)
    idx_fmin = np.where(f_vector == fmin)[0][0]
    idx_fmax = np.where(f_vector == fmax)[0][0] + 1
    delta_spec = np.array([], dtype=float)
    delta_spec_norm = np.array([], dtype=float)

    for i in np.arange(0, len(x), window_s * sf):
        f, Pxx_spec = welch(x[i:i + window_s * sf], sf, 'hanning',
                            nperseg=sf * (1 / freq_spacing),
                            scaling='spectrum')
        mean_delta = np.mean(Pxx_spec[idx_fmin:idx_fmax, ])
        norm_delta = np.sum(Pxx_spec[idx_fmin:idx_fmax, ]) / np.sum(Pxx_spec)
        delta_spec = np.append(delta_spec, mean_delta)
        delta_spec_norm = np.append(delta_spec_norm, norm_delta)

    return delta_spec_norm if norm else delta_spec
