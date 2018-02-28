#include <cstdio>

#define MESSAGE_BUFSIZE  256
#define MESSAGE_MAXSIZE  (MESSAGE_BUFSIZE-6)

class Message {
public:
  enum COBS_State {
    cobs_HavePacket = 0,
    cobs_InProgress,
    cobs_UnexpectedEOP,
    cobs_InvalidPacket,
    cobs_TooLong
  };

private:
  unsigned char buffer[MESSAGE_BUFSIZE];
  unsigned char offset;
  unsigned char cobsin;
public:
  inline void set_address_src (unsigned char address_src) {
    buffer[0] = address_src;
  }
  inline void set_address_dest (unsigned char address_dest) {
    buffer[1] = address_dest;
  }
  inline void set_command_id (unsigned char command_id) {
    buffer[2] = command_id;
  }
private:
  inline void set_length (unsigned char length) {
    buffer[3] = length;
  }
public:
  inline unsigned char get_address_src () const {
    return buffer[0];
  }
  inline unsigned char get_address_dest () const {
    return buffer[1];
  }
  inline unsigned char get_command_id () const {
    return buffer[2];
  }
  inline unsigned char get_length () const {
    return buffer[3];
  }

  inline void clear () {
    offset = 0;
    cobsin = 0;
    set_length (0);
  }

  Message (unsigned char address_src, unsigned char address_dest, unsigned char command_id) : 
    offset(0),
    cobsin(0)
  {
    set_address_src (address_src);
    set_address_dest (address_dest);
    set_command_id (command_id);
    set_length (0);
  }

  ~Message () {
    // ...
  }

  Message & operator+= (unsigned char uc);
  Message & operator+= (const char * right);
  Message & operator= (const char * right);

  void encode (unsigned char *& bytes, int & size);

  COBS_State decode (unsigned char c);
};

Message & Message::operator+= (unsigned char uc) {
  unsigned char length = get_length ();

  if (length < MESSAGE_MAXSIZE) {
    buffer[4+(length++)] = uc;
  }
  set_length (length);

  return *this;
}

Message & Message::operator+= (const char * right) {
  if (right) {
    unsigned char length = get_length ();
    unsigned char spaces = MESSAGE_MAXSIZE - length;

    while (spaces--) {
      if (!*right) break;
      buffer[4+(length++)] = *right++;
    }
    set_length (length);
  }
  return *this;
}

Message & Message::operator= (const char * right) {
  unsigned char length = 0;

  if (right) {
    unsigned char spaces = MESSAGE_MAXSIZE;

    while (spaces--) {
      if (!*right) break;
      buffer[4+(length++)] = *right++;
    }
    set_length (length);
  }
  return *this;
}

Message::COBS_State Message::decode (unsigned char c) {
  if (!c) { // EOP
    if (cobsin) { // we were expecting something non-zero
      clear ();   // reset
      return cobs_UnexpectedEOP;
    }
    if (offset < 4) { // invalid packet
      clear ();   // reset
      return cobs_InvalidPacket;
    }
    if (get_length () != (offset - 4)) { // invalid packet
      clear ();   // reset
      return cobs_InvalidPacket;
    }
    return cobs_HavePacket;
  }
  if (offset >= (MESSAGE_MAXSIZE + 4)) { // packet too long
    return cobs_TooLong;
  }
  if (cobsin) {
    --cobsin;
    buffer[offset++] = c;
  } else {
    cobsin = c - 1;
    buffer[offset++] = 0;
  }
  return cobs_InProgress;
}

void Message::encode (unsigned char *& bytes, int & size) {
  unsigned char * ptr1 = buffer + get_length () + 3;
  unsigned char * ptr2 = buffer + MESSAGE_BUFSIZE - 1;

  unsigned char count = 0;

  *ptr2 = 0; // EOP

  while (true) {
    if (*ptr1 == 0) {
      *--ptr2 = ++count;
      count = 0;
    } else {
      *--ptr2 = *ptr1;
      ++count;
    }
    if (ptr1 == buffer) {
      break;
    }
    --ptr1;
  }

  bytes = ptr2;
  size = MESSAGE_BUFSIZE - (ptr2 - buffer);
}

int main () {
  Message M(9,8,7);
  return 0;
}
