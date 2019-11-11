/* Copyright (c) 2019 Francis James Franklin
 * 
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided
 * that the following conditions are met:
 * 
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and
 *    the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
 *    the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
 * NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <errno.h>
#include <time.h>
#include <unistd.h>

#include <cstdio>
#include <cstring>

#include <mosquitto.h>

class Ticker {
private:
  bool bLoop;

  unsigned long time_secs;
  unsigned long time_nano;

  void get_time(unsigned long & secs, unsigned long & nano) {
    struct timespec ts;
    clock_gettime (CLOCK_MONOTONIC, &ts);
    secs = (unsigned long) ts.tv_sec;
    nano = (unsigned long) ts.tv_nsec;
  }
public:
  Ticker() : bLoop(true) {
    get_time(time_secs, time_nano);
  }
  virtual ~Ticker() {
    // ...
  }

  unsigned long millis () {
    unsigned long new_time_secs;
    unsigned long new_time_nano;
    get_time(new_time_secs, new_time_nano);

    unsigned long us = 0;

    if (new_time_nano < time_nano) {
      us  = (1000000000UL + new_time_nano - time_nano) / 1000000UL;
      us += 1000UL * (new_time_secs - time_secs - 1);
    } else {
      us  = (new_time_nano - time_nano) / 1000000UL;
      us += 1000UL * (new_time_secs - time_secs);
    }
    return us;
  }

  void stop() {
    bLoop = false;
  }
  void loop() {
    unsigned long ms0 = millis();

    bLoop = true;
    while (bLoop) {
      unsigned long ms1 = millis();

      if (ms0 != ms1) {
	ms0 = ms1;
	tick();
      }
      usleep(1);
    }
  }
  virtual void tick() {
    // ...
  }
};

class Client : public Ticker {
private:
  struct mosquitto * M;

  enum ConnectionStatus {
    cs_NoConnection = 0,
    cs_Disconnecting,
    cs_Connecting,
    cs_Connected
  } cs;
protected:
  const char * broker;
  int port;
  int mid;
  int keepalive;
  int qos;
  bool retain;
  bool verbose;
public:
  Client(const char * client_id) : cs(cs_NoConnection), broker("127.0.0.1"), port(1883),
				   mid(0), keepalive(60), qos(0), retain(false), verbose(false) {
    M = mosquitto_new(client_id, true, this);
  }
  virtual ~Client() {
    disconnect();
    mosquitto_destroy(M);
  }

private:
  static void s_on_connect(struct mosquitto * M, void * user_data, int rc) {
    Client * C = reinterpret_cast<Client *>(user_data);
    if (!rc) {
      if (C->verbose)
	fprintf(stdout, "client: connect: success\n");
      C->cs = cs_Connected;
    } else {
      if (C->verbose)
	fprintf(stdout, "client: connect: failed (%d)\n", rc);
      C->cs = cs_NoConnection;
    }
  }
public:
  bool connect() {
    mosquitto_connect_callback_set(M, Client::s_on_connect);

    if (cs != cs_NoConnection) {
      return false;
    }
    int result = mosquitto_connect(M, broker, port, keepalive);
    if (result == MOSQ_ERR_SUCCESS) {
      cs = cs_Connecting;
      return true;
    } else if (result == MOSQ_ERR_ERRNO) {
      if (verbose)
	fprintf(stdout, "client: connect[%s:%d]: error (%s)\n", broker, port, strerror(errno));
      return false;
    } else {
      if (verbose)
	fprintf(stdout, "client: connect: error (%d)\n", result);
      return false;
    }
  }
  inline bool connecting() const {
    return cs == cs_Connecting;
  }
  inline bool connected() const {
    return cs == cs_Connected;
  }

private:
  static void s_on_disconnect(struct mosquitto * M, void * user_data, int rc) {
    Client * C = reinterpret_cast<Client *>(user_data);
    if (C->verbose)
      fprintf(stdout, "client: disconnected (%d)\n", rc);
    C->cs = cs_NoConnection;
  }
public:
  void disconnect() {
    mosquitto_disconnect_callback_set(M, Client::s_on_disconnect);

    cs = cs_Disconnecting;
    mosquitto_disconnect(M);
  }

private:
  static void s_on_publish(struct mosquitto * M, void * user_data, int mid) {
    Client * C = reinterpret_cast<Client *>(user_data);
    if (C->verbose)
      fprintf(stdout, "client: %d published\n", mid);
  }
public:
  bool publish(const char * topic, const char * message) {
    mosquitto_publish_callback_set(M, Client::s_on_publish);

    mid = 0;
    if (mosquitto_publish(M, &mid, topic, strlen(message), message, qos, retain) == MOSQ_ERR_SUCCESS) {
      if (verbose)
	fprintf(stdout, "client: %d publishing...\n", mid);
      return true;
    } else {
      return false;
    }
  }

  virtual void message(const char * topic, const char * message, int length) {
    // ...
  }
private:
  static void s_on_message(struct mosquitto * M, void * user_data, const struct mosquitto_message * message) {
    Client * C = reinterpret_cast<Client *>(user_data);
    if (C->verbose)
      fprintf(stdout, "client: message received on topic %s\n", message->topic);
    C->message(message->topic, reinterpret_cast<const char *>(message->payload), message->payloadlen);
  }
  static void s_on_subscribe(struct mosquitto * M, void * user_data, int mid, int qos_count, const int * granted_qos) {
    Client * C = reinterpret_cast<Client *>(user_data);
    if (C->verbose)
      fprintf(stdout, "client: %d subscribed (%d)\n", mid, qos_count);
  }
public:
  bool subscribe(const char * pattern) {
    mosquitto_subscribe_callback_set(M, Client::s_on_subscribe);
    mosquitto_message_callback_set(M, Client::s_on_message);

    mid = 0;
    if (mosquitto_subscribe(M, &mid, pattern, qos) == MOSQ_ERR_SUCCESS) {
      if (verbose)
        fprintf(stdout, "client: %d subscribing...\n", mid);
      return true;
    } else {
      return false;
    }
  }

  virtual void setup() {
    // ...
  }
private:
  virtual void tick() {
    static bool bConnected = false;

    if (!connected()) {
      bConnected = false;
      if (!connecting()) {
	connect();
      }
    } else {
      if (!bConnected) {
	bConnected = true;
	setup();
      }
    }
    mosquitto_loop(M, 0, 1);
  }
};

class Car : public Client {
private:
  const char * base_pattern = "/wifi-py-rpi-car-controller/#";
  int base_length;
public:
  Car() : Client("car") {
    base_pattern = "/wifi-py-rpi-car-controller/#";
    base_length = strlen(base_pattern) - 1;
  }
  virtual ~Car() {
  }
  virtual void setup() {
    if (!subscribe(base_pattern)) {
      fprintf(stdout, "car: Failed to subscribe with pattern %s\n", base_pattern);
    }
  }
  virtual void message(const char * topic, const char * message, int length) {
    static char buf[32];

    if (length > 31) {
      length = 31;
    }
    strncpy(buf, message, length);
    buf[length] = 0;

    fprintf(stdout, "car: message=\"%s\" @ %s\n", buf, topic + base_length);
  }
};

int main(int argc, char ** argv) {
  Car C;
  C.loop();

  // client.subscribe ("/wifi-py-rpi-car-controller/car/XY");
  // message.destinationName = "/wifi-py-rpi-car-controller/system/exit";
  // message.destinationName = "/wifi-py-rpi-car-controller/dash/XY";

  return 0;
}
