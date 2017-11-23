class APin;
class DPin;

class PinManager {
private:
  APin * AP[6];
  DPin * DP[14];

  bool (*user_command) (String & first, int argc, char ** argv);

  PinManager ();

public:
  ~PinManager ();

  static PinManager * manager ();

  void dpin_write (int pin_no, bool value);

  void input_callbacks (bool (*user_command_callback) (String & first, int argc, char ** argv), void (*user_interrupt_callback) ());

  bool command (int argc, char ** argv); // commands handled by PinManager

private:
  int parse_pin_no (const char * str, unsigned int flags, bool bDigital) const; // returns pin no if valid, otherwise -1

  void list (bool bAnalog, bool bDigital) const;
};
