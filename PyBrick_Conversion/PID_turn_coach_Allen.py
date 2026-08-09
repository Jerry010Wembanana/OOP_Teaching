"""Science Builders - beginner-friendly driving and turning with PID.

This file is an improved teaching version of PID_turn_coach_Mao.py.
Coach Mao's original file is intentionally kept unchanged for comparison.

Pybricks Code: 3.0.1
SPIKE Prime firmware: 4.0.1

Important ideas used in this file:

* Straight driving stops after a requested DISTANCE in millimetres.
* The gyro yaw is used only to keep the robot pointing straight.
* Each straight drive resets yaw to 0 degrees and tries to maintain 0.
* Turns are RELATIVE to the robot's heading when the turn starts.
* Positive turns are right/clockwise. Negative turns are left/counterclockwise.
* PID state is reset before every movement.
* Every movement has a timeout and always stops the motors in ``finally``.

This is teaching code. Measure and tune the geometry and PID constants on the
real Science Builders robot before using it in an FLL match.
"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Axis, Button, Color, Direction, Port, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import StopWatch, wait
from umath import pi


# ===========================================================================
# 1. ROBOT CONFIGURATION - MEASURE THESE VALUES ON THE PHYSICAL ROBOT
# ===========================================================================

# Coach Allen's temporary example motor ports.
LEFT_MOTOR_PORT = Port.A
RIGHT_MOTOR_PORT = Port.E

# With these directions, positive DriveBase speed should move both wheels
# forward on this robot: left motor CCW and right motor CW.
LEFT_MOTOR_DIRECTION = Direction.COUNTERCLOCKWISE
RIGHT_MOTOR_DIRECTION = Direction.CLOCKWISE

# Temporary reference measurements from the project's Pybricks examples.
#
# WHEEL_DIAMETER_MM affects distance calculations. If this number is wrong,
# every requested straight distance will be too long or too short.
#
# AXLE_TRACK_MM is the distance between the two wheel contact lines. It affects
# how DriveBase converts a turn rate into left/right wheel speeds. If this
# number is wrong, turns can be too large or too small.
WHEEL_DIAMETER_MM = 56
AXLE_TRACK_MM = 112


# ===========================================================================
# 2. BEGINNER-FRIENDLY STARTING VALUES - TUNE THESE ON THE ROBOT
# ===========================================================================

# Straight-drive PID values. Ki starts at 0 because integral is usually the
# last term an FLL team should add after Kp and Kd work well.
DEFAULT_STRAIGHT_KP = 2.0
DEFAULT_STRAIGHT_KI = 0.0
DEFAULT_STRAIGHT_KD = 0.1

# Relative-turn PID values. With Ki and Kd at 0, this starts as Coach Mao's
# simple proportional controller. The speed automatically becomes smaller as
# the robot gets closer to its target. Ki or Kd may be tuned later if needed.
DEFAULT_TURN_KP = 4.0
DEFAULT_TURN_KI = 0.0
DEFAULT_TURN_KD = 0.0

# Safety and reliability limits.
DEFAULT_MAX_DRIVE_SPEED_MM_S = 700
DEFAULT_MIN_DRIVE_SPEED_MM_S = 50
DEFAULT_MAX_CORRECTION_DEG_S = 150
DEFAULT_MAX_TURN_RATE_DEG_S = 150
DEFAULT_MIN_TURN_RATE_DEG_S = 25
DEFAULT_YAW_TOLERANCE_DEG = 2
DEFAULT_TIMEOUT_MS = 5000
DEFAULT_LOOP_DELAY_MS = 10
DEFAULT_SETTLED_READINGS = 3
DEFAULT_INTEGRAL_LIMIT_DEG_SECONDS = 50


# ===========================================================================
# 3. HARDWARE SETUP
# ===========================================================================

# The hub is flat. The hub's LEFT button points toward the robot's front and
# the USB port points toward the robot's right. This orientation tells the IMU
# which hub direction should count as the robot's front.
hub = PrimeHub(top_side=Axis.Z, front_side=-Axis.Y)

left_motor = Motor(LEFT_MOTOR_PORT, LEFT_MOTOR_DIRECTION)
right_motor = Motor(RIGHT_MOTOR_PORT, RIGHT_MOTOR_DIRECTION)

drive_base = DriveBase(
    left_motor,
    right_motor,
    wheel_diameter=WHEEL_DIAMETER_MM,
    axle_track=AXLE_TRACK_MM,
)

# We are writing our own educational gyro PID controller below, so the
# DriveBase's built-in gyro correction is disabled. Enabling both controllers
# at the same time would make them compete with each other.
drive_base.use_gyro(False)

# LEFT + RIGHT remains the Pybricks emergency-stop combination. CENTER is used
# by our menu to start a program and to request a controlled stop while moving.
hub.system.set_stop_button((Button.LEFT, Button.RIGHT))


# ===========================================================================
# 4. SMALL REUSABLE HELPERS
# ===========================================================================

def clamp(value, minimum, maximum):
    """Return value, limited so it stays between minimum and maximum."""
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def sign(value):
    """Return 1 for positive values, -1 for negative values, or 0."""
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def normalize_relative_angle(angle_deg):
    """Normalize an angle to the shortest equivalent angle from -180 to 180.

    Examples:
        270 degrees becomes -90 degrees (a shorter left turn).
        -270 degrees becomes 90 degrees (a shorter right turn).
        Positive 180 stays positive so its direction is not surprising.

    This helper is for relative targets and yaw errors. It intentionally means
    that this teaching function does not perform deliberate multi-turn spins.
    """
    normalized = (angle_deg + 180) % 360 - 180

    # Both +180 and -180 are equally short. Preserve a positive request as
    # +180 instead of unexpectedly changing it to -180.
    if normalized == -180 and angle_deg > 0:
        return 180

    return normalized


def normalized_yaw_error(target_yaw, current_yaw):
    """Return the shortest signed error from current_yaw to target_yaw."""
    return normalize_relative_angle(target_yaw - current_yaw)


def wheel_rotation_to_distance_mm(motor_rotation_deg):
    """Convert wheel/motor rotation in degrees to travel distance in mm.

    Formula:
        wheel circumference = pi * wheel diameter
        distance = (motor degrees / 360) * wheel circumference

    This assumes the drive motor turns the wheel directly (1:1 gearing). If the
    robot uses gears between the motor and wheel, add the gear ratio here.
    """
    wheel_circumference_mm = pi * WHEEL_DIAMETER_MM
    return motor_rotation_deg / 360 * wheel_circumference_mm


def average_travel_distance_mm(start_left_deg, start_right_deg):
    """Estimate absolute robot travel using the average of both drive wheels.

    One slipping or blocked wheel should not be trusted by itself, so both
    encoder changes are averaged. This measures wheel travel, not robot yaw.
    """
    left_change_deg = left_motor.angle() - start_left_deg
    right_change_deg = right_motor.angle() - start_right_deg

    # Average the signed wheel changes first, then take the absolute value.
    # This makes extra wheel motion used only for steering cancel out instead
    # of being incorrectly counted as extra forward travel.
    average_change_deg = abs((left_change_deg + right_change_deg) / 2)
    return wheel_rotation_to_distance_mm(average_change_deg)


def validate_stop_action(then):
    """Check that the requested ending action is HOLD, BRAKE, or COAST."""
    if then != Stop.HOLD and then != Stop.BRAKE and then != Stop.COAST:
        raise ValueError("then must be Stop.HOLD, Stop.BRAKE, or Stop.COAST")


def stop_drive(then=Stop.HOLD):
    """Stop both drive motors using the requested behavior.

    Stop.HOLD actively keeps the wheels in position and is the default.
    Stop.BRAKE passively resists motion. Stop.COAST lets the wheels roll.
    """
    validate_stop_action(then)

    # First end the continuing DriveBase.drive() command.
    drive_base.stop()

    if then == Stop.HOLD:
        left_motor.hold()
        right_motor.hold()
    elif then == Stop.BRAKE:
        left_motor.brake()
        right_motor.brake()
    else:
        left_motor.stop()
        right_motor.stop()


def wait_for_imu_ready(timeout_ms=3000):
    """Wait briefly for the IMU and return True when it is ready."""
    timer = StopWatch()

    while not hub.imu.ready():
        if timer.time() >= timeout_ms:
            return False
        wait(DEFAULT_LOOP_DELAY_MS)

    return True


def reset_yaw_to_zero():
    """Stop, wait for the IMU, and define the robot's current yaw as 0 deg."""
    drive_base.stop()

    if not wait_for_imu_ready():
        raise RuntimeError("IMU was not ready before its timeout")

    hub.imu.reset_heading(0)
    wait(50)


