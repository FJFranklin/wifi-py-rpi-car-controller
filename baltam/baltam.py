"""Some functions (especially for plotting) to make Python behave like Matlab

Just add at the beginning of your Python script or session:

from baltam import *

Provides: ode, csvread, answer, and various plotting functions
Requires: numpy, scipy and matplotlib
"""

# If using Spyder or some interactive Python, the figures behave in a very
# different way, so this forces the figures to appear in separate windows
try:
    from IPython import get_ipython
    get_ipython().run_line_magic('matplotlib', 'qt')
except:
    pass

# A useful library for reading data from text files
import csv

# NumPy is an important library for using Python to manipulate data mathematically
import numpy as np

# SciPy builds a lot of mathematical and scientific functionality on top of NumPy
import scipy.integrate as integrate     # e.g., for solving ODEs

# MatPlotLib does scientific plotting for Python
from mpl_toolkits.mplot3d import Axes3D # Need this for 3D plots
from matplotlib import cm               # Different color maps
import matplotlib.pyplot as plt

def fzero(fn, x0):
    print('Instead of fzero(), use opt.fsolve() [or: from scipy.optimize import fsolve]')

def fminsearch(fn, x0):
    print('Instead of fminsearch(), use opt.fmin() [or: from scipy.optimize import fmin]')

def ode(fn, from_to, y0):
    """Similar in form to Matlab's ode23() for solving ordinary differential equations

    Parameters
    ----------
    fn : function
        A function f(t,y) returning dy/dt, where t is scalar
    from_to : list
        Either [t1, t2] or [t1, ..., t2] specifying time-span of integration
    y0 : scalar or array to match y
        Format string as usual for plot() (default is 'b-')

    Returns
    -------
    array
        array of start, intermediate and end time points
    array
        array of y at corresponding start, intermediate and end time points
    """
    t_values = [from_to[0]]
    if np.isscalar(y0):
        y_values = [np.asarray([y0])]
    else:
        y_values = [np.asarray(y0)]
    r = integrate.ode(fn).set_integrator('lsoda')
    r.set_initial_value(y0, from_to[0])
    if len(from_to) == 2:
        from_to = np.linspace(from_to[0], from_to[1], 100)
    for t in range(1,len(from_to)):
        tn = from_to[t]
        yn = r.integrate(tn)
        if r.successful():
            t_values.append(tn)
            y_values.append(yn)
        else:
            break
    return np.asarray(t_values), np.asarray(y_values)

def csvread(filename, skip_rows=0, skip_cols=0):
    """Similar in form to Matlab's csvread() for importing comma-delimited CSV text data files

    Parameters
    ----------
    filename : str
        Name of CSV file to import
    skip_rows : int
        How many initial rows (lines) to skip in the text file before beginning to import (default none)
    skip_cols : int
        How many initial columns (comma-delimited) to skip in the text file before beginning to import (default none)

    Returns
    -------
    array
        array of data imported
    """
    data = []
    with open(filename, newline='') as csvfile:
        rows = csv.reader(csvfile, delimiter=',')
        row_no = 0
        for row in rows:
            row_no += 1
            if row_no <= skip_rows:
                continue
            values = []
            col_no = 0
            for col in row:
                col_no += 1
                if col_no <= skip_cols:
                    continue
                values.append(float(col))
            data.append(values)
    return np.asarray(data)

