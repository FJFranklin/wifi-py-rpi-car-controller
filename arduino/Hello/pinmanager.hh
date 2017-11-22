class APin;
class DPin;

class PinManager {
private:
  APin * AP[6];
  DPin * DP[14];
public:
  PinManager ();

  ~PinManager ();

  bool command (const String & first, int argc, char ** argv);

private:
  int parse_pin_no (const char * str, unsigned int flags, bool bDigital) const; // returns pin no if valid, otherwise -1

  void list (bool bAnalog, bool bDigital) const;
};
