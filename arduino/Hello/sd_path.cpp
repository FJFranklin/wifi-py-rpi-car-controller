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

void SD_Card_Info (Message & response) { // FIXME / TODO
  if (!sd.card()->begin ()) {
    response.set_type (Message::Text_Error);
    response = "SD: Unable to initialise card.";
    response.send ();
  } else {
    bool bSDHC = (sd.card()->type () == SD_CARD_TYPE_SDHC);

    if (!bSDHC) {
      response = "SD (FAT16): ";
    } else {
      response = "SDHC (FAT32): ";
    }

    uint32_t block_count = sd.card()->cardSize (); // no. of 512-byte blocks

    response.append_lu (block_count);
    response += " (512-byte) blocks = ";
    response.append_lu (block_count / 2048);
    response += " MB";
    response.send ();
  }
}

void SD_Card_Erase (Message & response) {
  SD_Geometry::erase (response);
}
void SD_Card_Format (Message & response) {
  SD_Geometry::format (response);
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
    if (ptr2 - ptr1 > SD_FILE_MAX) { // path component too long
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

void SD_Path::path (Message & M) const { // append full path to string
  if (!m_count) {
    M += "/";
  } else {
    const char * f = m_path;

    uint16_t n = m_count;

    while (n--) {
      M += "/";
      M += f;
      while (*f++);
    }
  }
}

bool SD_Path::fs_init (Message & response) const {
  bool bOkay = true;

  if (!FatFile::cwd ()) {
    if (!sd.begin ()) {
      response.set_type (Message::Text_Error);
      response = "SD: Unable to initialise SD device.";
      response.send ();
      bOkay = false;
    }
  }
  return bOkay;
}

FatFile * SD_Path::open (Message & response) const {
  if (!fs_init (response)) {
    return 0;
  }

  FatVolume * vol = sd.vol ();

  if (!vol) {
    response.set_type (Message::Text_Error);
    response = "SD: No volume available.";
    response.send ();
    return 0;
  }

  FatFile * dir  = new FatFile;
  FatFile * file = new FatFile;

  bool bOkay = true;

  if (!dir || !file) {
    response.set_type (Message::Text_Error);
    response = "Memory error.";
    response.send ();
    bOkay = false;
  } else if (!dir->openRoot (vol)) {
    response.set_type (Message::Text_Error);
    response = "SD: Unable to open volume root.";
    response.send ();
    bOkay = false;
  } else {
    const char * f = m_path;

    for (uint16_t n = 1; n <= m_count; n++) {
      if (!file->open (dir, f, O_READ)) {
	response.set_type (Message::Text_Error);
	response  = "SD: Unable to open '";
	response += f;
	response += "'.";
	response.send ();
	bOkay = false;
	break;
      }
      if (!file->isDir ()) {
	response.set_type (Message::Text_Error);
	response  = "SD: '";
	response += f;
	response += "' exists but is not a folder.";
	response.send ();
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

FatFile * SD_Path::mkdir (Message & response) const {
  if (!fs_init (response)) {
    return 0;
  }

  FatVolume * vol = sd.vol ();

  if (!vol) {
    response.set_type (Message::Text_Error);
    response = "SD: No volume available.";
    response.send ();
    return 0;
  }

  FatFile * dir  = new FatFile;
  FatFile * file = new FatFile;

  bool bOkay = true;

  if (!dir || !file) {
    response.set_type (Message::Text_Error);
    response = "Memory error.";
    response.send ();
    bOkay = false;
  } else if (!dir->openRoot (vol)) {
    response.set_type (Message::Text_Error);
    response = "SD: Unable to open volume root.";
    response.send ();
    bOkay = false;
  } else {
    const char * f = m_path;

    for (uint16_t n = 1; n <= m_count; n++) {
      if (file->open (dir, f, O_READ)) {
	if (!file->isDir ()) {
	  response.set_type (Message::Text_Error);
	  response  = "SD: '";
	  response += f;
	  response += "' exists but is not a folder.";
	  response.send ();
	  bOkay = false;
	  break;
	}
      } else { // we need to create a new folder
	if (!file->mkdir (dir, f, false)) {
	  response.set_type (Message::Text_Error);
	  response  = "SD: Unable to create folder '";
	  response += f;
	  response += "'.";
	  response.send ();
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

bool SD_Path::ls (Message & response) const {
  FatFile * dir = open (response);
  if (!dir) {
    return false;
  }

  Message listing(response.get_address_src (), response.get_address_dest ());
  path (listing);
  listing += ":";
  listing.send ();

  bool bOkay = true;

  FatFile entry;
      
  char buffer[SD_FILE_MAX+1];

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
    if (entry.isLFN ()) {
      buffer[2] = 'l';
    }
    listing = buffer;

    if (!entry.getName (buffer, sizeof buffer)) {
      response.set_type (Message::Text_Error);
      response = "SD: Unable to get short file name.";
      response.send ();
      bOkay = false;
    } else {
      listing += buffer;
      listing.send ();
    }
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

void SD_Path::pwd (Message & response) {
  s_path_cwd.path (response);
  response.send ();
}

bool SD_Path::cd (Message & response, const char * path) {
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

  if (!bSetRoot) {
    if (!s_path_tmp.push (path)) {
      response.set_type (Message::Text_Error);
      response  = "SD: Invalid path: '";
      response += path;
      response += "'.";
      response.send ();
      return false;
    }
  }

  bool bOkay = true;

  FatFile * dir = s_path_tmp.open (response);

  if (!dir) {
    bOkay = false;
  } else {
    if (!FatFile::setCwd (dir)) {
      response.set_type (Message::Text_Error);
      response = "SD: Unable to change working directory.";
      response.send ();
      bOkay = false;
    } else {
      s_path_cwd = s_path_tmp;
    }
    delete dir;
  }
  return bOkay;
}

bool SD_Path::ls (Message & response, const char * path) {
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

  if (!bSetRoot) {
    if (!s_path_tmp.push (path)) {
      response.set_type (Message::Text_Error);
      response  = "SD: Invalid path: '";
      response += path;
      response += "'.";
      response.send ();
      return false;
    }
  }
  return s_path_tmp.ls (response);
}

bool SD_Path::mkdir (Message & response, const char * path) {
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

  if (!s_path_tmp.push (path)) {
    response.set_type (Message::Text_Error);
    response  = "SD: Invalid path: '";
    response += path;
    response += "'.";
    response.send ();
    return false;
  }

  bool bOkay = true;

  FatFile * dir = s_path_tmp.mkdir (response);

  if (!dir) {
    response.set_type (Message::Text_Error);
    response  = "SD: mkdir: Failed to create '";
    response += path;
    response += "'.";
    response.send ();
    bOkay = false;
  } else {
    delete dir;
  }
  return bOkay;
}

bool SD_Path::rmdir (Message & response, const char * path) {
  if (!path) return false;

  if (*path == '/') { // an absolute path
    s_path_tmp.clear ();
    if (!(*++path)) { // allow "/" by itself - but root has to exist anyway
      return false;
    }
  } else {
    s_path_tmp = s_path_cwd;
  }
  if (!(*path)) {
    return false;
  }

  if (!s_path_tmp.push (path)) {
    response.set_type (Message::Text_Error);
    response  = "SD: Invalid path: '";
    response += path;
    response += "'.";
    response.send ();
    return false;
  }

  bool bOkay = true;

  FatFile * dir = s_path_tmp.open (response);

  if (!dir) {
    response.set_type (Message::Text_Error);
    response  = "SD: rmdir: Unable to open path '";
    response += path;
    response += "'.";
    response.send ();
    bOkay = false;
  } else {
    if (!dir->rmdir ()) {
      response.set_type (Message::Text_Error);
      response  = "SD: rmdir: Unable to remove path '";
      response += path;
      response += "'.";
      response.send ();
      bOkay = false;
    }
    delete dir;
  }
  return bOkay;
}

#endif /* CORE_TEENSY */