def movement_cancel_requested():
    """Return True if CENTER is pressed during a running example."""
    return Button.CENTER in hub.buttons.pressed()


def wait_for_button_release():
    """Wait until the user has released every hub button."""
    while hub.buttons.pressed():
        wait(DEFAULT_LOOP_DELAY_MS)


def validate_common_movement_values(timeout_ms, loop_delay_ms, then):
    """Validate values shared by straight driving and turning."""
    validate_stop_action(then)

    if WHEEL_DIAMETER_MM <= 0:
        raise ValueError("WHEEL_DIAMETER_MM must be greater than 0")
    if AXLE_TRACK_MM <= 0:
        raise ValueError("AXLE_TRACK_MM must be greater than 0")
    if timeout_ms <= 0:
        raise ValueError("timeout_ms must be greater than 0")
    if loop_delay_ms <= 0:
        raise ValueError("loop_delay_ms must be greater than 0")


# ===========================================================================
# 5. STRAIGHT DRIVING PID
# ===========================================================================

def _drive_straight_pid(
    start_speed_mm_s,
    end_speed_mm_s,
    distance_mm,
    kp,
    ki,
    kd,
    max_correction_deg_s,
    integral_limit_deg_seconds,
    min_drive_speed_mm_s,
    max_drive_speed_mm_s,
    timeout_ms,
    loop_delay_ms,
    then,
):
    """Shared implementation for constant-speed and ramped straight driving."""
    validate_common_movement_values(timeout_ms, loop_delay_ms, then)

    if start_speed_mm_s < 0 or end_speed_mm_s < 0:
        raise ValueError("start and end speeds must be nonnegative magnitudes")
    if start_speed_mm_s == 0 and end_speed_mm_s == 0 and distance_mm != 0:
        raise ValueError("at least one drive speed must be greater than 0")
    if min_drive_speed_mm_s < 0:
        raise ValueError("min_drive_speed_mm_s cannot be negative")
    if max_drive_speed_mm_s <= 0:
        raise ValueError("max_drive_speed_mm_s must be greater than 0")
    if min_drive_speed_mm_s > max_drive_speed_mm_s:
        raise ValueError("minimum drive speed cannot exceed maximum drive speed")
    if max_correction_deg_s <= 0:
        raise ValueError("max_correction_deg_s must be greater than 0")
    if integral_limit_deg_seconds < 0:
        raise ValueError("integral_limit_deg_seconds cannot be negative")

    target_distance_mm = abs(distance_mm)
    drive_direction = sign(distance_mm)

    # A zero-distance command should not reset the gyro or start the motors.
    if target_distance_mm == 0:
        stop_drive(then)
        return {
            "status": "completed",
            "completed": True,
            "timed_out": False,
            "cancelled": False,
            "target_distance_mm": 0,
            "traveled_distance_mm": 0,
            "final_yaw_deg": hub.imu.heading(),
            "final_yaw_error_deg": 0,
            "elapsed_ms": 0,
            "final_speed_mm_s": 0,
            "final_correction_deg_s": 0,
        }

    timer = StopWatch()
    status = "running"
    traveled_distance_mm = 0
    current_yaw = 0
    yaw_error = 0
    current_speed_mm_s = 0
    correction_deg_s = 0
    p_term = 0
    i_term = 0
    d_term = 0

    try:
        # The robot's current direction becomes 0. PID will maintain that 0.
        reset_yaw_to_zero()

        start_left_deg = left_motor.angle()
        start_right_deg = right_motor.angle()

        integral = 0
        current_yaw = hub.imu.heading()
        previous_error = normalized_yaw_error(0, current_yaw)
        previous_time_ms = 0
        timer.reset()

        while True:
            elapsed_ms = timer.time()
            traveled_distance_mm = average_travel_distance_mm(
                start_left_deg,
                start_right_deg,
            )

            # DISTANCE decides when straight driving is finished.
            if traveled_distance_mm >= target_distance_mm:
                status = "completed"
                break

            if elapsed_ms >= timeout_ms:
                status = "timed_out"
                break

            if movement_cancel_requested():
                status = "cancelled"
                break

            # A linear ramp: start + (end - start) * fraction completed.
            progress = clamp(traveled_distance_mm / target_distance_mm, 0, 1)
            requested_speed_mm_s = (
                start_speed_mm_s
                + (end_speed_mm_s - start_speed_mm_s) * progress
            )

            # Maximum speed protects the robot. Minimum speed helps overcome
            # motor friction, especially near a ramp endpoint of 0.
            current_speed_mm_s = clamp(
                requested_speed_mm_s,
                0,
                max_drive_speed_mm_s,
            )
            if current_speed_mm_s < min_drive_speed_mm_s:
                current_speed_mm_s = min_drive_speed_mm_s

            current_yaw = hub.imu.heading()
            yaw_error = normalized_yaw_error(0, current_yaw)

            # dt is seconds. PID math must use elapsed time so changing the
            # loop delay does not completely change Ki and Kd behavior.
            dt = (elapsed_ms - previous_time_ms) / 1000
            if dt <= 0:
                dt = loop_delay_ms / 1000

            # Integral remembers old error. Clamping it prevents windup, which
            # is a huge stored correction that can cause overshoot later.
            if ki != 0:
                integral = clamp(
                    integral + yaw_error * dt,
                    -integral_limit_deg_seconds,
                    integral_limit_deg_seconds,
                )
            else:
                integral = 0

            derivative = (yaw_error - previous_error) / dt

            p_term = kp * yaw_error
            i_term = ki * integral
            d_term = kd * derivative
            raw_correction_deg_s = p_term + i_term + d_term

            # Limiting the final PID output keeps one noisy sensor reading from
            # commanding an excessively sharp correction.
            correction_deg_s = clamp(
                raw_correction_deg_s,
                -max_correction_deg_s,
                max_correction_deg_s,
            )

            # Speed is mm/s. Turn rate is deg/s. Positive turn rate is right
            # (clockwise), matching positive SPIKE Prime yaw for this setup.
            drive_base.drive(
                drive_direction * current_speed_mm_s,
                correction_deg_s,
            )

            previous_error = yaw_error
            previous_time_ms = elapsed_ms
            wait(loop_delay_ms)

    finally:
        # This also runs if an exception happens, preventing runaway motors.
        stop_drive(then)

    elapsed_ms = timer.time()
    current_yaw = hub.imu.heading()
    yaw_error = normalized_yaw_error(0, current_yaw)

    return {
        "status": status,
        "completed": status == "completed",
        "timed_out": status == "timed_out",
        "cancelled": status == "cancelled",
        "target_distance_mm": target_distance_mm,
        "traveled_distance_mm": traveled_distance_mm,
        "final_yaw_deg": current_yaw,
        "final_yaw_error_deg": yaw_error,
        "elapsed_ms": elapsed_ms,
        "final_speed_mm_s": current_speed_mm_s,
        "final_correction_deg_s": correction_deg_s,
        "final_p_term": p_term,
        "final_i_term": i_term,
        "final_d_term": d_term,
    }


