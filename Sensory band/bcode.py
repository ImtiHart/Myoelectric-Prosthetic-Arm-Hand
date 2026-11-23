# ============================================================
# SENSOR BAND - Peripheral Pico W
# Reads IMU, calculates roll angle, sends over BLE
# ============================================================
'''
import aioble
import bluetooth
import struct
import time
import math
import asyncio
from machine import I2C, Pin
from imu import MPU6050

# ============================================================
# BLE UUIDs (must match the Central/Arm code)
# ============================================================
_SERVICE_UUID = bluetooth.UUID(0x1848)
_ROLL_CHAR_UUID = bluetooth.UUID(0x2A6E)

# ============================================================
# IMU SETUP
# ============================================================
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)

SCALE = 7.2

# Smoothing buffers
BUFFER_SIZE = 10
x_buffer = [0] * BUFFER_SIZE
z_buffer = [0] * BUFFER_SIZE

x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0

ALPHA = 0.15
DEADBAND = 0.5
last_roll = 0.0

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def moving_average(buffer, new_value):
    buffer.pop(0)
    buffer.append(new_value)
    return sum(buffer) / len(buffer)

def low_pass_filter(previous, new_value, alpha):
    return previous + alpha * (new_value - previous)

def get_roll_angle(x, z):
    return math.atan2(x, z) * 180 / math.pi

# ============================================================
# BLE SETUP
# ============================================================
service = aioble.Service(_SERVICE_UUID)
roll_char = aioble.Characteristic(service, _ROLL_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

# ============================================================
# BLE TASK - Advertise and wait for connection
# ============================================================
async def peripheral_task():
    while True:
        print("Advertising as ProstheticBand...")
        async with await aioble.advertise(
            250_000,
            name="ProstheticBand",
            services=[_SERVICE_UUID]
        ) as connection:
            print("Central connected")
            await connection.disconnected(timeout_ms=None)
            print("Central disconnected")

# ============================================================
# SENSOR TASK - Read IMU and send roll angle
# ============================================================
async def sensor_task():
    global x_filtered, z_filtered, roll_filtered, last_roll

    # Pre-fill buffers for stability
    for i in range(BUFFER_SIZE):
        x = mpu.accel.x * SCALE
        z = mpu.accel.z * SCALE
        x_buffer[i] = x
        z_buffer[i] = z
        await asyncio.sleep_ms(20)

    x_filtered = sum(x_buffer) / BUFFER_SIZE
    z_filtered = sum(z_buffer) / BUFFER_SIZE
    roll_filtered = get_roll_angle(x_filtered, z_filtered)

    while True:
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE

        x_avg = moving_average(x_buffer, x_raw)
        z_avg = moving_average(z_buffer, z_raw)

        x_filtered = low_pass_filter(x_filtered, x_avg, ALPHA)
        z_filtered = low_pass_filter(z_filtered, z_avg, ALPHA)

        roll_raw = get_roll_angle(x_filtered, z_filtered)

        if abs(roll_raw - last_roll) > DEADBAND:
            roll_filtered = low_pass_filter(roll_filtered, roll_raw, ALPHA)
            last_roll = roll_filtered

        roll_int = int(roll_filtered * 10)
        roll_char.write(struct.pack("<h", roll_int), send_update=True)

        print(f"Roll: {roll_filtered:7.2f}°")
        await asyncio.sleep_ms(50)

# ============================================================
# MAIN
# ============================================================
async def main():
    tasks = [
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(sensor_task()),
    ]
    await asyncio.gather(*tasks)

asyncio.run(main())'''
##################################################################
###############################################################
###########################################################
#####################################################
'''import aioble
import bluetooth
import asyncio
from machine import Pin, ADC

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

emg_adc = ADC(Pin(26))
emg_values = []

service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    print("Calibrating...")
    await asyncio.sleep_ms(1000)
    baseline = emg_adc.read_u16()
    print(f"Baseline: {baseline}")

    while True:
        val = emg_adc.read_u16()
        # Show the raw difference
        diff = abs(val - baseline)
        print(f"Raw: {val} | Difference: {diff}")
        await asyncio.sleep_ms(200)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
'''import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0
ALPHA = 0.15
last_roll = 0.0

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []
emg_baseline = 0  # Will store the resting voltage

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered, last_roll, emg_baseline

    # ==========================================
    # CALIBRATION PHASE (Do not flex arm!)
    # ==========================================
    print("Calibrating EMG Baseline... Keep arm relaxed!")
    await asyncio.sleep_ms(1000) 
    
    cal_sum = 0
    for _ in range(10):
        cal_sum += emg_adc.read_u16()
        await asyncio.sleep_ms(50)
    
    emg_baseline = cal_sum / 10
    print(f"Calibration complete! Baseline is: {int(emg_baseline)}")

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # Subtract baseline and get absolute value
        clean_emg = abs(avg_emg - emg_baseline)

        # IGNORE NOISE: If the signal is below 15,000, treat it as 0
        if clean_emg < 15000:
            emg_final = 0
        else:
            emg_final = int(clean_emg)

        # 2. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        roll_raw = math.atan2(x_filtered, z_filtered) * 180 / math.pi
        if abs(roll_raw - last_roll) > 0.5:
            roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)
            last_roll = roll_filtered

        # 3. Send both
        payload = f"{emg_final},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {emg_final:5d} | Roll: {int(roll_filtered)}")
        await asyncio.sleep_ms(100)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
