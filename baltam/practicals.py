import math   # default Python maths library
import cmath  # default Python maths library - with support for complex numbers

# NumPy is an important library for using Python to manipulate data mathematically
import numpy as np

# SciPy builds a lot of mathematical and scientific functionality on top of NumPy
import scipy.optimize as opt            # e.g., for solving zeros and minima

# MatPlotLib does scientific plotting for Python
from mpl_toolkits.mplot3d import Axes3D # Need this for 3D plots
from matplotlib import cm               # Different color maps
import matplotlib.pyplot as plt

# baltam has a number of functions that make simple Matlab-style plots easy
from baltam import gca, figure, xlabel, ylabel, zlabel, xlim, ylim, zlim, hold
from baltam import title, legend, fplot, fsurf, surface, contour, plot, plot3
# ode() is similar to Matlab's ode23
from baltam import ode
# Matlab no longer supports csvread(), although dlmread() still works for now
from baltam import csvread
# answer() is not a Matlab function, just a handy tool for printing numbers neatly
from baltam import answer

def Practical_1():
    answer( 1 - math.cos(math.pi/6)**2 )
    answer( math.log(10) )
    answer( math.log10(100) )
    answer( 3 * math.atan(1.7321) )
    answer( math.exp(-0.5) )
    answer( math.sqrt(67) )
    answer( math.pow(216, 1/3) )
    answer( 10**1.398 )
    answer( math.cosh(math.log10(5))**2 - math.sinh(-math.log10(1/5))**2 )

    a = -2
    b = math.sqrt(2)
    w = -2 + 3j
    z = 1 - 1j

    answer( a + 3 )
    answer( math.sqrt(a + 2*b) )
    answer( cmath.sqrt(w) )
    answer( abs(z) )
    answer( (z - 2*w).real )
    answer( w / z )

    def no_1(x):
        return 1 - np.cos(x)**2

    #fplot(no_1, [-10,10], 'r:')

    def no_9(x):
        return np.cosh(np.log10(x))**2 - np.sinh(-np.log10(1/x))**2

    #fplot(no_9, [0,0.01], 'k-')

    answer( np.roots([1,3,2]) )
    answer( np.roots([1,3,3]) )
    answer( np.roots([1,-1,2,1]) )
    answer( np.roots([1,1,-2,0,1]) )
    answer( np.roots([1,-3,1,3,1]) )

    def no_19(x):
        return np.polyval([1,1,-2,0,1], x)

    fplot(no_19, [-2.5,2.5], 'b-')
    title('Quartic poly')
    xlabel('x')
    ylabel('y')
    hold(True)
    plot([-1.91,-0.671], [0,0], 'ro')
    hold(False)

    answer( np.arange(1, 11)**2 )
    answer( np.sum(np.arange(1, 11)**2) )
    answer( 1j ** np.arange(0, 4) )
    answer( np.sum(1j ** np.arange(0, 4)) )
    answer( 0.5 ** np.arange(0, 5) )
    answer( np.sum(0.5 ** np.arange(0, 5)) )

def Practical_2():
    answer( math.sqrt(101) - math.sqrt(99) )
    answer( 500**(1/3) )
    answer( math.pi**3 )
    answer( math.acos(math.sin(math.pi/7)) - math.asin(math.cos(math.pi/7)) )

    answer( np.roots([1,0,0,0,4]) )
    answer( np.roots([1,1,1,1,1,1]) )

    answer( (-1j)**np.arange(0,4) )
    answer( np.arange(1,6)**(-2.0) ) # Interesting: This complains about integers to -ve integer powers

    np.asarray([[1,7],[-3,4]])
    np.asarray([[-2,1,0],[0,-1,2]])

    def sin_c(x):
        c = 1.6
        return np.sin(x + c)

    figure(1)

    fplot(sin_c,  [-2*math.pi,2*math.pi], 'b-')
    hold(True)
    fplot(np.cos, [-2*math.pi,2*math.pi], 'r-')
    legend(['sin(x+1.6)','cos(x)'])
    hold(False)

    figure(2)

    V = [0.16, 0.42, 0.69, 1.21, 1.67, 1.99,  2.22,  2.49]
    T = [1.40, 2.29, 3.66, 5.93, 8.15, 9.24, 10.32, 11.41]

    plot(V, T, 'ro')
    xlabel('Signal Voltage [V]')
    ylabel('Torque [Nm]')
    title('Torque vs Voltage')
    hold(True)

    p = np.polyfit(V, T, 1)
    print('Best fit straight line is: T = {m:.3g} V + {c:.3g}'.format(m=p[0], c=p[1]))

    def fit(x):
        return np.polyval(p, x)

    fplot(fit, [0,2.5], 'k--')
    hold(False)

