from pybricks.tools import wait, StopWatch

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


def drive_straight_pid(base_speed, duration_ms, target_yaw=0):
    Kp = 3.0
    Ki = 0.0
    Kd = 0.5

    integral = 0
    last_error = 0

    timer = StopWatch()
    last_time = timer.time()

    while timer.time() < duration_ms:
        current_time = timer.time()
        dt = (current_time - last_time) / 1000

        if dt <= 0:
            dt = 0.01

        current_yaw = hub.imu.heading()
        error = target_yaw - current_yaw

        integral += error * dt
        derivative = (error - last_error) / dt

        correction = Kp * error + Ki * integral + Kd * derivative

        left_speed = limit_speed(base_speed - correction)
        right_speed = limit_speed(base_speed + correction)

        set_drive_speed(left_speed, right_speed)

        last_error = error
        last_time = current_time

        wait(10)

    left_motor.stop()
    right_motor.stop()

drive_straight_pid(300,5000)