'''import aioble
import bluetooth
import struct
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) # One pipe for both

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0
ALPHA = 0.15
last_roll = 0.0

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered, last_roll

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # 2. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        roll_raw = math.atan2(x_filtered, z_filtered) * 180 / math.pi
        if abs(roll_raw - last_roll) > 0.5:
            roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)
            last_roll = roll_filtered

        # 3. Send both as a single string "EMG,ROLL"
        # Example: "45000,25.5"
        payload = f"{int(avg_emg)},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {int(avg_emg)} | Roll: {int(roll_filtered)}")
        await asyncio.sleep_ms(50)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
##############################################
####################################################
#########################################################
'''
import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0
ALPHA = 0.15
last_roll = 0.0

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered, last_roll

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # 2. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        roll_raw = math.atan2(x_filtered, z_filtered) * 180 / math.pi
        if abs(roll_raw - last_roll) > 0.5:
            roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)
            last_roll = roll_filtered

        # 3. Send both as a single string "EMG,ROLL"
        payload = f"{int(avg_emg)},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {int(avg_emg)} | Roll: {int(roll_filtered)}")
        
        # CHANGED: Send every 500ms (half a second)
        await asyncio.sleep_ms(500)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
###########################
###################
############
'''
import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0
ALPHA = 0.15

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []

# High-pass filter variable
# This tracks the drifting baseline and subtracts it
emg_baseline = 32000.0  # Starting point (approx 1.65V)
HP_ALPHA = 0.02         # Lower = slower to adapt to drift, higher = faster

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered, emg_baseline

    print("Calibrating EMG baseline... Please keep arm relaxed.")
    # Read the sensor 20 times to find the true resting baseline
    for _ in range(20):
        emg_values.append(emg_adc.read_u16())
        if len(emg_values) > 5: emg_values.pop(0)
        await asyncio.sleep_ms(50)
    
    # Set the baseline to the average of the resting state
    emg_baseline = sum(emg_values) / len(emg_values)
    print(f"Calibration complete! Baseline set to: {emg_baseline}")

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # 2. Apply High-Pass Filter
        emg_baseline = emg_baseline + HP_ALPHA * (avg_emg - emg_baseline)
        emg_clean = avg_emg - emg_baseline

        # 3. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        roll_raw = math.atan2(x_filtered, z_filtered) * 180 / math.pi
        roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)

        # 4. Send both
        payload = f"{int(emg_clean)},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        #print(f"Sent -> EMG: {int(emg_clean):5d} | Roll: {int(roll_filtered)}")
        print(f"Raw: {int(avg_emg)} | Clean: {int(emg_clean)}")
        await asyncio.sleep_ms(100)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
####################################################
#################################################
#############################################
'''
import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0
ALPHA = 0.15

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # Clean up tiny noise (anything under 500 becomes 0)
        if avg_emg < 500:
            emg_final = 0
        else:
            emg_final = int(avg_emg)

        # 2. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        roll_raw = math.atan2(x_filtered, z_filtered) * 180 / math.pi
        roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)

        # 3. Send both
        payload = f"{emg_final},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {emg_final:5d} | Roll: {int(roll_filtered)}")
        
        await asyncio.sleep_ms(100)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