def Practical_3():
    answer( 1 / math.cos(math.radians(60)) ) # No sec/cosec/cot functions defined
    answer( np.roots([1,0,0,0,-1]) )
    answer( (-1)**np.arange(0,4) )
    answer( ((-1)**np.arange(0,4) + 1) / 2 )
    answer( ((-1)**np.arange(0,5) + 1) / 2 * np.arange(1,6) )

    S = np.asarray([[5],[-3],[2]]) # or: np.asarray([[5,-3,2]]).T
    S[0,0] = S[1,0] + S[2,0]
    print('S = {m}'.format(m=S))

    def g(x):
        return np.polyval([1,0,1], x)

    def w(t):
        return np.polyval([1,-1,1,-1], t)

    def V(q):
        return np.polyval([-5,6,3], q)

    def U(p):
        return np.polyval([1/math.factorial(5),-1/math.factorial(4),0,0,0,0], p)

    def f(x):
        return x * np.sin(x)

    def h(t):
        return np.log(np.tan(t))

    def Z(w):
        if np.isscalar(w):
            return np.asarray([[np.exp(-w**2)],[np.cos(w)]])
        else:
            return np.asarray([np.exp(-w**2),np.cos(w)])

    fplot(Z)

    def Q(x,y):
        return x * np.cos(x) + y * np.cos(y)

    
    T = np.arange(1,11)
    Elevation = [73.01, 69.71, 64.26, 54.5,  36.01,  3.99, -29.49, -49.79, -60.79, -67.27]
    Distance  = [30.46, 45.88, 51.04, 48.19, 40.96, 37.48,  46.81,  67.06,  92.6,  120.58]

    p_ea = np.polyfit(T, Elevation, 3)
    p_d  = np.polyfit(T, Distance , 3)

    def ea(t):
        return np.polyval(p_ea, t)

    def d(t):
        return np.polyval(p_d,  t)

def Practical_4():
    answer( 2e16 / 3 - 2e16 * (1 / 3) )

    def e(x):
        return x * 1e16 - ((1 / 3) * 1e16) * (3 * x)

    figure(1)
    fplot(e, [0,10])
    title('A plot demonstrating numerical errors')

    def f(v):
        return np.linspace(-v,v,3) # or: v * np.arange(-1,2)

    def h(v):
        return np.linspace(-v,v,4) # or: v * np.arange(-3,4,2) / 3

    def Z(n):
        return np.linspace(0,n,n+1) # or: np.arange(0,n+1)

    def Q(n):
        return np.linspace(0,1,n+1) # or: np.arange(0,n+1) / n

    def J(n,v):
        return np.linspace(0,v,n+1) # or: v * np.arange(0,n+1) / n

    S = np.asarray([[6,-3,7],[-2,1,5]])
    S[1,2] = -S[1,2]
    print('S = {m}'.format(m=S))

    T = np.arange(1,11)
    Elevation = [73.01, 69.71, 64.26, 54.5,  36.01,  3.99, -29.49, -49.79, -60.79, -67.27]
    Distance  = [30.46, 45.88, 51.04, 48.19, 40.96, 37.48,  46.81,  67.06,  92.6,  120.58]

    p_ea = np.polyfit(T, Elevation, 3)
    p_d  = np.polyfit(T, Distance , 3)

    def ea(t):
        return np.polyval(p_ea, t)

    def d(t):
        return np.polyval(p_d,  t)

    figure(2)
    plot(T, Elevation, 'go')
    hold(True)
    fplot(ea, [0,10], 'r-')
    xlabel('Time [s]')
    ylabel('Elevation [deg]')
    title('Elevation vs Time')
    hold(False)

    figure(3)
    plot(T, Distance, 'go')
    hold(True)
    fplot(d, [0,10], 'r-')
    xlabel('Time [s]')
    ylabel('Distance [m]')
    title('Distance vs Time')
    hold(False)

