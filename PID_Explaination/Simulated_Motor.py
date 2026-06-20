import numpy as np

def simulate_motor(Kp, Ki, Kd, target_position=100, total_time=10, dt=0.01):
    time_list = []
    position_list = []
    speed_list = []
    power_list = []
    error_list = []

    position = 0
    speed = 0

    integral = 0
    previous_error = target_position - position

    max_power = 100

    for t in np.arange(0, total_time, dt):
        error = target_position - position

        integral = integral + error * dt

        derivative = (error - previous_error) / dt

        power = Kp * error + Ki * integral + Kd * derivative

        if power > max_power:
            power = max_power
        elif power < -max_power:
            power = -max_power

        # Simulated motor physics
        acceleration = power - 0.8 * speed
        speed = speed + acceleration * dt
        position = position + speed * dt

        time_list.append(t)
        position_list.append(position)
        speed_list.append(speed)
        power_list.append(power)
        error_list.append(error)

        previous_error = error

    return time_list, position_list, speed_list, power_list, error_list