def drive_straight_pid_distance(
    speed_mm_s,
    distance_mm,
    kp=DEFAULT_STRAIGHT_KP,
    ki=DEFAULT_STRAIGHT_KI,
    kd=DEFAULT_STRAIGHT_KD,
    max_correction_deg_s=DEFAULT_MAX_CORRECTION_DEG_S,
    integral_limit_deg_seconds=DEFAULT_INTEGRAL_LIMIT_DEG_SECONDS,
    min_drive_speed_mm_s=DEFAULT_MIN_DRIVE_SPEED_MM_S,
    max_drive_speed_mm_s=DEFAULT_MAX_DRIVE_SPEED_MM_S,
    timeout_ms=DEFAULT_TIMEOUT_MS,
    loop_delay_ms=DEFAULT_LOOP_DELAY_MS,
    then=Stop.HOLD,
):
    """Drive a physical distance while PID maintains zero yaw.

    Parameters:
        speed_mm_s: Nonnegative speed magnitude in millimetres per second.
        distance_mm: Signed travel distance in millimetres. Positive is forward
            and negative is backward.
        kp, ki, kd: Straight-heading PID gains.
        max_correction_deg_s: Largest left/right steering correction in deg/s.
        integral_limit_deg_seconds: Integral windup limit in degree-seconds.
        min_drive_speed_mm_s: Smallest command used to overcome friction.
        max_drive_speed_mm_s: Safety limit for the forward/backward speed.
        timeout_ms: Safety timeout in milliseconds.
        loop_delay_ms: Delay between PID updates in milliseconds.
        then: Stop.HOLD (default), Stop.BRAKE, or Stop.COAST.

    Yaw behavior:
        The IMU yaw is reset to 0 at the start. Target yaw is always 0, and PID
        corrects yaw error while distance decides when to stop.

    Stops when:
        Average left/right encoder travel reaches abs(distance_mm), CENTER is
        pressed, or the timeout expires.

    Returns:
        A readable dictionary containing status and final diagnostic values.

    Assumptions:
        Drive motors turn the wheels at a 1:1 gear ratio. Encoder distance can
        still be wrong if the wheels slip or WHEEL_DIAMETER_MM is inaccurate.
    """
    return _drive_straight_pid(
        speed_mm_s,
        speed_mm_s,
        distance_mm,
        kp,
        ki,
        kd,
        max_correction_deg_s,
        integral_limit_deg_seconds,
        min_drive_speed_mm_s,
        max_drive_speed_mm_s,
        timeout_ms,
        loop_delay_ms,
        then,
    )