def Practical_5():
    def M(n,a,b):
        return np.linspace(a,b,n+1) # or: a + (b-a) * np.arange(0,n+1) / n

    name = input('What is your name: ')
    colour = input('What is your favourite colour: ')
    birthplace = input('Where were you born: ')
    print('{n}\'s favourite colour is {c}. {n} was born in {p}.'.format(n=name, c=colour, p=birthplace))

    print('I will now calculate the sum and average of three numbers.')
    n1 = input('Enter the 1st number: ')
    n2 = input('Enter the 2nd number: ')
    n3 = input('Enter the 3rd number: ')
    nsum = float(n1) + float(n2) + float(n3)
    print('The sum is {s:.3g} and the average is {a:.3g}.'.format(s=nsum, a=nsum/3))

def Practical_6():
    def f1(x):
        return 1 - 3 / (1 + x**2)

    answer( f1(np.asarray([0,1,2])) )

    f1z = opt.fsolve(f1, 1.5)
    answer( f1z )

    figure(1)
    fplot(f1, [0,3])
    hold(True)
    plot([f1z], [0], 'ro')
    hold(False)

    def f2(x):
        return 3 * np.sin(x) / (x**2 + 1) - 2 / (x**2 - 4*x + 5) + 1

    figure(2)
    fplot(f2, [-2,4])
    hold(True)

    for x0 in [-1.5, 0, 1.5, 3]:
        f2z = opt.fsolve(f2, x0)
        answer( f2z )
        plot([f2z], [0], 'ro')

    hold(False)

    def root_1_plus(x0, N):
        x = x0
        for n in range(0, N):
            x = math.sqrt(1 + x)
        return x

    answer( root_1_plus(2, 4) )
    answer( root_1_plus(3, 3) )
    answer( root_1_plus(5, 5) )

    print('Starting with a value x0, I will calculate 1 + sqrt(1 + x); I will do this n times.')
    x0 = input('Give me a starting value (x0): ')
    n  = input('How many times shall I do it: ')
    print('The answer is x={x:.5g}'.format(x=root_1_plus(float(x0), int(n))))

    print('Now I''m going to calculate a Fibonacci sequence, i.e., x_n = x_(n-1) + x_(n-2)')
    fn1 = input('Enter the 1st number: ')
    fn2 = input('Enter the 2nd number: ')
    fnN = input('Which term (N>2) shall I calculate: ')

    x_2 = float(fn1)
    x_1 = float(fn2)
    fiN = int(fnN)
    for n in range(3, fiN+1):
        x_0 = x_1 + x_2
        x_2 = x_1
        x_1 = x_0
    print('The Nth term (N={n}) is {x:.3g}.'.format(n=fiN, x=x_1))

def Practical_7():
    Nx =  41
    Ny = 101
    x = np.linspace(-1, 1, Nx) # or, for Nx =  41: np.arange(-100, 101, 5) / 100
    y = np.linspace( 0, 1, Ny) # or, for Ny = 101: np.arange(   0, 101) / 100

    Z = np.zeros((Ny,Nx))

    def dimple(x, y):
        radius_squared = x**2 + y**2
        return radius_squared * np.exp(-radius_squared)

    for r in range(0, Ny):
        for c in range(0, Nx):
            Z[r,c] = dimple(x[c], y[r])

    figure(1)
    surface(x, y, Z)
    title('Matrix plot of surface')

    figure(2)
    fsurf(dimple, [-2.5,2.5,0,2.5], resolution=(141,71), cmap=cm.jet)
    title('Function plot of surface')

    Temp = 20           # degrees C
    Diameter = 0.01     # m
    Density = 1E3       # kg/m3
    Viscosity = 1.01E-3 # kg/s/m

    v = input('Enter average flow speed [m/s]: ')
    Velocity = float(v)

    Reynolds = Density * Diameter * Velocity / Viscosity
    if Reynolds < 2000:
        print('The flow is laminar.')
    elif Reynolds > 3000:
        print('The flow is turbulent.')
    else:
        print('The flow is transitional.')

