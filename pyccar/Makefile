all:	pyccar

pyccar:	pyccar.cc pyccar.hh TouchInput.hh Timer.hh Window.hh
	c++ -o pyccar pyccar.cc `python-config --cflags --ldflags`

run:
	PYTHONPATH=/home/pi/wifi-py-rpi ./pyccar