def drive_straight_pid_ramp(
    start_speed_mm_s,
    end_speed_mm_s,
    distance_mm,
    kp=DEFAULT_STRAIGHT_KP,
    ki=DEFAULT_STRAIGHT_KI,
    kd=DEFAULT_STRAIGHT_KD,
    max_correction_deg_s=DEFAULT_MAX_CORRECTION_DEG_S,
    integral_limit_deg_seconds=DEFAULT_INTEGRAL_LIMIT_DEG_SECONDS,
    min_drive_speed_mm_s=DEFAULT_MIN_DRIVE_SPEED_MM_S,
    max_drive_speed_mm_s=DEFAULT_MAX_DRIVE_SPEED_MM_S,
    timeout_ms=DEFAULT_TIMEOUT_MS,
    loop_delay_ms=DEFAULT_LOOP_DELAY_MS,
    then=Stop.HOLD,
):
    """Drive a distance with a linear speed ramp and zero-yaw PID correction.

    Parameters:
        start_speed_mm_s: Starting nonnegative speed magnitude in mm/s.
        end_speed_mm_s: Ending nonnegative speed magnitude in mm/s.
        distance_mm: Signed distance in mm; positive forward, negative backward.
        kp, ki, kd: Straight-heading PID gains.
        All remaining limits, timing values, and stop behavior have the same
        units and meanings as drive_straight_pid_distance().

    The IMU yaw is reset to 0 at the start, so yaw is relative to the starting
    direction. Distance, not yaw, decides when driving is complete. Speed is:

        current = start + (end - start) * (travelled / target distance)

    This formula works for acceleration and deceleration. No Kfactor is used;
    Kp, Ki, and Kd remain independent, understandable PID gains.

    Returns a readable dictionary with status and final diagnostic values.
    """
    return _drive_straight_pid(
        start_speed_mm_s,
        end_speed_mm_s,
        distance_mm,
        kp,
        ki,
        kd,
        max_correction_deg_s,
        integral_limit_deg_seconds,
        min_drive_speed_mm_s,
        max_drive_speed_mm_s,
        timeout_ms,
        loop_delay_ms,
        then,
    )


