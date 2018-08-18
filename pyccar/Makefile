all:	pyccar

runX:	pyccar
	PYTHONPATH=`pwd` ./pyccar

runhp:	pyccar
	PYTHONPATH=`pwd` ./pyccar --frame-buffer --hyperpixel

runtft:	pyccar
	PYTHONPATH=`pwd` ./pyccar --frame-buffer --fb-device=/dev/fb1 --touch-device=/dev/input/event3

clean:
	rm -f *~ *.o

pyccar:		pyccar.o TouchInput.o Window.o PyCCarUI.o
		c++ -o pyccar pyccar.o TouchInput.o Window.o PyCCarUI.o `python-config --ldflags`

pyccar.o:	pyccar.hh TouchInput.hh Window.hh pyccar.cc
		c++ -c pyccar.cc `python-config --cflags`

TouchInput.o:	pyccar.hh TouchInput.hh Window.hh TouchInput.cc
		c++ -c TouchInput.cc `python-config --cflags`

Window.o:	pyccar.hh TouchInput.hh Window.hh Window.cc
		c++ -c Window.cc `python-config --cflags`

PyCCarUI.o:	pyccar.hh PyCCarUI.cc
		c++ -c PyCCarUI.cc `python-config --cflags`
