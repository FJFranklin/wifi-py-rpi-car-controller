/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

/* Included directly by sd.cpp
 */

#include "util.hh"

#ifdef CORE_TEENSY

#include "sd_path.hh"

static SdFatSdio sd;

#include "sd_geometry.hh"

static SD_Path s_path_cwd;
static SD_Path s_path_tmp;

void SD_Card_Info (uint8_t address_src) { // FIXME / TODO
  Message response;

  if (!sd.card()->begin ()) {
    response.text = "SD: Unable to initialise card.";
    response.send (address_src);
  } else {
    bool bSDHC = (sd.card()->type () == SD_CARD_TYPE_SDHC);

    if (!bSDHC) {
      response.text = "SD (FAT16): ";
    } else {
      response.text = "SDHC (FAT32): ";
    }

    uint32_t block_count = sd.card()->cardSize (); // no. of 512-byte blocks

    response.text += String (block_count);
    response.text += " (512-byte) blocks = ";
    response.text += String (block_count / 2048);
    response.text += "MB";
    response.send (address_src);
  }
}

void SD_Card_Erase (uint8_t address_src) {
  SD_Geometry::erase (address_src);
}
void SD_Card_Format (uint8_t address_src) {
  SD_Geometry::format (address_src);
}

SD_Path::SD_Path () :
  m_length(0),
  m_count(0)
{
  // ...
}

SD_Path::~SD_Path ()
{
  // ...
}

void SD_Path::clear () { // back to root
  m_length = 0;
  m_count = 0;
}

const char * SD_Path::folder (uint16_t n) const { // where n = 1 .. count
  const char * f = "/";

  if (n > m_count) {
    f = 0;
  } else if (n) {
    f = m_path;

    while (--n) {
      while (*f++);
    }
  }
  return f;
}

void SD_Path::pop () {
  if (!m_count) {
    return;
  }
    
  const char * f = m_path;

  uint16_t n = m_count--;

  while (--n) {
    while (*f++);
  }
  m_length = f - m_path;
}

bool SD_Path::push (const char * name, uint8_t length) {
  if (*name == '.') { // first check special cases
    if (length == 1) { // do nothing
      return true;
    }
    if ((length == 2) && (*(name + 1) == '.')) { // go to parent
      pop ();
      return true;
    }
  }

  if (SD_PATH_MAX - m_length < length) return false;

  memcpy (m_path + m_length, name, length);
  m_length += length;
  m_path[m_length++] = 0;
  ++m_count;
  return true;
}

bool SD_Path::push (const char * name) {
  if (!name) return false;

  const char * ptr1 = name;

  bool bOkay = true;

  while (true) {
    const char * ptr2 = ptr1;

    while (*ptr2 && (*ptr2 != '/')) {
      ++ptr2;
    }
    if (ptr2 == ptr1) { // zero-length path component
      bOkay = false;
      break;
    }
    if (ptr2 - ptr1 > 12) { // path component too long; ignoring long file names here // TODO ??
      bOkay = false;
      break;
    }
    if (!push (ptr1, ptr2 - ptr1)) {
      bOkay = false;
      break;
    }
    if (*ptr2 == '/') {
      ptr1 = ptr2 + 1;
    } else {
      break;
    }
  }
  return bOkay;
}

void SD_Path::path (String & str) const { // append full path to string
  if (!m_count) {
    str += "/";
  } else {
    const char * f = m_path;

    uint16_t n = m_count;

    while (n--) {
      str += "/";
      str += f;
      while (*f++);
    }
  }
}

bool SD_Path::fs_init (uint8_t address_src) const {
  bool bOkay = true;

  if (!FatFile::cwd ()) {
    if (!sd.begin ()) {
      Message response;
      response.text = "SD: Unable to initialise SD device.";
      response.send (address_src);
      bOkay = false;
    }
  }
  return bOkay;
}

FatFile * SD_Path::open (uint8_t address_src) const {
  if (!fs_init (address_src)) {
    return 0;
  }

  Message response;

  FatVolume * vol = sd.vol ();

  if (!vol) {
    response.text = "SD: No volume available.";
    response.send (address_src);
    return 0;
  }

  FatFile * dir  = new FatFile;
  FatFile * file = new FatFile;

  bool bOkay = true;

  if (!dir || !file) {
    response.text = "Memory error.";
    response.send (address_src);
    bOkay = false;
  } else if (!dir->openRoot (vol)) {
    response.text = "SD: Unable to open volume root.";
    response.send (address_src);
    bOkay = false;
  } else {
    const char * f = m_path;

    for (uint16_t n = 1; n <= m_count; n++) {
      if (!file->open (dir, f, O_READ)) {
	response.text  = "SD: Unable to open '";
	response.text += f;
	response.text += "'.";
	response.send (address_src);
	bOkay = false;
	break;
      }
      if (!file->isDir ()) {
	response.text  = "SD: '";
	response.text += f;
	response.text += "' exists but is not a folder.";
	response.send (address_src);
	bOkay = false;
	break;
      }
      dir->close ();

      FatFile * tmp = dir;
      dir = file;
      file = tmp;

      while (*f++);
    }
  }
  if (bOkay) {
    delete file;
    return dir;
  }

  if (dir)  delete dir;
  if (file) delete file;
  return 0;
}