def drive_straight_pid_turns(
    base_speed_deg_s,
    turns,
    target_yaw=0,
    then=Stop.HOLD,
    timeout_ms=DEFAULT_TIMEOUT_MS,
):
    """Legacy teaching bridge from Coach Mao's motor-turn interface.

    Prefer drive_straight_pid_distance() in new programs because millimetres are
    easier to measure on an FLL field.

    Parameters:
        base_speed_deg_s: Nonnegative wheel motor speed in degrees per second.
        turns: Signed number of wheel rotations; positive forward and negative
            backward.
        target_yaw: Kept only so old calls are recognizable. It must be 0,
            because this Allen version resets yaw and maintains 0 every run.
        then: Stop.HOLD (default), Stop.BRAKE, or Stop.COAST.
        timeout_ms: Safety timeout in milliseconds.

    Conversion formulas:
        distance_mm = turns * pi * WHEEL_DIAMETER_MM
        speed_mm_s = motor_deg_s / 360 * pi * WHEEL_DIAMETER_MM

    It returns the same diagnostic dictionary as the distance function.
    """
    if base_speed_deg_s < 0:
        raise ValueError("base_speed_deg_s must be a nonnegative magnitude")
    if target_yaw != 0:
        raise ValueError("Allen straight driving resets yaw; target_yaw must be 0")

    distance_mm = turns * pi * WHEEL_DIAMETER_MM
    speed_mm_s = wheel_rotation_to_distance_mm(base_speed_deg_s)

    return drive_straight_pid_distance(
        speed_mm_s=speed_mm_s,
        distance_mm=distance_mm,
        timeout_ms=timeout_ms,
        then=then,
    )


