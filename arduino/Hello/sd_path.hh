/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifndef ArduinoHello_sd_path_hh
#define ArduinoHello_sd_path_hh

#include "util.hh"

#ifdef CORE_TEENSY

#include <SdFat.h>

#define SD_PATH_MAX MESSAGE_MAXSIZE // maximum length of path, i.e., 250
#define SD_FILE_MAX 63              // maximum length of filename - an arbitrary choice here; arguably should be (SD_PATH_MAX-1)

extern void SD_Card_Info (Message & response);
extern void SD_Card_Erase (Message & response);
extern void SD_Card_Format (Message & response);

class SD_Path {
private:
  char m_path[SD_PATH_MAX+1];

  uint16_t m_length; // buffer used
  uint16_t m_count;  // number of folders in path

public:
  SD_Path ();

  ~SD_Path ();

  void clear (); // back to root

  inline uint16_t count () const {
    return m_count;
  }

  const char * folder (uint16_t n) const; // where n = 1 .. count

  void pop ();
private:
  bool push (const char * name, uint8_t length);
public:
  bool push (const char * name);

  void path (Message & M) const; // append full path to message
private:
  bool fs_init (Message & response) const;
public:
  FatFile * open (Message & response) const;

  FatFile * mkdir (Message & response) const;

  bool ls (Message & response) const;

  static const SD_Path & pwd ();

  static void pwd (Message & response);
  static bool cd (Message & response, const char * path);
  static bool ls (Message & response, const char * path);
  static bool mkdir (Message & response, const char * path);
  static bool rmdir (Message & response, const char * path);
};

#endif /* CORE_TEENSY */

#endif /* ! ArduinoHello_sd_path_hh */