def answer(number, **kwargs):
    """Not a Matlab function, just a handy way to print an answer to a specified number of significant figures

    Parameters
    ----------
    number : scalar or array
        One or more values (potentially complex numbers) to print

    Keyword Arguments
    -----------------
    sigfigs : int, optional
        Number of significant figures (default 3)
    continuation : bool, optional
        Whether to suppress the leading text 'answer (3 s.f.)' (default is False)
    style : str, optional
        To format as a matrix, use style='matrix' (default is 'number')
    zero : float, optional
        Set a tolerance for zero values (default is 1E-15)
    """
    if 'continuation' in kwargs:
        bCont = kwargs['continuation']
    else:
        bCont = False
    if 'sigfigs' in kwargs:
        SF = kwargs['sigfigs']
    else:
        SF = 3
    if 'style' in kwargs:
        style = kwargs['style']
    else:
        style = 'number'
    if 'zero' in kwargs:
        zero = kwargs['zero']
    else:
        zero = 1E-15

    if style == 'matrix':
        def append_number(str, number):
            if isinstance(number, complex):
                n_r = number.real
                n_i = number.imag
                if abs(n_r) <= zero:
                    n_r = 0
                if abs(n_i) <= zero:
                    n_i = 0
                if n_i < 0:
                    sign = '-'
                else:
                    sign = '+'

                return str + ' ({r:{w}.{f}g} {s}{i:{w}.{f}g}i)'.format(s=sign, r=n_r, i=abs(n_i), f=SF, w=(SF+8))
            else:
                if abs(number) <= zero:
                    number = 0
                return str + ' {r:{w}.{f}g}'.format(r=number, f=SF, w=(SF+8))
            
        if number.ndim == 1:
            cols = len(number)
            if not bCont:
                line = 'answer (%d s.f.): ' % SF
            else:
                line = '                 '
            for c in range(cols):
                line = append_number(line, number[c])
            print(line)
        else:
            rows, cols = number.shape
            for r in range(rows):
                if r == 0 and not bCont:
                    line = 'answer (%d s.f.): ' % SF
                else:
                    line = '                 '
                for c in range(cols):
                    line = append_number(line, number[r,c])
                print(line)
    elif not np.isscalar(number):
        for no in number:
            answer(no, continuation=bCont, sigfigs=SF)
            bCont = True
    else:
        def append_number(str, number):
            if isinstance(number, complex):
                n_r = number.real
                n_i = number.imag
                if abs(n_r) <= zero:
                    n_r = 0
                if abs(n_i) <= zero:
                    n_i = 0
                if n_i < 0:
                    sign = '-'
                else:
                    sign = '+'

                return str + '{r:.{f}g} {s} {i:.{f}g}i'.format(s=sign, r=n_r, i=abs(n_i), f=SF)
            else:
                if abs(number) <= zero:
                    number = 0
                return str + '{r:.{f}g}'.format(r=number, f=SF)

        if bCont:
            lead = '                 '
        else:
            lead = 'answer (%d s.f.): ' % SF

        print(append_number(lead, number))

class BaltamFigure(object):
    fig = None
    ax = None
    threeD: bool = False
    handles: list = None
    number: int = 0

    def __init__(self, fig_no: int, threeD: bool = False) -> None:
        self.fig = plt.figure(fig_no)
        self.threeD = threeD
        self.number = fig_no

        if threeD:
            self.ax = self.fig.add_subplot(projection='3d')
        else:
            self.ax = self.fig.subplots()

        self.fig.canvas.mpl_connect('close_event', baltam_figure_closed)
        
        self.handles = []

    def set_threeD(self, threeD: bool):
        if threeD != self.threeD:
            self.threeD = threeD
            self.fig.clf()
            self.handles = []
            if threeD:
                self.ax = self.fig.add_subplot(projection='3d')
            else:
                self.ax = self.fig.subplots()

    def clear(self) -> None:
        self.ax.cla()
        self.handles = []

_baltam_figures = {}
_baltam_figure_next = 1
_baltam_figure_current = None
_baltam_figure_hold = False

def baltam_figure_closed(event):
    # call-back function on window closure

    global _baltam_figure_current
    global _baltam_figures

    for fig_entry in _baltam_figures:
        bfig = _baltam_figures[fig_entry]
        if event.canvas.figure == bfig.fig:
            _baltam_figures.pop(fig_entry)
            if _baltam_figure_current == fig_entry:
                _baltam_figure_current = None
            break

def _baltam_new_figure(fig_no: int, threeD: bool = False) -> BaltamFigure:
    """Create a new plot window and axes.

    Parameters
    ----------
    fig_no : int
        Integer identifier for the figure
    threeD : bool (optional)
        Set to True if using 3D axes

    Returns
    -------
    bfig
        The BaltamFigure handle
    """
    global _baltam_figure_current
    global _baltam_figures
    
    if fig_no is None:
        fig_next = 1
        while fig_next in _baltam_figures:
            fig_next = fig_next + 1
        fig_no = fig_next

    bfig = None
    
    if fig_no in _baltam_figures:
        bfig = _baltam_figures[fig_no]
        bfig.set_threeD(threeD)

    else:
        bfig = BaltamFigure(fig_no, threeD)
        _baltam_figures[fig_no] = bfig

    _baltam_figure_current = fig_no
    return bfig