def Practical_8():
    data = csvread('accel_Dec0910_153854.csv', 1, 0)

    T = data[:,0]
    X = data[:,1]
    Y = data[:,2]
    Z = data[:,3]

    figure(1)
    plot(T,X,'r-')
    hold(True)
    plot(T,Y,'g-')
    plot(T,Z,'b-')
    legend(['X Accel','Y Accel','Z Accel'])
    hold(False)

    def index_at_time(t):
        return np.searchsorted(T, t)

    X_lo_start = index_at_time(32.0) # D
    X_lo_end   = index_at_time(38.9)
    X_hi_start = index_at_time(10.4) # B
    X_hi_end   = index_at_time(17.8)
    Y_lo_start = index_at_time(48.9) # F
    Y_lo_end   = index_at_time(57.3)
    Y_hi_start = index_at_time(61.3) # G
    Y_hi_end   = index_at_time(74.5)
    Z_l1_start = index_at_time( 0.0) # A
    Z_l1_end   = index_at_time( 8.8)
    Z_l2_start = index_at_time(40.1) # E
    Z_l2_end   = index_at_time(46.7)
    Z_l3_start = index_at_time(76.2) # H
    Z_l3_end   = index_at_time(87.0)
    Z_hi_start = index_at_time(19.4) # C
    Z_hi_end   = index_at_time(28.9)

    X_lo = X[X_lo_start:X_lo_end]
    X_hi = X[X_hi_start:X_hi_end]
    Y_lo = Y[Y_lo_start:Y_lo_end]
    Y_hi = Y[Y_hi_start:Y_hi_end]
    Z_l1 = Z[Z_l1_start:Z_l1_end]
    Z_l2 = Z[Z_l2_start:Z_l2_end]
    Z_l3 = Z[Z_l3_start:Z_l3_end]
    Z_hi = Z[Z_hi_start:Z_hi_end]

    Z_lo = np.append(Z_l1, Z_l2)
    Z_lo = np.append(Z_lo, Z_l3)

    print('X low  - mean: {m:.3g}'.format(m=np.mean(X_lo)))
    print('X high - mean: {m:.3g}'.format(m=np.mean(X_hi)))
    print('Y low  - mean: {m:.3g}'.format(m=np.mean(Y_lo)))
    print('Y high - mean: {m:.3g}'.format(m=np.mean(Y_hi)))
    print('Z low  - mean: {m:.3g}'.format(m=np.mean(Z_lo)))
    print('Z high - mean: {m:.3g}'.format(m=np.mean(Z_hi)))

    X0 = (np.mean(X_lo) + np.mean(X_hi)) / 2
    Y0 = (np.mean(Y_lo) + np.mean(Y_hi)) / 2
    Z0 = (np.mean(Z_lo) + np.mean(Z_hi)) / 2

    print('X zero: {m:.3g}'.format(m=X0))
    print('Y zero: {m:.3g}'.format(m=Y0))
    print('Z zero: {m:.3g}'.format(m=Z0))

    data = csvread('accel_Dec0710_164002.csv', 1, 0)

    T = data[:,0]
    X = data[:,1] - X0
    Y = data[:,2] - Y0
    Z = data[:,3] - Z0
    A = (X**2 + Y**2 + Z**2)**0.5
    G = np.degrees(np.arccos(-Z/A))
    N = len(T)

    reduced_T = []
    reduced_A = []
    reduced_G = []
    q = 0
    while N - q >= 100:
        reduced_T.append(T[q])
        reduced_A.append(np.mean(A[q:(q+100)]))
        reduced_G.append(np.mean(G[q:(q+100)]))
        q += 100

    # Proper Python plotting instead of baltam
    fig, (ax1, ax2) = plt.subplots(2)
    fig.suptitle('Manchester to Leeds: Accelerometer Data')
    ax1.plot(reduced_T, reduced_A, 'b-')
    ax1.set(ylabel='Acceleration [g]')
    ax2.plot(reduced_T, reduced_G, 'r-')
    ax2.set(xlabel='Time [s]', ylabel='Incline [deg]')

