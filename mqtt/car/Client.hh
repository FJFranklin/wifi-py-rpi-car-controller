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

#ifndef Car_Client_hh
#define Car_Client_hh

#include "Ticker.hh"

struct mosquitto;

class Client : public Ticker {
private:
  struct mosquitto * m_M;

  enum ConnectionStatus {
    cs_NoConnection = 0,
    cs_Disconnecting,
    cs_Connecting,
    cs_Connected
  } m_cs;

protected:
  const char * m_broker;

  int m_port;
private:
  int m_mid;
protected:
  int m_keepalive;
  int m_qos;

  bool m_retain;
private:
  bool m_verbose;

public:
  Client(const char * client_id, bool verbose=false);

  virtual ~Client();

  inline bool verbose() const {
    return m_verbose;
  }

private:
  static void s_on_connect(struct mosquitto * M, void * user_data, int rc);
public:
  bool connect();

  inline bool connecting() const {
    return m_cs == cs_Connecting;
  }
  inline bool connected() const {
    return m_cs == cs_Connected;
  }

private:
  static void s_on_disconnect(struct mosquitto * M, void * user_data, int rc);
public:
  void disconnect();

private:
  static void s_on_publish(struct mosquitto * M, void * user_data, int mid);
public:
  bool publish(const char * topic, const char * message);

  virtual void message(const char * topic, const char * message, int length);
private:
  static void s_on_message(struct mosquitto * M, void * user_data, const struct mosquitto_message * message);

  static void s_on_subscribe(struct mosquitto * M, void * user_data, int mid, int qos_count, const int * granted_qos);
public:
  bool subscribe(const char * pattern);

  virtual void setup();
  virtual void tick();
};

#endif /* ! Car_Client_hh */