# ===========================================================================
# 6. RELATIVE PID TURN
# ===========================================================================

def turn_relative_pid(
    relative_angle_deg,
    adjustment_deg=0,
    kp=DEFAULT_TURN_KP,
    ki=DEFAULT_TURN_KI,
    kd=DEFAULT_TURN_KD,
    max_turn_rate_deg_s=DEFAULT_MAX_TURN_RATE_DEG_S,
    min_turn_rate_deg_s=DEFAULT_MIN_TURN_RATE_DEG_S,
    yaw_tolerance_deg=DEFAULT_YAW_TOLERANCE_DEG,
    integral_limit_deg_seconds=DEFAULT_INTEGRAL_LIMIT_DEG_SECONDS,
    settled_readings=DEFAULT_SETTLED_READINGS,
    timeout_ms=DEFAULT_TIMEOUT_MS,
    loop_delay_ms=DEFAULT_LOOP_DELAY_MS,
    then=Stop.HOLD,
):
    """Make a shortest-path RELATIVE gyro turn using PID.

    Parameters:
        relative_angle_deg: Requested change from the starting heading in deg.
            Positive is right/clockwise; negative is left/counterclockwise.
            The request is normalized to the shortest path from -180 to 180.
        adjustment_deg: Nonnegative early-stop amount in degrees. Default 0.
            Use it only as a last-resort correction for unavoidable inertia.
        kp, ki, kd: Turning PID gains. The defaults are proportional-only.
        max_turn_rate_deg_s: Safety limit for turn rate in deg/s.
        min_turn_rate_deg_s: Minimum command used to overcome motor friction.
        yaw_tolerance_deg: Allowed error from the effective target in degrees.
        integral_limit_deg_seconds: Integral windup limit in degree-seconds.
        settled_readings: Consecutive in-tolerance readings required to finish.
        timeout_ms: Safety timeout in milliseconds.
        loop_delay_ms: Delay between PID updates in milliseconds.
        then: Stop.HOLD (default), Stop.BRAKE, or Stop.COAST.

    Target behavior:
        The input is relative, not an absolute hub heading. For example, 90
        means turn right 90 degrees from wherever the robot starts. The yaw
        error is normalized so the robot takes the shortest valid path.

        If adjustment_deg is 3 for a 90-degree turn, the motor command targets
        87 degrees. The hoped-for final 3 degrees come from inertia. Leave this
        at 0 unless physical tests show that PID tuning cannot remove the error.

    Stops when:
        The effective target is within yaw_tolerance_deg for settled_readings,
        CENTER is pressed, or timeout_ms expires.

    Returns:
        A readable dictionary with status, headings, errors, and final PID terms.
    """
    validate_common_movement_values(timeout_ms, loop_delay_ms, then)

    if adjustment_deg < 0:
        raise ValueError("adjustment_deg must be nonnegative")
    if max_turn_rate_deg_s <= 0:
        raise ValueError("max_turn_rate_deg_s must be greater than 0")
    if min_turn_rate_deg_s < 0:
        raise ValueError("min_turn_rate_deg_s cannot be negative")
    if min_turn_rate_deg_s > max_turn_rate_deg_s:
        raise ValueError("minimum turn rate cannot exceed maximum turn rate")
    if yaw_tolerance_deg <= 0:
        raise ValueError("yaw_tolerance_deg must be greater than 0")
    if integral_limit_deg_seconds < 0:
        raise ValueError("integral_limit_deg_seconds cannot be negative")
    if settled_readings <= 0:
        raise ValueError("settled_readings must be greater than 0")

    requested_turn_deg = normalize_relative_angle(relative_angle_deg)
    turn_direction = sign(requested_turn_deg)

    if requested_turn_deg != 0 and adjustment_deg >= abs(requested_turn_deg):
        raise ValueError("adjustment_deg must be smaller than the requested turn")

    effective_turn_deg = turn_direction * (
        abs(requested_turn_deg) - adjustment_deg
    )

    timer = StopWatch()
    status = "running"
    current_yaw = hub.imu.heading()
    start_yaw = current_yaw
    desired_target_yaw = start_yaw + requested_turn_deg
    control_target_yaw = start_yaw + effective_turn_deg
    control_error = normalized_yaw_error(control_target_yaw, current_yaw)
    desired_error = normalized_yaw_error(desired_target_yaw, current_yaw)
    turn_rate_deg_s = 0
    p_term = 0
    i_term = 0
    d_term = 0

    # A 0-degree turn is already complete and should not start the motors.
    if requested_turn_deg == 0:
        stop_drive(then)
        return {
            "status": "completed",
            "completed": True,
            "timed_out": False,
            "cancelled": False,
            "requested_turn_deg": 0,
            "effective_turn_deg": 0,
            "adjustment_deg": adjustment_deg,
            "start_yaw_deg": start_yaw,
            "control_target_yaw_deg": start_yaw,
            "desired_target_yaw_deg": start_yaw,
            "final_yaw_deg": current_yaw,
            "final_control_error_deg": 0,
            "final_desired_error_deg": 0,
            "elapsed_ms": 0,
            "final_turn_rate_deg_s": 0,
        }

    try:
        integral = 0
        previous_error = control_error
        previous_time_ms = 0
        in_tolerance_count = 0
        timer.reset()

        while True:
            elapsed_ms = timer.time()
            current_yaw = hub.imu.heading()
            control_error = normalized_yaw_error(
                control_target_yaw,
                current_yaw,
            )

            # Check safety exits before calculating or sending another motor
            # command. The finally block below performs the requested stop.
            if elapsed_ms >= timeout_ms:
                status = "timed_out"
                break

            if movement_cancel_requested():
                status = "cancelled"
                break

            # Several good readings prevent one noisy IMU sample from ending
            # the turn too soon.
            if abs(control_error) <= yaw_tolerance_deg:
                in_tolerance_count += 1
                drive_base.drive(0, 0)

                if in_tolerance_count >= settled_readings:
                    status = "completed"
                    break
            else:
                in_tolerance_count = 0

                dt = (elapsed_ms - previous_time_ms) / 1000
                if dt <= 0:
                    dt = loop_delay_ms / 1000

                if ki != 0:
                    integral = clamp(
                        integral + control_error * dt,
                        -integral_limit_deg_seconds,
                        integral_limit_deg_seconds,
                    )
                else:
                    integral = 0

                derivative = (control_error - previous_error) / dt

                p_term = kp * control_error
                i_term = ki * integral
                d_term = kd * derivative
                raw_turn_rate_deg_s = p_term + i_term + d_term

                turn_rate_deg_s = clamp(
                    raw_turn_rate_deg_s,
                    -max_turn_rate_deg_s,
                    max_turn_rate_deg_s,
                )

                # Kp makes the robot slow down near the target. The minimum is
                # used only outside the tolerance, to overcome motor friction.
                if abs(turn_rate_deg_s) < min_turn_rate_deg_s:
                    turn_rate_deg_s = sign(control_error) * min_turn_rate_deg_s

                drive_base.drive(0, turn_rate_deg_s)

                previous_error = control_error
                previous_time_ms = elapsed_ms

            wait(loop_delay_ms)

    finally:
        stop_drive(then)

    elapsed_ms = timer.time()
    current_yaw = hub.imu.heading()
    control_error = normalized_yaw_error(control_target_yaw, current_yaw)
    desired_error = normalized_yaw_error(desired_target_yaw, current_yaw)

    return {
        "status": status,
        "completed": status == "completed",
        "timed_out": status == "timed_out",
        "cancelled": status == "cancelled",
        "requested_turn_deg": requested_turn_deg,
        "effective_turn_deg": effective_turn_deg,
        "adjustment_deg": adjustment_deg,
        "start_yaw_deg": start_yaw,
        "control_target_yaw_deg": control_target_yaw,
        "desired_target_yaw_deg": desired_target_yaw,
        "final_yaw_deg": current_yaw,
        "final_control_error_deg": control_error,
        "final_desired_error_deg": desired_error,
        "elapsed_ms": elapsed_ms,
        "final_turn_rate_deg_s": turn_rate_deg_s,
        "final_p_term": p_term,
        "final_i_term": i_term,
        "final_d_term": d_term,
    }