def Practical_9():
    answer( 1 - math.sin(math.pi/3)**2 )
    answer( math.log(100) )
    answer( math.log10(100) )
    answer( 4 * math.atan(1) )
    answer( math.exp(-0.75) )
    answer( math.sqrt(72.25) )
    answer( math.pow(343, 1/3) )
    answer( 10**math.pi )
    answer( math.cosh(math.log10(7))**2 - math.sinh(-math.log10(1/7))**2 )
    answer( cmath.asin(3).conjugate() + cmath.log(-3) ) # curious difference in behaviour between Python and Matlab with cmath.asin()

    def f(x):
        return x - 1 + np.exp(-x) # or: x + np.expm1(-x)

    figure(1)
    fplot(f, [0,2], 'b-')
    hold(True)
    xz = opt.fsolve(f, 0)
    answer( xz )
    plot([xz],[0],'ro')
    hold(False)

    def h(t):
        return np.exp(-3*t) * (3 * np.cos(t) - np.sin(t))

    figure(2)
    fplot(h, [0,2], 'b-')
    hold(True)
    xz = opt.fsolve(h, 1.25)
    answer( xz )
    plot([xz],[0],'ro')
    hold(False)

    def F(s):
        return 1 / (2 * s**2 + 1) - s / (s**2 + 1)

    figure(3)
    fplot(F, [0,2], 'b-')
    hold(True)
    xz = opt.fsolve(F, 0.75)
    answer( xz )
    plot([xz],[0],'ro')
    hold(False)

    def QI(u):
        return (np.arcsin(u+0j) + np.log(0j-u) - math.pi * 1j).imag

    figure(4)
    fplot(QI, [1E-6,2])

    def QR(u):
        return (np.arcsin(u+0j) + np.log(0j-u) - math.pi * 1j).real

    figure(5)
    fplot(QR, [1E-6,2], 'b-')
    hold(True)
    xz = opt.fsolve(QR, 0.5)
    answer( xz )
    plot([xz],[0],'ro')
    hold(False)

    answer( np.roots([1,3,-4]) )
    answer( np.roots([1,3,4]) )
    answer( np.roots([1,-2,2,1]) )
    answer( np.roots([1,1,0,0,1]) )
    answer( np.roots([1,-3,5,-3,1]) )

    answer( np.arange(1,11)**3 )
    answer( sum(np.arange(1,11)**3) )
    answer( -(1j)**np.arange(0,4) )
    answer( sum(-(1j)**np.arange(0,4)) )
    answer( 3**(0.0-np.arange(0,5)) )
    answer( sum(3**(0.0-np.arange(0,5))) )

    answer( np.arange(1,11)/10 )
    answer( np.arange(-6,7,4)/3 )
    answer( np.arange(-2,3)/6 )

def Practical_10():
    x_test = np.asarray([1,2,3])

    def f1(x):
        return np.log(1 + x + x**2)

    answer( f1(x_test) )

    def f2(x):
        return (x + 1) / x**2

    answer( f2(x_test) )

    def f3(x):
        return x**x + 1

    answer( f3(x_test) )

    def f4(x):
        return np.sinh(1 / x)

    answer( f4(x_test) )

    def fAll(x):
        return np.asarray([f1(x),f2(x),f3(x),f4(x)])

    figure(1)
    fplot(fAll, [0,3,0,5])
    legend(['log(1 + x + x**2)','(x + 1) / x**2','x**x + 1','sinh(1/x)'])
    xlabel('x')
    ylabel('y')
    title('Practical 10')

    def g(x,y):
        return np.exp(-(x**2 + y**2)/2) / math.sqrt(2 * math.pi)

    figure(2)
    fsurf(g,[-3,3,-3,3], resolution=(201,201))

    def F(u,v):
        return u**2 + u*v + v**2

    figure(3)
    fsurf(F,[-3,3,-3,3,-5,30], resolution=(201,201), cmap=cm.inferno, plot_type='surfc')

    def J(s,t):
        return s * np.cos(t) - t * np.cos(s)

    figure(4)
    fsurf(J,[-3,3,-3,3], resolution=(201,201), cmap=cm.winter, plot_type='cont2d')

    def f(x,y):
        return np.exp(-(x**2 + y**2)) * np.cos(6 * np.sqrt(x**2 + y**2))

    figure(5)
    fsurf(f,[-3,3,-3,3], resolution=(201,201), cmap=cm.jet, plot_type='cont3d')

