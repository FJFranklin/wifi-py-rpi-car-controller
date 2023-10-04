baltam - Matlab plotting functions for Python beginners
=======================================================

## Overview

Matlab has a very simple set of commands for creating a variety of figures, and although Python's MatPlotLib these days has much of the same functionality, if not more, the class structure that needs to be understood can be a little intimidating. If the goal is to produce simple plots of functions and data, it's convenient to have some short cuts that don't require diving deep into Python.

`baltam.py` provides a few convenient functions that should not be treated as a permanent alternative to learning the various Python libraries such as SciPy and MatPlotLib. `practicals.py` gives a set of solutions to some Matlab practicals as an illustration of how to use baltam - and also its limitations.

## baltam

The simplest way to use these functions is just to include everything:
```python
from baltam import *
```
although if you are using Spyder (for example) it will complain about using functions that aren't clearly defined.

The functions defined in `baltam.py` are:

### `answer(number)`
A simple way to print a number to three significant figures, with options for the number of significant figures, to layout as a matrix, and a tolerance for zero (defaulting to 1E-15).
```
In [52]: answer(1/3)
answer (3 s.f.): 0.333

In [53]: answer(1j/3, sigfigs=5)
answer (5 s.f.): 0 + 0.33333i

In [54]: answer(np.asarray([[1,1j],[2,2j]]), style='matrix')
answer (3 s.f.):  (          1 +          0i) (          0 +          1i)
                  (          2 +          0i) (          0 +          2i)

In [55]: answer(0.001**5)
answer (3 s.f.): 0

In [56]: answer(0.001**5, zero=1E-16)
answer (3 s.f.): 1e-15
```
### `csvread(filename, skip_rows=0, skip_cols=0)`
Reads the named comma-separated variable (CSV) file, starting at row zero and column zero unless specified otherwise, e.g.:
```Python
data = csvread('accel_Dec0910_153854.csv', 1, 0)
```
### `ode(fn, from_to, y0)`
An ordinary differential equation solver, where `fn` is a function f(t,y) returning dy/dt; `from_to` is a list ([t1, t2] or [t1, ..., t2]) specifying the time-span of integration; and `y0` is the initial value to match `fn`, e.g.:
```Python
def dzdn(n, z):
    return np.asarray([z[0] - z[1], z[0] + z[1]])

N, Z = ode(dzdn, [0.5,1.5], [0.5,-0.5])
```

--------

## License

Unless otherwise stated, the code and examples here are
provided under the MIT License:

Copyright (c) 2020-23 Francis James Franklin

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the
Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to
do so, subject to the following conditions:

The above copyright notice and this permission notice shall
be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
