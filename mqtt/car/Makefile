HEADERS = \
	Ticker.hh \
	Client.hh

SOURCES = \
	Ticker.cc \
	Client.cc \
	car.cc

car:	$(HEADERS) $(SOURCES)
	c++ -o car $(SOURCES) -lmosquitto

clean:
	rm *.o
