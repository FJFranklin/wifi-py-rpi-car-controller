#include <cstdio>

#define BUFSIZE  256
#define MAXSIZE  (BUFSIZE-6)

class Message {
private:
  unsigned char buffer[256];
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

  Message (unsigned char address_src, unsigned char address_dest, unsigned char command_id) {
    set_address_src (address_src);
    set_address_dest (address_dest);
    set_command_id (command_id);
    set_length (0);
  }

  ~Message () {
    // ...
  }

  inline Message & operator+= (const char * right) {
    if (right) {
      unsigned char length = get_length ();
      unsigned char spaces = MAXSIZE - length;

      while (spaces--) {
	if (!*right) break;
	buffer[4+(length++)] = *right++;
      }
      set_length (length);
    }
    return *this;
  }

  inline Message & operator= (const char * right) {
    unsigned char length = 0;

    if (right) {
      unsigned char spaces = MAXSIZE;

      while (spaces--) {
	if (!*right) break;
	buffer[4+(length++)] = *right++;
      }
      set_length (length);
    }
    return *this;
  }

  void print () {
    unsigned char length = get_length ();
    
    for (unsigned char c = 0; c < length; c++) {
      fputc (buffer[4+c], stdout);
    }
  }
};

int main (int /* argc */, char ** /* argv */) {
  Message M(1,2,3);

  M = "The quick brown fox jumps over the lazy dog.";
  M.print ();
  M += "\n";
  M += "The quick brown fox jumps over the lazy dog.";
  M += "The quick brown fox jumps over the lazy dog.";
  M += "The quick brown fox jumps over the lazy dog.";
  M += "\n";
  M.print ();

  return 0;
}