def Practical_11():
    def sigma(t):
        return 81.4E6 * (1 - np.exp((np.sin(t) + t**2 - 4) / (t**4 + 4)))

    figure(1)
    fplot(sigma, [-10,10])
    t_min = opt.fmin(sigma, 5)
    answer( t_min )
    s_min = sigma(t_min)
    answer( s_min )

    def upside_down(t):
        return -sigma(t)

    t_max = opt.fmin(upside_down, 0)
    answer( t_max )
    s_max = sigma(t_max)
    answer( s_max )

    def DK(a):
        return 1.12 * (s_max - s_min) * np.sqrt(math.pi * a)

    def dadN(t, a):
        return 1E-11 * (DK(a)/1E6)**3

    T, Y = ode(dadN, [0, 30E6], 0.01E-3)
    answer( Y[-1] )
    figure(2)
    plot(T, Y, 'b-o')

def Practical_12():
    def dydt(t,y):
        return (1 - y) / (1 + t**2)

    T, Y = ode(dydt, [0,5], 0)
    answer( Y[-1] )

    def dGds(s, G):
        return np.log(1 + s**2)

    S, G = ode(dGds, [0,11], -1)
    answer( G[-1] )

    def dudv(v, u):
        return np.sinh(u) - np.cosh(v)

    V, U = ode(dudv, [-1,0.5], 1)
    answer( U[-1] )

    def dydx(x, y):
        return np.asarray([-y[1], y[0]])

    X, Y = ode(dydx, [0,3], [1,0])
    answer( Y[-1,0] )

    def dzdn(n, z):
        return np.asarray([z[0] - z[1], z[0] + z[1]])

    N, Z = ode(dzdn, [0.5,1.5], [0.5,-0.5])
    answer( Z[-1,1] )

    def b1_dydt(t, y):
        return np.asarray([3 * np.exp(-t) + 3 * y[0] - 2 * y[1], y[0]])

    T, B1_Y = ode(b1_dydt, [0,5], [1,0])
    answer( B1_Y[-1,1] )

    def b2_dydt(t, y):
        return np.asarray([3 * np.exp(-t) - 3 * y[0] - 2 * y[1], y[0]])

    T, B2_Y = ode(b2_dydt, [0,5], [1,0])
    answer( B2_Y[-1,1] )

    def b3_dydt(t, y):
        return np.asarray([3 * np.exp(-t) - 2 * y[0] - y[1], y[0]])

    T, B3_Y = ode(b3_dydt, [0,5], [1,0])
    answer( B3_Y[-1,1] )

    plot(T, B1_Y[:,1], 'b-')
    hold(True)
    plot(T, B2_Y[:,1], 'g-')
    plot(T, B3_Y[:,1], 'r-')
    legend(['1','2','3'])
    xlim([0,1])
    ylim([0,9])
    xlabel('Time, t')
    ylabel('y(t)')
    hold(False)

def Practical_13():
    def mabode(A, B):
        NA = len(A)
        NB = len(B)

        M = np.zeros((NB,NA))

        for row in range(NB):
            for col in range(NA):
                def dydt(t, y):
                    return np.asarray([y[0]**2 - y[1]**2 + A[col] * np.cos(2 * np.pi * t), 2 * y[0] * y[1] + B[row] * np.sin(2 * np.pi * t)])
                T, Y = ode(dydt, [0,1], [0,0])
                M[row,col] = np.linalg.norm(Y[-1,:])

        return M

    x = np.linspace(-2.5,  1.5,  80)
    y = np.linspace(-1.25, 1.25, 50)
    M = mabode(x, y)

    figure(1)
    surface(x, y, M, cmap=cm.seismic)

    def lorenz(r0, rho, t):
        def drdt(t, r):
            return np.asarray([10*(r[1]-r[0]), r[0]*(rho-r[2])-r[1], r[0]*r[1]-8*r[2]/3])

        T, R = ode(drdt, np.linspace(0,t,10000), r0)

        plot3(R[:,0], R[:,1], R[:,2], 'b-')

    figure(2)
    lorenz([1,1,1], 25, 100)

