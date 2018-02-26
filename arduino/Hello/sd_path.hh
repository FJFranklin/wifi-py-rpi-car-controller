/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifdef CORE_TEENSY

#include <SdFat.h>

#define SD_PATH_MAX 255

extern void SD_Card_Info (uint8_t address_src);
extern void SD_Card_Erase (uint8_t address_src);
extern void SD_Card_Format (uint8_t address_src);

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

  void path (String & str) const; // append full path to string
private:
  bool fs_init (uint8_t address_src) const;
public:
  FatFile * open (uint8_t address_src) const;

  FatFile * mkdir (uint8_t address_src) const;

  bool ls (uint8_t address_src) const;

  static const SD_Path & pwd ();

  static void pwd (uint8_t address_src);
  static bool cd (uint8_t address_src, const char * path);
  static bool ls (uint8_t address_src, const char * path);
  static bool mkdir (uint8_t address_src, const char * path);
};

#endif /* CORE_TEENSY */
