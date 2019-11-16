CPPFLAGS=-I/usr/local/Cellar/mosquitto/1.6.7/include
LDFLAGS=-L/usr/local/Cellar/mosquitto/1.6.7/lib

HEADERS = \
	Ticker.hh \
	Serial.hh \
	Client.hh

SOURCES = \
	Ticker.cc \
	Serial.cc \
	Client.cc \
	car.cc

car:	$(HEADERS) $(SOURCES)
	c++ -o car $(SOURCES) $(CPPFLAGS) $(LDFLAGS) -lmosquitto

clean:
	rm *.o
