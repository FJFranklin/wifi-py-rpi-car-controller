/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifndef ArduinoHello_message_hh
#define ArduinoHello_message_hh

#define ADDRESS_UNKNOWN    0x7f
#define ADDRESS_BROADCAST  0x80

#define MESSAGE_BUFSIZE  256
#define MESSAGE_MAXSIZE  (MESSAGE_BUFSIZE-6) // maximum message data length is therefore 250 characters
                                             // which must therefore be the maximum allowable path length

class Message {
public:
  enum MessageType {
    Raw_Data          =  0, // Not part of the network

    /* Networking
     */
    Request_Address   =  1, // For external connections to the network
    Supply_Address    =  2, // Requested address
    Broadcast_Address =  3, // Once you have an address, tell everyone what it is
    No_Route          =  4, // Address not recognised / not on network
    Ping              =  5, // Send ping ...
    Pong              =  6, //           ... ping received.

    /* User interface commands & messages
     */
    User_Interrupt    = 10,
    Text_Command      = 11,
    Text_Response     = 12,
    Text_Error        = 13
  };

  enum COBS_State {
    cobs_HavePacket = 0,
    cobs_InProgress,
    cobs_UnexpectedEOP,
    cobs_InvalidPacket,
    cobs_TooLong
  };

private:
  uint8_t buffer[MESSAGE_BUFSIZE];
  uint8_t offset;
  uint8_t cobsin;
public:
  inline void set_address_src (uint8_t address_src) {
    buffer[0] = address_src;
  }
  inline void set_address_dest (uint8_t address_dest) {
    buffer[1] = address_dest;
  }
  inline void set_type (MessageType type) {
    buffer[2] = (uint8_t) type;
  }
private:
  inline void set_length (uint8_t length) {
    buffer[3] = length;
  }
public:
  inline uint8_t get_address_src () const {
    return buffer[0];
  }
  inline uint8_t get_address_dest () const {
    return buffer[1];
  }
  inline MessageType get_type () const {
    return (MessageType) buffer[2];
  }
  inline uint8_t get_length () const {
    return buffer[3];
  }
  inline uint8_t * get_buffer () {
    return buffer + 4;
  }
  inline const char * c_str () const {
    return (const char *) (buffer + 4);
  }
  inline void clear () {
    offset = 0;
    cobsin = 0;
    set_length (0);
    buffer[4] = 0;
  }

  Message (uint8_t address_src = ADDRESS_UNKNOWN, uint8_t address_dest = ADDRESS_UNKNOWN, MessageType type = Text_Response) : 
    offset(0),
    cobsin(0)
  {
    set_address_src (address_src);
    set_address_dest (address_dest);
    set_type (type);
    set_length (0);
    buffer[4] = 0;
  }

  ~Message () {
    // ...
  }

  Message & operator-- ();

  Message & operator+= (uint8_t uc);
  Message & operator+= (const char * right);
  Message & operator= (const char * right);

  Message & append_lu (unsigned long i); // change number to string, and append
  Message & append_int (int i);          // change number to string, and append
  Message & append_hex (uint8_t i);      // change number to string, and append

#ifndef COBS_USER // For the Arduino
  Message & pgm (const char * str);      // append string stored in PROGMEM

  void pgm_list (const char ** list);    // send list of text messages stored in PROGMEM
#endif

  void send ();

  void encode (uint8_t *& bytes, int & size);

  COBS_State decode (uint8_t c);
};

#endif /* !ArduinoHello_message_hh */
