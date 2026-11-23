# Sensory Band

The wearable half of a low-cost **transradial myoelectric prosthetic**. The band sits on the user's residual forearm, reads muscle activity (EMG) and forearm orientation (IMU), and sends both over Bluetooth Low Energy (BLE) to the [prosthetic arm](../Prosthetic%20arm/). It runs MicroPython on a **Raspberry Pi Pico W**.

Built for the Industrial Computing Design Project 3 (DES371S) at the Cape Peninsula University of Technology.

## How It Works

1. **EMG:** A surface EMG sensor on the ADC pin reads muscle flex. A 5-sample moving average smooths the signal, and anything below a noise floor of 500 is set to 0.
2. **IMU:** An MPU6050 accelerometer gives the forearm's roll angle. A low-pass filter (`ALPHA = 0.15`) smooths the gravity vectors, then `atan2(x, y)` gives an absolute roll angle from -180° to 180°.
3. **BLE:** The band advertises as `ProstheticBand` and exposes a readable, notifying characteristic. Every 100 ms it writes a packet in the form:

   ```
   <emg>,<roll>\n      e.g.  "6240,-12\n"
   ```

The arm connects to the band, reads the packet, and uses it to open and close the hand and rotate the wrist.

## Hardware

| Part | Notes |
| --- | --- |
| Raspberry Pi Pico W | Runs the band code and acts as the BLE peripheral |
| Generic dual-supply EMG sensor + electrodes | Powered from two 9V batteries (±9V) |
| 2 × 100 kΩ resistors | Voltage divider that scales the EMG signal into the Pico's 0 to 3.3 V ADC range |
| MPU6050 IMU | 6-axis accelerometer and gyroscope over I2C |

### Pin map

| Function | Pico pin |
| --- | --- |
| EMG signal (ADC) | `GP26` |
| MPU6050 SDA | `GP4` |
| MPU6050 SCL | `GP5` |

## Files

```
Sensory band/
├── bcode.py      # Main program: reads EMG and IMU and sends them over BLE
├── EMG.py        # Standalone EMG test: prints the smoothed ADC value
├── imu.py        # MPU6050 driver (adapted from micropython-IMU, MIT licence)
├── vector3d.py   # 3D vector helper used by imu.py
└── lib/
    └── aioble/   # BLE library for MicroPython (aioble 0.6.2)
```

## Setup

1. Flash **MicroPython** (with Bluetooth support) onto the Pico W.
2. Copy `imu.py`, `vector3d.py` and the `lib/` folder onto the Pico. You can use Thonny or `mpremote`.
3. Copy `bcode.py` to the Pico as `main.py` so it runs on power-up (or run it from Thonny while testing).
4. Wire the EMG sensor and MPU6050 as shown above.
5. Power the Pico over USB, and the EMG sensor from its 9V batteries.
6. Place the electrodes on the forearm muscle. Put the reference electrode about 2 cm away.

Testing in stages:

- Run `EMG.py` to check the signal before using the full program. Flex and relax the muscle and note the values.
- Then run `bcode.py`. You should see `Band Ready! Waiting for Arm to connect...`, and then `Sent -> EMG: ... | Roll: ...` lines.

## Tuning

| Setting | Where | Effect |
| --- | --- | --- |
| Noise floor (`500`) | `bcode.py` | Raise it if the EMG value is non-zero at rest |
| `ALPHA` (`0.15`) | `bcode.py` | Lower values make the roll angle smoother but slower |
| `SCALE` (`7.2`) | `bcode.py` | Scales the raw accelerometer readings |
| Send interval (`100` ms) | `bcode.py` | Update rate of the BLE packet |

