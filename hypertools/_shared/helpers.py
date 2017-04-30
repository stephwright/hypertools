#!/usr/bin/env python

"""
Helper functions
"""

##PACKAGES##
from __future__ import division
from __future__ import print_function
import itertools
import sys
import six
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.interpolate import PchipInterpolator as pchip


##HELPER FUNCTIONS##
def center(x):
    assert type(x) is list, "Input data to center must be list"
    x_stacked = np.vstack(x)
    return [i - np.mean(x_stacked, 0) for i in x]


def scale(x):
    assert type(x) is list, "Input data to scale must be list"
    x_stacked = np.vstack(x)
    m1 = np.min(x_stacked)
    m2 = np.max(x_stacked - m1)
    return map(lambda i: 2 * ((i - m1) / m2) - 1, x)


def group_by_category(vals):
    if any(isinstance(el, list) for el in vals):
        vals = list(itertools.chain(*vals))
    val_set = list(sorted(set(vals), key=list(vals).index))
    return [val_set.index(val) for val in vals]


def vals2colors(vals, cmap='GnBu_d', res=100):
    """Maps values to colors
    Args:
    values (list or list of lists) - list of values to map to colors
    cmap (str) - color map (default is 'husl')
    res (int) - resolution of the color map (default: 100)
    Returns:
    list of rgb tuples
    """
    # flatten if list of lists
    if any(isinstance(el, list) for el in vals):
        vals = list(itertools.chain(*vals))

    # get palette from seaborn
    palette = np.array(sns.color_palette(cmap, res))
    ranks = np.digitize(vals, np.linspace(np.min(vals), np.max(vals) + 1, res + 1)) - 1
    return [tuple(i) for i in palette[ranks, :]]


def vals2bins(vals, res=100):
    """Maps values to bins
    Args:
    values (list or list of lists) - list of values to map to colors
    res (int) - resolution of the color map (default: 100)
    Returns:
    list of numbers representing bins
    """
    # flatten if list of lists
    if any(isinstance(el, list) for el in vals):
        vals = list(itertools.chain(*vals))
    return list(np.digitize(vals, np.linspace(np.min(vals), np.max(vals) + 1, res + 1)) - 1)


def interp_array(arr, interp_val=10):
    x = np.arange(0, len(arr), 1)
    xx = np.arange(0, len(arr) - 1, 1 / interp_val)
    q = pchip(x, arr)
    return q(xx)


def interp_array_list(arr_list, interp_val=10):
    smoothed = [np.zeros(arr_list[0].shape)] * len(arr_list)
    for idx, arr in enumerate(arr_list):
        smoothed[idx] = interp_array(arr, interp_val)
    return smoothed


def check_data(data):
    if type(data) is list:
        if all([isinstance(x, np.ndarray) for x in data]):
            return 'list'
        elif all([isinstance(x, pd.DataFrame) for x in data]):
            return 'dflist'
        else:
            raise ValueError(
                "Data must be numpy array, list of numpy array, pandas dataframe or list of pandas dataframes.")
    elif isinstance(data, np.ndarray):
        return 'array'
    elif isinstance(data, pd.DataFrame):
        return 'df'
    else:
        raise ValueError(
            "Data must be numpy array, list of numpy array, pandas dataframe or list of pandas dataframes.")


def parse_args(x, args):
    args_list = []
    for i, item in enumerate(x):
        tmp = []
        for ii, arg in enumerate(args):
            if type(arg) is tuple or type(arg) is list:
                if len(arg) == len(x):
                    tmp.append(arg[i])
                else:
                    print('Error: arguments must be a list of the same length as x')
                    sys.exit(1)
            else:
                tmp.append(arg)
        args_list.append(tuple(tmp))
    return args_list


def parse_kwargs(x, kwargs):
    kwargs_list = []
    for i, item in enumerate(x):
        tmp = {}
        for kwarg in kwargs:
            if type(kwargs[kwarg]) is tuple or type(kwargs[kwarg]) is list:
                if len(kwargs[kwarg]) == len(x):
                    tmp[kwarg] = kwargs[kwarg][i]
                else:
                    print('Error: keyword arguments must be a list of the same length as x')
                    sys.exit(1)
            else:
                tmp[kwarg] = kwargs[kwarg]
        kwargs_list.append(tmp)
    return kwargs_list


def reshape_data(x, labels):
    categories = list(sorted(set(labels), key=list(labels).index))
    x_stacked = np.vstack(x)
    x_reshaped = [[]] * len(categories)
    for idx, point in enumerate(labels):
        x_reshaped[categories.index(point)].append(x_stacked[idx])
    return [np.vstack(i) for i in x_reshaped]


def parse_equivalent_args(**kwargs):
    plurals = {'colors': 'color',
               'linestyles': 'linestyle',
               'markers': 'marker'}
    for k, v in six.iteritems(plurals):
        if k in kwargs:
            kwargs[k] = v
            del kwargs[v]
    return kwargs


def default_args(x, **kwargs):
    kwargs = parse_equivalent_args(**kwargs)

    defaults = {'normalize': False,
                'ndims': np.min([3, eval('x[0].shape[1]')]),
                'style': 'whitegrid',
                'palette': 'hls',
                'n_colors': eval('len(x)'),
                'animate': False,
                'zoom': 0,
                'chemtrails': False,
                'rotations': 2,
                'duration': 30,
                'frame_rate': 50,
                'tail_duration': 2,
                'return_data': False,
                'save': False,
                'show': True,
                'legend': False,
                'labels': False,
                'explore': False,
                'picker': False}

    for d in defaults.keys():
        if not (d in kwargs):
            kwargs[d] = defaults[d]

    assert (kwargs['ndims'] in [1, 2, 3]), 'ndims must be 1,2 or 3.'

    if kwargs['explore']:
        assert x[0].ndim > 1, "Explore mode is currently only supported for 3D plots."

    if 'save_path' in kwargs:
        kwargs['save'] = True
    else:
        kwargs['save_path'] = ''  # ensures this argument will be removed later

    if kwargs['show']:
        matplotlib.use('Agg')

    sns.set_palette(palette=kwargs['palette'], n_colors=len(x))

    return kwargs


def remove_hyper_args(x, **kwargs):
    defaults = default_args(x, **kwargs)
    for d in defaults.keys():
        if d in kwargs:
            del kwargs[d]
    return kwargs


def format_data(x):
    # not sure why i needed to import here, but its the only way I could get it to work
    from ..tools.df2mat import df2mat

    data_type = check_data(x)

    if data_type == 'df':
        x = df2mat(x)

    if data_type == 'dflist':
        x = [df2mat(i) for i in x]

    if type(x) is not list:
        x = [x]

    if any([i.ndim == 1 for i in x]):
        x = [np.reshape(i, (i.shape[0], 1)) if i.ndim == 1 else i for i in x]

    return x


def multipad(x):
    widths = map(lambda m: m.shape[1], x)
    maxwidth = np.max(widths)
    if not np.all(widths == maxwidth):
        y = []
        for i in x:
            pad = np.zeros([i.shape[0], maxwidth - i.shape[1]])
            y.append(np.hstack((x[i], pad)))
        return y
    else:
        return x


def patch_lines(x):
    """
    Draw lines between groups
    """
    for idx in range(len(x) - 1):
        x[idx] = np.vstack([x[idx], x[idx + 1][0, :]])
    return x