def gca():
    """Returns the current MatPlotLib axis.

    Returns
    -------
    ax
        The MatPlotLib axes handle, or None
    """
    global _baltam_figure_current
    global _baltam_figures

    ax = None
    if _baltam_figure_current is not None:
        bfig = _baltam_figures[_baltam_figure_current]
        ax = bfig.ax
    return ax

def figure(fig_no = None) -> BaltamFigure:
    """Similar in form to Matlab's figure() for opening or specifying a figure window.

    Parameters
    ----------
    fig_no : int (optional)
        Integer specifying the figure window

    Returns
    -------
    bfig
        The BaltamFigure handle
    """
    return _baltam_new_figure(fig_no)

def xlim(limits):
    """Similar in form to Matlab's xlim() for setting x-axis limits.

    Parameters
    ----------
    limits : list
        List with two values (minimum and maximum)
    """
    ax = gca()
    if ax is not None:
        ax.set_xlim(limits[0], limits[1])

def ylim(limits):
    """Similar in form to Matlab's ylim() for setting y-axis limits.

    Parameters
    ----------
    limits : list
        List with two values (minimum and maximum)
    """
    ax = gca()
    if ax is not None:
        ax.set_ylim(limits[0], limits[1])

def zlim(limits):
    """Similar in form to Matlab's zlim() for setting z-axis limits.

    Parameters
    ----------
    limits : list
        List with two values (minimum and maximum)
    """
    ax = gca()
    if ax is not None:
        ax.set_zlim(limits[0], limits[1])

def xlabel(label):
    """Similar in form to Matlab's xlabel() for labelling the x-axis.

    Parameters
    ----------
    label : str
        Text to set as axis label
    """
    ax = gca()
    if ax is not None:
        ax.set_xlabel(label)

def ylabel(label):
    """Similar in form to Matlab's ylabel() for labelling the y-axis.

    Parameters
    ----------
    label : str
        Text to set as axis label
    """
    ax = gca()
    if ax is not None:
        ax.set_ylabel(label)

def zlabel(label):
    """Similar in form to Matlab's zlabel() for labelling the z-axis.

    Parameters
    ----------
    label : str
        Text to set as axis label
    """
    ax = gca()
    if ax is not None:
        ax.set_zlabel(label)

def title(text):
    """Similar in form to Matlab's title() for adding a title to the plot.

    Parameters
    ----------
    text : str
        Text to set as plot title
    """
    ax = gca()
    if ax is not None:
        ax.set_title(text)
    else:
        print('no axis?')

def legend(descriptions: list) -> None:
    """Similar in form to Matlab's title() for adding a title to the plot.

    Parameters
    ----------
    descriptions : list of str
        Text to set as descriptions for each line in plot
    """
    global _baltam_figure_current
    global _baltam_figures

    if _baltam_figure_current is not None:
        bfig = _baltam_figures[_baltam_figure_current]
        index = 0
        for d in descriptions:
            if index == len(bfig.handles):
                break
            h = bfig.handles[index]
            h.set_label(d)
            index = index + 1
        bfig.ax.legend()

def hold(on=True):
    """Similar in form to Matlab's hold on / hold off for superimposing plots.

    Parameters
    ----------
    on : bool
        If False, new plots will overwrite any existing plot in the current figure
    """
    global _baltam_figure_hold
    _baltam_figure_hold = on