# ===========================================================================
# 7. DELIBERATE BUTTON-START EXAMPLES
# ===========================================================================

def show_result(result):
    """Print diagnostics and show a short success/failure signal on the hub."""
    print(result)

    if result["completed"]:
        hub.light.on(Color.GREEN)
        hub.display.char("Y")
    elif result["timed_out"]:
        hub.light.on(Color.RED)
        hub.display.char("T")
    else:
        hub.light.on(Color.YELLOW)
        hub.display.char("X")

    wait(800)
    hub.light.off()


def example_drive_constant_speed():
    """Example D: drive forward 200 mm at 200 mm/s."""
    return drive_straight_pid_distance(
        speed_mm_s=200,
        distance_mm=200,
    )


def example_drive_with_ramp():
    """Example R: accelerate from 100 to 300 mm/s over 300 mm."""
    return drive_straight_pid_ramp(
        start_speed_mm_s=100,
        end_speed_mm_s=300,
        distance_mm=300,
    )


def example_turn_right_90():
    """Example T: make a relative 90-degree right turn."""
    return turn_relative_pid(
        relative_angle_deg=90,
        adjustment_deg=0,
    )


EXAMPLE_PROGRAMS = [
    ("D", example_drive_constant_speed),
    ("R", example_drive_with_ramp),
    ("T", example_turn_right_90),
]


