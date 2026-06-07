# Do NOT use RUN button within IDE!
# For uploading code to Hub, go to https://code.pybricks.com/

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Stop, Direction
from pybricks.tools import wait

hub = PrimeHub()
left_motor = Motor(Port.A)
right_motor = Motor(Port.E)

attachment_c = Motor(Port.C)
attachment_f = Motor(Port.F)

left_color = ColorSensor(Port.B)
right_color = ColorSensor(Port.D)

def stop_drive():
    left_motor.stop()
    right_motor.stop()

def set_drive_power(left_power, right_power):
    left_motor.run(left_power)
    right_motor.run(right_power)

def main():
    hub.imu.reset_heading(0)

    set_drive_power(30,30)
    wait(1000)

    stop_drive()
    wait(500)

    # set_drive_power(-30,30) # Left Turn hold position
    # set_drive_power(0,30)

    attachment_c.run_angle(300,90,then=Stop.HOLD,wait=True)
    attachment_f.run_angle(300,90,then=Stop.HOLD,wait=True)