def fsurf(fn, from_to=None, **kwargs):
    """Similar in form to Matlab's fsurf() for plotting surfaces; with options for producing contours instead / as well.

    Parameters
    ----------
    fn : function
        A function of two variables returning a scalar value
    from_to : list, optional
        Either [xmin, xmax, ymin, ymax] or [xmin, xmax, ymin, ymax, zmin, zmax] (default is [-5, 5, -5, 5])

    Keyword Arguments
    -----------------
    resolution : tuple
        A tuple of integers (Nx, Ny) specifying resolutions in x- and y-axes (default (51, 51))
    cmap : colormap
        A matplotlib colormap, e.g., cm.jet, cm.winter (default is cm.coolwarm)
    plot_type : str
        Type of plot: one of 'surf', 'surfc', 'cont2d', 'cont3d' (default is 'surf')

    Returns
    -------
    surf
        The surface plot handle, or None
    contour
        The contour plot handle, or None
    """
    global _baltam_figure_current
    global _baltam_figure_hold

    if 'resolution' in kwargs:
        N = kwargs['resolution']
    else:
        N = (51,51)
    if 'cmap' in kwargs:
        colormap = kwargs['cmap']
    else:
        colormap = cm.coolwarm
    if 'plot_type' in kwargs:
        pt = kwargs['plot_type']
        # S = Surface only; C = Contour [2D] only; B = both Surface and Contour [2D]; '3' = Contour [3D] only
        if pt == 'surfc':
            plot_type = 'B'
        elif pt == 'cont2d':
            plot_type = 'C'
        elif pt == 'cont3d':
            plot_type = '3'
        else:
            plot_type = 'S'
    else:
        plot_type = 'S'

    if from_to is None:
        from_to = [-5,5,-5,5]

    surf = None
    contour = None

    Nx, Ny = N
    x = np.linspace(from_to[0], from_to[1], Nx)
    y = np.linspace(from_to[2], from_to[3], Ny)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros((Ny,Nx))
    for r in range(0, Ny):
        Z[r,:] = fn(x, y[r])

    if plot_type == 'C':
        bfig = _baltam_new_figure(_baltam_figure_current)
    else:
        bfig = _baltam_new_figure(_baltam_figure_current, True)
    fig = bfig.fig
    ax  = bfig.ax

    if not _baltam_figure_hold:
        bfig.clear()

    if plot_type == 'S' or plot_type == 'B':
        surf = ax.plot_surface(X, Y, Z, cmap=colormap, rcount=Ny, ccount=Nx)
        fig.colorbar(surf, shrink=0.5, aspect=5)
    if plot_type == 'C' or plot_type == '3':
        contour = ax.contour(X, Y, Z, cmap=colormap)
        if plot_type == 'C':
            ax.clabel(contour, inline=1, fontsize=10)
    ax.set_xlim(from_to[0], from_to[1])
    ax.set_ylim(from_to[2], from_to[3])
    if len(from_to) == 6 and plot_type != 'C':
        ax.set_zlim(from_to[4], from_to[5])
    if plot_type == 'B':
        if len(from_to) > 4:
            z_off = from_to[4]
        else:
            z_off = Z.min()
        contour = ax.contour(X, Y, Z, cmap=colormap, offset=z_off)
    plt.show(block=False)

    return surf, contour

def surface(x_vector, y_vector, Z_matrix, **kwargs):
    """Similar in form to Matlab's surface() for plotting surfaces.

    Parameters
    ----------
    x_vector : numpy array
        A vector with x-data
    y_vector : numpy array
        A vector with y-data
    Z_matrix : 2D numpy array
        A matrix with z-data, aligned with x-data as columns, y-data as rows

    Keyword Arguments
    -----------------
    cmap : colormap
        A matplotlib colormap, e.g., cm.jet, cm.winter (default is cm.coolwarm)

    Returns
    -------
    surf
        The surface plot handle, or None
    """
    global _baltam_figure_current
    global _baltam_figure_hold

    if 'cmap' in kwargs:
        colormap = kwargs['cmap']
    else:
        colormap = cm.coolwarm

    Nx = len(x_vector)
    Ny = len(y_vector)
    X, Y = np.meshgrid(x_vector, y_vector)

    bfig = _baltam_new_figure(_baltam_figure_current, True)
    fig = bfig.fig
    ax  = bfig.ax

    if not _baltam_figure_hold:
        bfig.clear()

    surf = ax.plot_surface(X, Y, Z_matrix, cmap=colormap, rcount=Ny, ccount=Nx)
    fig.colorbar(surf, shrink=0.5, aspect=5)
    plt.show(block=False)

    return surf

