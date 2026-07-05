from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Stop
from pybricks.tools import wait

hub = PrimeHub()
left_motor = Motor(Port.A)
right_motor = Motor(Port.E)


def limit_speed(speed):
    if speed > 1000:
        return 1000
    elif speed < -1000:
        return -1000
    else:
        return speed


def set_drive_speed(left_speed, right_speed):
    left_motor.run(left_speed)
    right_motor.run(right_speed)


def stop_drive(then=Stop.HOLD):
    if then == Stop.HOLD:
        left_motor.hold()
        right_motor.hold()
    elif then == Stop.BRAKE:
        left_motor.brake()
        right_motor.brake()
    else:
        left_motor.stop()
        right_motor.stop()


def drive_straight_pid_turns(base_speed, turns, target_yaw=0, then=Stop.HOLD):
    Kp = 3.0
    Ki = 0.0
    Kd = 0.5

    integral = 0
    last_error = 0

    # Reset motor angle readings.
    left_motor.reset_angle(0)
    right_motor.reset_angle(0)

    target_angle = abs(turns) * 360

    # If turns is negative, drive backward.
    if turns < 0:
        drive_speed = -abs(base_speed)
    else:
        drive_speed = abs(base_speed)

    last_time = 0

    while True:
        # Average motor rotation in degrees.
        left_angle = abs(left_motor.angle())
        right_angle = abs(right_motor.angle())
        average_angle = (left_angle + right_angle) / 2

        # Stop when the average motor angle reaches the target.
        if average_angle >= target_angle:
            break

        current_time = hub.system.time()
        dt = (current_time - last_time) / 1000

        if dt <= 0:
            dt = 0.01

        current_yaw = hub.imu.heading()
        error = target_yaw - current_yaw

        integral += error * dt
        derivative = (error - last_error) / dt

        correction = Kp * error + Ki * integral + Kd * derivative

        left_speed = limit_speed(-drive_speed + correction)
        right_speed = limit_speed(drive_speed + correction)

        set_drive_speed(left_speed, right_speed)

        last_error = error
        last_time = current_time

        wait(10)

    stop_drive(then)


def turn_to_yaw(target_yaw, max_speed=300):
    Kp = 4.0
    tolerance = 2

    while True:
        current_yaw = hub.imu.heading()
        error = target_yaw - current_yaw

        if abs(error) <= tolerance:
            break

        turn_speed = Kp * error
        turn_speed = limit_speed(turn_speed)

        if turn_speed > max_speed:
            turn_speed = max_speed
        elif turn_speed < -max_speed:
            turn_speed = -max_speed

        # One motor forward, one motor backward.
        left_motor.run(turn_speed)
        right_motor.run(turn_speed)

        wait(10)

    stop_drive()


# Drive forward for 3 motor turns at 300 deg/s.
drive_straight_pid_turns(base_speed=300, turns=3, target_yaw=0)

wait(1000)

turn_to_yaw(90)