#################################
######################
####################
'''
import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0
ALPHA = 0.15

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # Apply a noise floor (anything under 500 becomes 0)
        # This makes the data perfectly clean
        if avg_emg < 500:
            emg_final = 0
        else:
            emg_final = int(avg_emg)

        # 2. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        roll_raw = math.atan2(x_filtered, z_filtered) * 180 / math.pi
        roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)

        # 3. Send both values
        payload = f"{emg_final},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {emg_final:5d} | Roll: {int(roll_filtered)}")
        
        # Transmit every 100ms (10 times a second)
        await asyncio.sleep_ms(100)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
################################
############################
######################
'''import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
ALPHA = 0.15

# Variables for calibration
offset_x = 0.0
offset_z = 0.0
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered, offset_x, offset_z

    # ==========================================
    # CALIBRATION PHASE (New)
    # ==========================================
    print("Calibrating IMU... Keep sensor flat (0 degrees)")
    await asyncio.sleep_ms(500) # Give user time to hold it still
    
    # Take 10 readings and average them to find the "Zero" point
    sum_x = 0
    sum_z = 0
    for i in range(10):
        sum_x += mpu.accel.x * SCALE
        sum_z += mpu.accel.z * SCALE
        await asyncio.sleep_ms(50)
        
    offset_x = sum_x / 10.0
    offset_z = sum_z / 10.0
    
    # Start the filtered variables at the calibrated zero point
    x_filtered = offset_x
    z_filtered = offset_z
    
    print(f"Calibration complete! X_Offset: {offset_x:.2f}, Z_Offset: {offset_z:.2f}")

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)
        emg_final = 0 if avg_emg < 500 else int(avg_emg)

        # 2. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        
        # Apply low-pass filter
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        # Subtract the offset to find the true angle relative to the start position
        x_calibrated = x_filtered - offset_x
        z_calibrated = z_filtered - offset_z
        
        # Calculate Roll (Y-axis rotation for forearm)
        # Using atan2(Z, X) or atan2(X, Z) depending on how the board is mounted.
        # We use X and Z here based on your previous testing.
        roll_raw = math.atan2(x_calibrated, z_calibrated) * 180 / math.pi
        roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)

        # 3. Send both values
        payload = f"{emg_final},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {emg_final:5d} | Roll: {int(roll_filtered)}")
        
        await asyncio.sleep_ms(100)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