def contour(x_vector, y_vector, Z_matrix, **kwargs):
    """Similar in form to Matlab's contour() for plotting a 2D contour map.

    Parameters
    ----------
    x_vector : numpy array
        A vector with x-data
    y_vector : numpy array
        A vector with y-data
    Z_matrix : 2D numpy array
        A matrix with z-data, aligned with x-data as columns, y-data as rows

    Keyword Arguments
    -----------------
    cmap : colormap
        A matplotlib colormap, e.g., cm.jet, cm.winter (default is cm.coolwarm)

    Returns
    -------
    contour
        The contour plot handle, or None
    """
    global _baltam_figure_current
    global _baltam_figure_hold

    if 'cmap' in kwargs:
        colormap = kwargs['cmap']
    else:
        colormap = cm.coolwarm

    X, Y = np.meshgrid(x_vector, y_vector)

    bfig = _baltam_new_figure(_baltam_figure_current, False)
    ax  = bfig.ax

    if not _baltam_figure_hold:
        bfig.clear()

    cont = ax.contour(X, Y, Z_matrix, cmap=colormap)
    ax.clabel(cont, inline=1, fontsize=10)
    plt.show(block=False)

    return cont

def fplot(fn, from_to=None, fmt=None):
    """Similar in form to Matlab's fplot() for plotting curves of functions.

    Parameters
    ----------
    fn : function
        A function of one variable returning a scalar value or array of values
    from_to : list, optional
        Either [xmin, xmax] or [xmin, xmax, ymin, ymax] (default is [-5, 5])
    fmt : str, optional
        Format string as usual for plot() (default is 'b-')

    Returns
    -------
    list
        a list of handles for curves plotted
    """
    global _baltam_figure_current
    global _baltam_figure_hold

    bfig = _baltam_new_figure(_baltam_figure_current)
    ax  = bfig.ax

    if not _baltam_figure_hold:
        bfig.clear()

    handles = []
    if from_to is None:
        from_to = [-5,5]
    x = np.linspace(from_to[0], from_to[1], 201)
    y = fn(x)
    if y.ndim == 1:
        if fmt is None:
            fmt = 'b-'
        p, = ax.plot(x, y, fmt)
        handles.append(p)
        bfig.handles.append(p)
    else:
        lsl = ['b-','r-','g-','c-','y-','m-','k-']
        lsi = 0
        for row in y:
            if fmt is None:
                ls = lsl[lsi]
                lsi += 1
                if lsi == len(lsl):
                    lsi = 0
            else:
                ls = fmt
            p, = ax.plot(x, row, ls)
            handles.append(p)
            bfig.handles.append(p)
    xlim([from_to[0], from_to[1]])
    if len(from_to) == 4:
        ylim([from_to[2], from_to[3]])
    plt.show(block=False)
    return handles

def plot(xdata, ydata, fmt=None):
    """Similar in form to Matlab's plot() for plotting curves of functions.

    Parameters
    ----------
    xdata : numpy array
        Array of x-data values
    ydata : numpy array
        Array of y-data values
    fmt : str, optional
        Format string as usual for plot() (default is 'b-')

    Returns
    -------
    list
        a list of handles for curves plotted
    """
    global _baltam_figure_current
    global _baltam_figure_hold

    bfig = _baltam_new_figure(_baltam_figure_current)
    ax  = bfig.ax

    if not _baltam_figure_hold:
        bfig.clear()

    handles = []
    if fmt is None:
        fmt = 'b-'
    p, = ax.plot(xdata, ydata, fmt)
    handles.append(p)
    bfig.handles.append(p)

    plt.show(block=False)
    return handles

def plot3(xdata, ydata, zdata, fmt=None):
    """Similar in form to Matlab's plot3() for plotting curves of functions.

    Parameters
    ----------
    xdata : numpy array
        Array of x-data values
    ydata : numpy array
        Array of y-data values
    zdata : numpy array
        Array of z-data values
    fmt : str, optional
        Format string as usual for plot() (default is 'b-')

    Returns
    -------
    list
        a list of handles for curves plotted
    """
    global _baltam_figure_current
    global _baltam_figure_hold

    bfig = _baltam_new_figure(_baltam_figure_current, True)
    ax  = bfig.ax

    if not _baltam_figure_hold:
        bfig.clear()

    handles = []
    if fmt is None:
        fmt = 'b-'
    p, = ax.plot(xdata, ydata, zdata, fmt)
    handles.append(p)
    bfig.handles.append(p)

    plt.show(block=False)
    return handles