def run_example_menu():
    """Select with LEFT/RIGHT and deliberately start with CENTER.

    D = constant-speed distance PID
    R = ramped-speed distance PID
    T = relative 90-degree right turn

    During a movement, CENTER asks the loop to stop safely. Press LEFT + RIGHT
    together for the Pybricks emergency stop.
    """
    selected = 0
    hub.light.on(Color.YELLOW)

    while True:
        name, selected_program = EXAMPLE_PROGRAMS[selected]
        hub.display.char(name)
        pressed = hub.buttons.pressed()

        if Button.RIGHT in pressed:
            selected += 1
            if selected >= len(EXAMPLE_PROGRAMS):
                selected = 0
            wait_for_button_release()

        elif Button.LEFT in pressed:
            selected -= 1
            if selected < 0:
                selected = len(EXAMPLE_PROGRAMS) - 1
            wait_for_button_release()

        elif Button.CENTER in pressed:
            wait_for_button_release()
            hub.light.on(Color.BLUE)
            hub.display.char("G")
            wait(300)

            try:
                result = selected_program()
                show_result(result)
            except Exception as error:
                # Each movement already has finally-stop protection. This menu
                # handler also reports the error and remains useful for testing.
                stop_drive(Stop.HOLD)
                print("Program error:", error)
                hub.light.on(Color.RED)
                hub.display.char("E")
                wait(1000)
                hub.light.off()

        wait(50)


# Importing this file does not move the robot. Running the file opens the menu,
# and no example moves until the user deliberately presses CENTER.
if __name__ == "__main__":
    run_example_menu()