##############################
############################
####################
'''import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
ALPHA = 0.15

offset_x = 0.0
offset_z = 0.0
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered, offset_x, offset_z

    print("Calibrating IMU... Keep sensor flat (0 degrees)")
    await asyncio.sleep_ms(500) 
    
    sum_x = 0
    sum_z = 0
    for i in range(10):
        sum_x += mpu.accel.x * SCALE
        sum_z += mpu.accel.z * SCALE
        await asyncio.sleep_ms(50)
        
    offset_x = sum_x / 10.0
    offset_z = sum_z / 10.0
    x_filtered = offset_x
    z_filtered = offset_z
    print(f"Calibration complete! X_Offset: {offset_x:.2f}, Z_Offset: {offset_z:.2f}")

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)
        emg_final = 0 if avg_emg < 500 else int(avg_emg)

        # 2. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        x_calibrated = x_filtered - offset_x
        z_calibrated = z_filtered - offset_z
        
        roll_raw = math.atan2(x_calibrated, z_calibrated) * 180 / math.pi
        roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)

        # --- FIX: Constrain the Roll Angle ---
        # Clamp the angle to +/- 80 degrees. 
        # If the math says 124, we force it to 80 so it doesn't break the servo.
        final_roll = int(roll_filtered)
        
        if final_roll > 80:
            final_roll = 80
        elif final_roll < -80:
            final_roll = -80
            
        # Apply a tiny dead zone so it doesn't jitter at 0
        if abs(final_roll) < 2:
            final_roll = 0

        # 3. Send both values
        payload = f"{emg_final},{final_roll}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {emg_final:5d} | Roll: {final_roll}")
        
        await asyncio.sleep_ms(100)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''
########################################
##############################
#########################
import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
ALPHA = 0.15

# IMU Filter Variables
x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0
last_roll = 0.0

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []
emg_baseline = 0

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered, last_roll, emg_baseline

    # ==========================================
    # CALIBRATION PHASE
    # ==========================================
    print("Calibrating... Keep arm relaxed and sensor flat!")
    await asyncio.sleep_ms(1000) 
    
    # Calibrate EMG
    cal_sum = 0
    for _ in range(20):
        cal_sum += emg_adc.read_u16()
        await asyncio.sleep_ms(50)
    emg_baseline = cal_sum / 20.0
    print(f"EMG Baseline: {int(emg_baseline)}")

    # Calibrate IMU starting position (Pre-fill filters)
    x_filtered = mpu.accel.x * SCALE
    z_filtered = mpu.accel.z * SCALE
    roll_filtered = math.atan2(x_filtered, z_filtered) * 180 / math.pi
    last_roll = roll_filtered

    print("Calibration Complete! Sending data...")

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # Subtract baseline and apply threshold
        clean_emg = abs(avg_emg - emg_baseline)
        
        # IGNORE NOISE (Adjust this 8000 based on your final flex test)
        if clean_emg < 8000:
            emg_final = 0
        else:
            emg_final = int(clean_emg)

        # 2. Read IMU (Absolute Angle Math)
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        roll_raw = math.atan2(x_filtered, z_filtered) * 180 / math.pi
        
        if abs(roll_raw - last_roll) > 0.5:
            roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)
            last_roll = roll_filtered

        # 3. Send both values as a single string "EMG,ROLL"
        payload = f"{emg_final},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {emg_final:5d} | Roll: {int(roll_filtered)}")
        await asyncio.sleep_ms(100)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())
'''import aioble
import bluetooth
import math
import asyncio
from machine import I2C, Pin, ADC
from imu import MPU6050

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- IMU SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
mpu = MPU6050(i2c)
SCALE = 7.2
ALPHA = 0.15

x_filtered = 0.0
z_filtered = 0.0
roll_filtered = 0.0
last_roll = 0.0

# --- EMG SETUP ---
emg_adc = ADC(Pin(26))
emg_values = []

# High-Pass Filter Variables
emg_baseline = 31522.0 
HP_ALPHA = 0.05 # Increased from 0.02 to settle faster

# --- BLE SETUP ---
service = aioble.Service(_SERVICE_UUID)
data_char = aioble.Characteristic(service, _DATA_CHAR_UUID, read=True, notify=True)
aioble.register_services(service)

async def peripheral_task():
    while True:
        async with await aioble.advertise(250_000, name="ProstheticBand", services=[_SERVICE_UUID]) as connection:
            print("Arm Connected")
            await connection.disconnected(timeout_ms=None)

async def main_task():
    global x_filtered, z_filtered, roll_filtered, last_roll, emg_baseline

    print("Calibrating IMU... Keep sensor flat!")
    await asyncio.sleep_ms(500)
    
    x_filtered = mpu.accel.x * SCALE
    z_filtered = mpu.accel.z * SCALE
    roll_filtered = math.atan2(x_filtered, z_filtered) * 180 / math.pi
    last_roll = roll_filtered

    print("Starting data transmission...")

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # Apply High-Pass Filter
        emg_baseline = emg_baseline + HP_ALPHA * (avg_emg - emg_baseline)
        clean_emg = avg_emg - emg_baseline
        clean_emg = abs(clean_emg)

        # THRESHOLD: Lowered to 1500
        if clean_emg < 1500:
            emg_final = 0
        else:
            emg_final = int(clean_emg)

        # 2. Read IMU
        x_raw = mpu.accel.x * SCALE
        z_raw = mpu.accel.z * SCALE
        
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)
        
        roll_raw = math.atan2(x_filtered, z_filtered) * 180 / math.pi
        
        if abs(roll_raw - last_roll) > 0.5:
            roll_filtered = roll_filtered + ALPHA * (roll_raw - roll_filtered)
            last_roll = roll_filtered

        # 3. Send both
        payload = f"{emg_final},{int(roll_filtered)}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {emg_final:5d} | Roll: {int(roll_filtered)}")
        
        # Transmit faster (every 50ms instead of 100ms) for less lag
        await asyncio.sleep_ms(50)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())'''