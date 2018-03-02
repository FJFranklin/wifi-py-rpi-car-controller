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

CommandStatus SD_Manager::command (Message & response, const ArgList & Args) {
  CommandStatus cs = cs_UnknownCommand;
#ifdef CORE_TEENSY
  Arg first = Args[0];
  uint8_t argc = Args.count ();

  if (first == "sd") {
    SD_Card_Info (response);
    cs = cs_Okay;
  } else if (first == "sd-erase") {
    SD_Card_Erase (response);
    cs = cs_Okay;
  } else if (first == "sd-format") {
    SD_Card_Format (response);
    cs = cs_Okay;
  } else if (first == "pwd") {
    SD_Path::pwd (response);
    cs = cs_Okay;
  } else if (first == "ls") {
    if (argc == 1) {
      SD_Path::pwd().ls (response);
    } else {
      for (int arg = 1; arg < argc; arg++) {
	SD_Path::ls (response, Args[arg].c_str ());
      }
    }
    cs = cs_Okay;
  } else if (first == "mkdir") {
    if (argc == 1) {
      response.set_type (Message::Text_Error);
      response = "usage: mkdir <path> [<path>]*";
      response.send ();
    } else {
      for (int arg = 1; arg < argc; arg++) {
	SD_Path::mkdir (response, Args[arg].c_str ());
      }
    }
    cs = cs_Okay;
  } else if (first == "rmdir") {
    if (argc == 1) {
      response.set_type (Message::Text_Error);
      response = "usage: rmdir <path> [<path>]*";
      response.send ();
    } else {
      for (int arg = 1; arg < argc; arg++) {
	SD_Path::rmdir (response, Args[arg].c_str ());
      }
    }
    cs = cs_Okay;
  } else if (first == "cd") {
    if (argc == 1) {
      SD_Path::cd (response, "/");
    } else if (argc == 2) {
      SD_Path::cd (response, Args[1].c_str ());
    } else {
      response.set_type (Message::Text_Error);
      response = "usage: cd [<path>]";
      response.send ();
    }
    cs = cs_Okay;
  }
#endif /* CORE_TEENSY */
  return cs;
}