FatFile * SD_Path::mkdir (uint8_t address_src) const {
  if (!fs_init (address_src)) {
    return 0;
  }

  Message response;

  FatVolume * vol = sd.vol ();

  if (!vol) {
    response.text = "SD: No volume available.";
    response.send (address_src);
    return 0;
  }

  FatFile * dir  = new FatFile;
  FatFile * file = new FatFile;

  bool bOkay = true;

  if (!dir || !file) {
    response.text = "Memory error.";
    response.send (address_src);
    bOkay = false;
  } else if (!dir->openRoot (vol)) {
    response.text = "SD: Unable to open volume root.";
    response.send (address_src);
    bOkay = false;
  } else {
    const char * f = m_path;

    for (uint16_t n = 1; n <= m_count; n++) {
      if (file->open (dir, f, O_READ)) {
	if (!file->isDir ()) {
	  response.text  = "SD: '";
	  response.text += f;
	  response.text += "' exists but is not a folder.";
	  response.send (address_src);
	  bOkay = false;
	  break;
	}
      } else { // we need to create a new folder
	if (!file->mkdir (dir, f, false)) {
	  response.text  = "SD: Unable to create folder '";
	  response.text += f;
	  response.text += "'.";
	  response.send (address_src);
	  bOkay = false;
	  break;
	}
      }
      dir->close ();

      FatFile * tmp = dir;
      dir = file;
      file = tmp;

      while (*f++);
    }
  }
  if (bOkay) {
    delete file;
    return dir;
  }

  if (dir)  delete dir;
  if (file) delete file;
  return 0;
}

bool SD_Path::ls (uint8_t address_src) const {
  FatFile * dir = open (address_src);
  if (!dir) {
    return false;
  }

  Message response;
  path (response.text);
  response.text += ":";
  response.send (address_src);

  bool bOkay = true;

  FatFile entry;
      
  char buffer[16];

  while (bOkay) {
    if (!entry.openNext (dir)) {
      break;
    }

    sprintf (buffer, "%13lu ", entry.fileSize ());

    if (entry.isDir ()) {
      buffer[1] = 'd';
    } else {
      buffer[1] = '-';
    }
    response.text = buffer;

    if (!entry.getSFN (buffer)) {
      response.text = "SD: Unable to get short file name.";
      bOkay = false;
    } else {
      response.text += buffer;
    }
    response.send (address_src);

    entry.close ();
  }
  delete dir;
  return bOkay;
}

/* Static functions
 */
const SD_Path & SD_Path::pwd () {
  return s_path_cwd;
}

void SD_Path::pwd (uint8_t address_src) {
  Message response;
  s_path_cwd.path (response.text);
  response.send (address_src);
}

bool SD_Path::cd (uint8_t address_src, const char * path) {
  if (!path) return false;

  bool bSetRoot = false;

  if (*path == '/') { // an absolute path
    s_path_tmp.clear ();
    if (!(*++path)) { // allow "/" by itself
      bSetRoot = true;
    }
  } else {
    s_path_tmp = s_path_cwd;
  }

  Message response;

  if (!bSetRoot) {
    if (!s_path_tmp.push (path)) {
      response.text  = "SD: Invalid path: '";
      response.text += path;
      response.text += "'.";
      response.send (address_src);
      return false;
    }
  }

  bool bOkay = true;

  FatFile * dir = s_path_tmp.open (address_src);

  if (!dir) {
    bOkay = false;
  } else {
    if (!FatFile::setCwd (dir)) {
      response.text = "SD: Unable to change working directory.";
      response.send (address_src);
      bOkay = false;
    } else {
      s_path_cwd = s_path_tmp;
    }
    delete dir;
  }
  return bOkay;
}

bool SD_Path::ls (uint8_t address_src, const char * path) {
  if (!path) {
    return false;
  }

  bool bSetRoot = false;

  if (*path == '/') { // an absolute path
    s_path_tmp.clear ();
    if (!(*++path)) { // allow "/" by itself
      bSetRoot = true;
    }
  } else {
    s_path_tmp = s_path_cwd;
  }

  Message response;

  if (!bSetRoot) {
    if (!s_path_tmp.push (path)) {
      response.text  = "SD: Invalid path: '";
      response.text += path;
      response.text += "'.";
      response.send (address_src);
      return false;
    }
  }
  return s_path_tmp.ls (address_src);
}

bool SD_Path::mkdir (uint8_t address_src, const char * path) {
  if (!path) return false;

  if (*path == '/') { // an absolute path
    s_path_tmp.clear ();
    if (!(*++path)) { // allow "/" by itself - but root has to exist anyway
      return true;
    }
  } else {
    s_path_tmp = s_path_cwd;
  }
  if (!(*path)) {
    return false;
  }

  Message response;

  if (!s_path_tmp.push (path)) {
    response.text  = "SD: Invalid path: '";
    response.text += path;
    response.text += "'.";
    response.send (address_src);
    return false;
  }

  bool bOkay = true;

  FatFile * dir = s_path_tmp.mkdir (address_src);

  if (!dir) {
    response.text  = "SD: mkdir: Failed to create '";
    response.text += path;
    response.text += "'.";
    response.send (address_src);
    bOkay = false;
  } else {
    delete dir;
  }
  return bOkay;
}

#endif /* CORE_TEENSY */