def Practical_14():
    A = np.asarray([[ 1, 2, 4],[-2,-1,-3],[-4,-3, 0]])
    B = np.asarray([[-2, 1, 0],[ 1, 0,-1],[ 0,-1, 2]])
    C = A + B

    A_inv = np.linalg.inv(A)
    C_inv = np.linalg.inv(C)

    answer(np.matmul(A,A), style='matrix')
    answer(36 * C_inv, style='matrix')
    answer(np.matmul(np.matmul(A_inv,B),A), style='matrix', sigfigs=5)

    B1 = np.asarray([[ 3, 2, 1],[ 5,-3,-3],[ 1,-1, 0]])
    b1 = np.asarray([14, 6, 1])
    answer(np.linalg.solve(B1, b1), style='matrix')

    B2 = np.asarray([[ 2,-3, 4],[ 1, 0,-7],[ 3,-2, 3]])
    b2 = np.asarray([ 6,-6, 6])
    answer(np.linalg.solve(B2, b2), style='matrix')

    values, vectors = np.linalg.eig(B)
    answer(values, style='matrix')
    answer(vectors, style='matrix')

    def inv2x2(A):
        det = A[0,0] * A[1,1] - A[1,0] * A[0,1]
        return np.asarray([[A[1,1],-A[0,1]],[-A[1,0],A[0,0]]]) / det

    A = np.random.rand(2,2)
    A_inv = inv2x2(A)
    answer(np.matmul(A_inv, A), style='matrix')

def Practical_15():
    def Hertz2DStress(p0, a, mu, x, z):
        """[sx,sz,tzx] = str2d(p0,a,mu,x,z)
            Routine to calculate stresses for Hertz 2D cylindrical contact
            p0  Peak contact pressure
            a   Semi-contact width
            mu  Friction coefficient
            x   Horizontal coordinate
            z   Vertical coordinate (+ve is down)
        """

        # need to normalize x & z w.r.t. semi-contact width a
        x   = x / a
        z   = z / a

        k1  = (1+x)**2 + z**2
        k2  = (1-x)**2 + z**2
        k   = np.sqrt(k2/k1)

        s   = (math.pi/k1)/k/np.sqrt(2*k + (k1 + k2 - 4)/k1)
        si  = s*(1-k)
        sib = s*(1+k)

        sx  =    - z/math.pi * ((1 + 2*x**2 + 2*z**2)*sib - 2*math.pi - 3*x*si)
        sx  = sx - (2*mu/math.pi)*((x**2 - 1 - 1.5*z**2)*si + math.pi*x)
        sx  = sx - (2*mu/math.pi)*((1 - x**2 - z**2)*x*sib)

        sz  =    - (z/math.pi)*(sib - x*si) - (mu/math.pi)*si*z**2

        tzx =     - (z**2/math.pi)*si
        tzx = tzx - (mu/math.pi)*((1 + 2*x**2 + 2*z**2)*z*sib - 2*math.pi*z - 3*x*z*si)

        sx  = p0 * sx
        sz  = p0 * sz
        tzx = p0 * tzx

        return sx, sz, tzx

    def Hertz2DContour(P, R, ECM, nu, mu, N):
        """Hertz2DContour (P,R,ECM,nu,mu,N)
           Plots contours of von Mises equivalent stress
           P    Load per unit length
           R    Equivalent radius
           ECM  Elastic contact modulus
           mu   Friction coefficient
           N    Number of points
        """

        # (1) Calculate and display semi-contact width, a
        a = math.sqrt((4 * P * R) / (math.pi * ECM))
        print('semi-contact width, a = {a:.4g}mm'.format(a=a*1000))

        # (2) Calculate and display peak pressure, p0
        p0 = math.sqrt((P * ECM) / (math.pi * R))
        print('peak pressure, p0 = {p:.4g}GPa'.format(p=p0/1E9))

        # Create vector of x values from -1.5a to 1.5a
        xmin = -1.5 * a
        xmax =  1.5 * a
        x = np.linspace(xmin, xmax, N)

        # Create vector of z values from 0 to 3a (avoiding zero - go for the midpoints)
        zmin = 3 * a * 0.5 / N
        zmax = 3 * a * (N - 0.5) / N
        z = np.linspace(zmin, zmax, N)

        # Create empty matrix for von Mises stress values
        sv = np.zeros((N,N))

        # (3) Loop through all X and Z values and calculate sv for each pair
        for row in range(N):
            for col in range(N):
                sx, sz, tzx = Hertz2DStress(p0, a, mu, x[col], z[row])

                sy  = nu * (sx + sz)

                I1 = sx + sy + sz
                I2 = sx * sy + sy * sz + sz * sx - tzx**2

                J2 = I2 - I1**2 / 3

                sv[row,col] = math.sqrt(-3 * J2)

        # (4) Create a contour plot of the X,Z,sv
        contour(x / a, z / a, sv / 1E9)
        xlabel('x / a')
        ylabel('z / a')
        title('Contours of von Mises stress [GPa]')

    Hertz2DContour(714000, 0.01175, 116E9, 0.3, 0.4, 100)