The flex threshold that triggers the hand is set on the arm side (`FLEX_THRESHOLD` in the arm's code), not here.

## Troubleshooting

- **The arm can't find the band:** Check the band is powered and that the name is still `ProstheticBand` on both sides.
- **EMG always 0:** The signal is below the noise floor. Check the electrode contact, the ±9V supply and the voltage divider.
- **EMG noisy or saturated:** Check the electrode placement and that the ground is shared correctly.
- **Roll angle is wrong or jumps:** Check the MPU6050 wiring (`GP4` and `GP5`) and the orientation of the band on the arm.

## Licence

`imu.py` and `vector3d.py` are by Peter Hinch and Sebastian Plamauer under the MIT licence. `aioble` is part of [micropython-lib](https://github.com/micropython/micropython-lib) (MIT licence). No licence has been chosen yet for the rest. Consider adding one, such as MIT.                                                     


# Prosthetic Arm

The robotic hand and wrist half of a low-cost **transradial myoelectric prosthetic**. It receives EMG and wrist-angle data over Bluetooth Low Energy (BLE) from the [sensory band](../Sensory%20band/) and moves servo-driven, tendon-actuated fingers and a rotating wrist. It runs MicroPython on a **Raspberry Pi Pico W**.

Built for the Industrial Computing Design Project 3 (DES371S) at the Cape Peninsula University of Technology. In the project report, the prototype cost about R1 411, which is over 99% less than a commercial myoelectric prosthesis.

## How It Works

1. The arm scans for a BLE device named `ProstheticBand` and connects to it.
2. It reads a packet of the form `<emg>,<roll>` about every 100 ms.
3. **Fingers (toggle):** When the EMG value rises above `FLEX_THRESHOLD` (default `5000`), the hand toggles between open and closed. A 1-second cooldown and a re-arm check prevent false triggers. The flex must drop below 50% of the threshold before another flex is detected.
4. **Wrist:** The roll angle is limited to -60° to +60° and mapped to a wrist servo angle of 20° to 140°.

```
 Band (EMG, roll) ──BLE──▶ Arm Pico ──PWM──▶ finger servos ──tendons──▶ fingers
                                      └─PWM──▶ wrist servo
```

## Hardware

| Part | Notes |
| --- | --- |
| Raspberry Pi Pico W | BLE central and servo controller |
| MG995 high-torque servos | Five for the fingers and one for the wrist (per the project report) |
| 3D-printed hand and forearm | Open-source InMoov design |
| Fishing line and extension springs | Tendons pull the fingers closed, and springs return them |
| Separate 6V battery packs | Each servo has its own supply, so the Pico doesn't brown out |

> **Power:** The servos draw a lot of current. Power them from separate battery packs and connect the grounds together. Don't power them from the Pico's pins.

### Pin map

| Servo | Pico pin |
| --- | --- |
| Pinky | `GP14` |
| Ring | `GP15` |
| Middle | `GP16` |
| Index and thumb | `GP17` |
| Wrist | `GP18` |

Servos use 50 Hz PWM.

### Finger positions

| Finger | Open (relaxed) | Closed (contracted) |
| --- | --- | --- |
| Pinky | 90° | 0° |
| Ring | 90° | 180° |
| Middle | 90° | 180° |
| Index and thumb | 90° | 180° |

The pinky closes in the opposite direction, which is why it goes to 0° instead of 180°.

## Files

```
Prosthetic arm/
├── final code .py        # Main program (the last, uncommented version is the active one)
├── servo_configure.py    # Servo test and calibration snippets
└── lib/
    ├── aioble/           # BLE library for MicroPython
    ├── servo.py          # PCA9685 servo helper
    └── pca9685.py        # PCA9685 driver
```

- **`final code .py`** has several earlier versions of the program commented out in triple quotes: a threshold-8000 toggle, a BLE receive test, a wrist-only test and a three-state version (relax, contract, pause). The final, uncommented version at the bottom is the one that runs.
- **`servo_configure.py`** is a collection of commented-out test scripts for checking individual servos and finger positions. They are useful when attaching the tendons and calibrating the servo ranges.
- **`servo.py` and `pca9685.py`** were used while testing with a PCA9685 servo driver board. The final design drives the servos directly from the Pico's PWM pins, because the PCA9685 couldn't supply enough current.

## Setup

1. Flash **MicroPython** (with Bluetooth support) onto the Pico W.
2. Copy the `lib/` folder to the Pico.
3. Wire the servos as in the pin map, each with its own 6V supply and a shared ground.
4. Copy the final code to the Pico as `main.py`, or run it from Thonny while testing. The file name has a space and a stray dot (`final code .py`), so rename it first, for example to `main.py`.
5. Power on the **sensory band** first, so it's advertising.
6. Power on the arm. It should print `Scanning for ProstheticBand...`, then `Connected to band!`.

## Usage

- **Flex your muscle** to close the hand. Flex again to open it.
- **Rotate your forearm** to rotate the wrist.

Example console output:

```
>>> CONTRACT: Closing Fingers
EMG:  6120 | IMU:  15° | Wrist:  50° | Hand: CLOSED
```

## Calibration

| Setting | Where | Notes |
| --- | --- | --- |
| `FLEX_THRESHOLD` | main program | Raise or lower it to suit the user's muscle strength |
| `COOLDOWN_MS` | main program | Minimum time between toggles |
| Finger angles | `set_all_fingers()` | Adjust the open and closed angles to match the tendon tension |
| Wrist range | wrist mapping | Currently limited to 20° to 140° so the servo and arm don't hit their limits |

Use the scripts in `servo_configure.py` to set each servo to a known angle before attaching the tendons.

## Known Limitations

- If the band isn't found within 5 seconds, or the connection drops, the program stops and doesn't reconnect. Restart the arm to try again.
- The code reads the band by polling, not by notifications, so there can be occasional dropouts.
- The project report describes two force-sensitive resistors in the palm and an LED bar for grip feedback. That feedback loop is not in the uploaded code, so either add it or remove it from the description.
- The report mentions six servos, but the final code drives five PWM pins (the index and thumb share a pin).

## Related

- [Sensory band](../Sensory%20band/): the wearable that sends the EMG and roll data

## Licence

`aioble` is part of [micropython-lib](https://github.com/micropython/micropython-lib) (MIT licence). No licence has been chosen yet for the rest. Consider adding one, such as MIT.
