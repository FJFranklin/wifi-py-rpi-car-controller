/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "sd.hh"

#ifdef CORE_TEENSY
#include "sd_path.hh"
#endif /* CORE_TEENSY */

static SD_Manager * s_manager = 0;

SD_Manager * SD_Manager::manager () {
#ifdef CORE_TEENSY
  if (!s_manager) {
    s_manager = new SD_Manager;
  }
#endif /* CORE_TEENSY */
  return s_manager;
}

CommandStatus SD_Manager::command (uint8_t address_src, const String & first, int argc, char ** argv) {
  CommandStatus cs = cs_UnknownCommand;
#ifdef CORE_TEENSY
  if (first == "sd") {
    SD_Card_Info (address_src);
    cs = cs_Okay;
  } else if (first == "sd-erase") {
    SD_Card_Erase (address_src);
    cs = cs_Okay;
  } else if (first == "sd-format") {
    SD_Card_Format (address_src);
    cs = cs_Okay;
  } else if (first == "pwd") {
    SD_Path::pwd (address_src);
    cs = cs_Okay;
  } else if (first == "ls") {
    if (argc == 1) {
      SD_Path::pwd().ls (address_src);
    } else {
      for (int arg = 1; arg < argc; arg++) {
	SD_Path::ls (address_src, argv[arg]);
      }
    }
    cs = cs_Okay;
  } else if (first == "mkdir") {
    if (argc == 1) {
      Message response(Message::Text_Error);
      response.text = "usage: mkdir <path> [<path>]*";
      response.send (address_src);
    } else {
      for (int arg = 1; arg < argc; arg++) {
	SD_Path::mkdir (address_src, argv[arg]);
      }
    }
    cs = cs_Okay;
  } else if (first == "rmdir") {
    if (argc == 1) {
      Message response(Message::Text_Error);
      response.text = "usage: rmdir <path> [<path>]*";
      response.send (address_src);
    } else {
      for (int arg = 1; arg < argc; arg++) {
	SD_Path::rmdir (address_src, argv[arg]);
      }
    }
    cs = cs_Okay;
  } else if (first == "cd") {
    if (argc == 1) {
      SD_Path::cd (address_src, "/");
    } else if (argc == 2) {
      SD_Path::cd (address_src, argv[1]);
    } else {
      Message response(Message::Text_Error);
      response.text = "usage: cd [<path>]";
      response.send (address_src);
    }
    cs = cs_Okay;
  }
#endif /* CORE_TEENSY */
  return cs;
}
