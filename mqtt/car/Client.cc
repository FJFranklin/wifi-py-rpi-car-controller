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

#include <cstdio>
#include <cstring>
#include <cerrno>

#include <mosquitto.h>

#include "Client.hh"

Client::Client(const char * client_id, bool verbose) :
  m_cs(cs_NoConnection),
  m_broker("127.0.0.1"),
  m_port(1883),
  m_mid(0),
  m_keepalive(60),
  m_qos(0),
  m_retain(false),
  m_verbose(verbose)
{
  m_M = mosquitto_new(client_id, true, this);
}

Client::~Client() {
  disconnect();
  mosquitto_destroy(m_M);
}

void Client::s_on_connect(struct mosquitto * M, void * user_data, int rc) {
  Client * C = reinterpret_cast<Client *>(user_data);

  if (!rc) {
    if (C->verbose())
      fprintf(stdout, "client: connect: success\n");
    C->m_cs = cs_Connected;
  } else {
    if (C->verbose())
      fprintf(stdout, "client: connect: failed (%d)\n", rc);
    C->m_cs = cs_NoConnection;
  }
}

bool Client::connect() {
  mosquitto_connect_callback_set(m_M, Client::s_on_connect);

  if (m_cs != cs_NoConnection) {
    return false;
  }

  int result = mosquitto_connect(m_M, m_broker, m_port, m_keepalive);
  if (result == MOSQ_ERR_SUCCESS) {
    m_cs = cs_Connecting;
    return true;
  } else if (result == MOSQ_ERR_ERRNO) {
    if (verbose())
      fprintf(stdout, "client: connect[%s:%d]: error (%s)\n", m_broker, m_port, strerror(errno));
    return false;
  } else {
    if (verbose())
      fprintf(stdout, "client: connect: error (%d)\n", result);
    return false;
  }
}

void Client::s_on_disconnect(struct mosquitto * M, void * user_data, int rc) {
  Client * C = reinterpret_cast<Client *>(user_data);
  if (C->verbose())
    fprintf(stdout, "client: disconnected (%d)\n", rc);
  C->m_cs = cs_NoConnection;
}

void Client::disconnect() {
  mosquitto_disconnect_callback_set(m_M, Client::s_on_disconnect);

  m_cs = cs_Disconnecting;
  mosquitto_disconnect(m_M);
}

void Client::s_on_publish(struct mosquitto * M, void * user_data, int mid) {
  Client * C = reinterpret_cast<Client *>(user_data);
  if (C->verbose())
    fprintf(stdout, "client: %d published\n", mid);
}

bool Client::publish(const char * topic, const char * message) {
  mosquitto_publish_callback_set(m_M, Client::s_on_publish);

  m_mid = 0;
  if (mosquitto_publish(m_M, &m_mid, topic, strlen(message), message, m_qos, m_retain) == MOSQ_ERR_SUCCESS) {
    if (verbose())
      fprintf(stdout, "client: %d publishing...\n", m_mid);
    return true;
  } else {
    return false;
  }
}

void Client::message(const char * topic, const char * message, int length) {
  // ...
}

void Client::s_on_message(struct mosquitto * M, void * user_data, const struct mosquitto_message * message) {
  Client * C = reinterpret_cast<Client *>(user_data);
  if (C->verbose())
    fprintf(stdout, "client: message received on topic %s\n", message->topic);
  C->message(message->topic, reinterpret_cast<const char *>(message->payload), message->payloadlen);
}

void Client::s_on_subscribe(struct mosquitto * M, void * user_data, int mid, int qos_count, const int * granted_qos) {
  Client * C = reinterpret_cast<Client *>(user_data);
  if (C->verbose())
    fprintf(stdout, "client: %d subscribed (%d)\n", mid, qos_count);
}

bool Client::subscribe(const char * pattern) {
  mosquitto_subscribe_callback_set(m_M, Client::s_on_subscribe);
  mosquitto_message_callback_set(m_M, Client::s_on_message);

  m_mid = 0;
  if (mosquitto_subscribe(m_M, &m_mid, pattern, m_qos) == MOSQ_ERR_SUCCESS) {
    if (verbose())
      fprintf(stdout, "client: %d subscribing...\n", m_mid);
    return true;
  } else {
    return false;
  }
}

void Client::setup() {
  // ...
}

void Client::tick() {
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
  mosquitto_loop(m_M, 0, 1);
}
