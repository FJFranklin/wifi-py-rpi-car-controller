If your MQTT server ("controller") and remote device ("car")
are operating without keyboard & display, then it's convenient
to have a way to shut down the Raspberry Pis easily.

These scripts create a user-space demon for doing that,
but to be perfectly honest it's a bad and hackish solution.

If car.py/controller.py crash on execution, then you will
need to mount the SD card on another machine to edit out the
shutdown command... I speak from experience.
