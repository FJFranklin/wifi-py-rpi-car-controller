all:	pyccar

pyccar:	pyccar.cc pyccar.hh TouchInput.o Window.o
	c++ -o pyccar pyccar.cc TouchInput.o Window.o `python-config --cflags --ldflags`

TouchInput.o:	TouchInput.hh TouchInput.cc
		c++ -c TouchInput.cc `python-config --cflags`

Window.o:	TouchInput.hh Window.hh Window.cc
		c++ -c Window.cc `python-config --cflags`

run:
	PYTHONPATH=/home/pi/wifi-py-rpi ./pyccar

clean:
	rm -f *~ *.o