def Practical_16():
    def wave_animation(tf=10): # tf = 10 # final time
        A1 = 1 # wave amplitude [m]
        L1 = 4 # wave length [m]
        c1 = 8 # wave speed [m/s]

        A2 = 0.75 # wave amplitude [m]
        L2 = 3    # wave length [m]
        c2 = 12   # wave speed [m/s]

        def f1(x,t): # wave function
            return A1 * np.sin(2*math.pi*(x - c1*t)/L1)

        def f2(x,t): # wave function
            return A2 * np.sin(2*math.pi*(x - c2*t)/L2)

        t0 = 0     # initial time
        dt = 0.01  # time step in seconds

        X =  np.linspace(-L1, L1, 201) # position(s) [m]
        Y1 = f1(X, t0)                 # wave form at time t0
        Y2 = f2(X, t0)                 # wave form at time t0

        line_list = plot(X, Y1, 'b-')  # plot the initial wave form
        p1 = line_list[0]              # save the line handle as p1
        hold(True)
        line_list = plot(X, Y2, 'r-')  # plot the initial wave form
        p2 = line_list[0]              # save the line handle as p2
        xlim([-L1, L1])
        ylim([-A1, A1])
        hold(False)

        t = t0 # time t [s]
        while t < tf:
            plt.pause(dt) # stop in real time for the length of the time step
            t = t + dt    # increment time by the time step

            Y1 = f1(X, t)    # wave form at current time t
            p1.set_ydata(Y1) # update the existing plot line function data

            Y2 = f2(X, t)    # wave form at current time t
            p2.set_ydata(Y2) # update the existing plot line function data

            plt.draw() # tell the figure window to update

    def soliton_animation():
        A1 =  1 # wave amplitude [m]
        c1 = 16 # wave speed [m/s]
        L1 =  6

        A2 = 0.75 # wave amplitude [m]
        c2 = 8    # wave speed [m/s]

        def f1(x,t): # wave function
            return A1 / np.cosh(0.5 * c1**0.5 * (x - c1 * t))**2

        def f2(x,t): # wave function
            return A2 / np.cosh(0.5 * c2**0.5 * (x - c2 * t))**2

        t0 = -1.1  # initial time
        tf =  1.1  # final time
        dt = 0.01  # time step in seconds

        X =  np.linspace(-L1, L1, 201) # position(s) [m]
        Y1 = f1(X, t0)                 # wave form at time t0
        Y2 = f2(X, t0)                 # wave form at time t0

        line_list = plot(X, Y1, 'g--') # plot the initial wave form
        p1 = line_list[0]              # save the line handle as p1
        hold(True)
        line_list = plot(X, Y2, 'k--') # plot the initial wave form
        p2 = line_list[0]              # save the line handle as p2
        xlim([-L1, L1])
        ylim([  0, A1])
        hold(False)

        t = t0 # time t [s]
        while t < tf:
            plt.pause(dt) # stop in real time for the length of the time step
            t = t + dt    # increment time by the time step

            Y1 = f1(X, t)    # wave form at current time t
            p1.set_ydata(Y1) # update the existing plot line function data

            Y2 = f2(X, t)    # wave form at current time t
            p2.set_ydata(Y2) # update the existing plot line function data

            plt.draw() # tell the figure window to update

    figure(1)
    wave_animation(2) # 2 seconds duration
    figure(2)
    soliton_animation()

no = int(input('Which practical do you wish to run [1-16]? '))
if no == 1:
    Practical_1() # intro
if no == 2:
    Practical_2() # 
if no == 3:
    Practical_3() # 
if no == 4:
    Practical_4() # 
if no == 5:
    Practical_5() # 
if no == 6:
    Practical_6() # need scipy now
if no == 7:
    Practical_7() # surface plot
if no == 8:
    Practical_8() # csv files
if no == 9:
    Practical_9() # 
if no == 10:
    Practical_10() # 
if no == 11:
    Practical_11() # ODE
if no == 12:
    Practical_12() # 
if no == 13:
    Practical_13() # 3D plots
if no == 14:
    Practical_14() # matrices
if no == 15:
    Practical_15() # contour plot
if no == 16:
    Practical_16() # animations
