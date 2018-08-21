ifneq ("$(wildcard /usr/include/linux/input.h)","")
LINUX_INPUT=1
else
LINUX_INPUT=0
endif

CFLAGS=$(shell python-config --cflags) -DHAVE_LINUX_INPUT_H=$(LINUX_INPUT)

all:	pyccar

runX:	pyccar
	PYTHONPATH=`pwd` ./pyccar

runhp:	pyccar
	PYTHONPATH=`pwd` ./pyccar --fb-touch

runtft:	pyccar
	PYTHONPATH=`pwd` ./pyccar --fb-touch --fb-device=/dev/fb1

clean:
	rm -f *~ *.o

pyccar:		pyccar.o TouchInput.o Window.o PyCCarUI.o
		c++ -o pyccar pyccar.o TouchInput.o Window.o PyCCarUI.o `python-config --ldflags`

pyccar.o:	pyccar.hh TouchInput.hh Window.hh pyccar.cc
		c++ -c pyccar.cc $(CFLAGS)

TouchInput.o:	pyccar.hh TouchInput.hh Window.hh TouchInput.cc
		c++ -c TouchInput.cc $(CFLAGS)

Window.o:	pyccar.hh TouchInput.hh Window.hh Window.cc
		c++ -c Window.cc $(CFLAGS)

PyCCarUI.o:	pyccar.hh PyCCarUI.cc
		c++ -c PyCCarUI.cc $(CFLAGS)
