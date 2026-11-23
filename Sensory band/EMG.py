'''from machine import Pin, ADC
import time

emg = ADC(Pin(26)) 
window_size = 5
values = []

while True:
    raw = emg.read_u16()
    values.append(raw)
    if len(values) > window_size:
        values.pop(0)
    avg = sum(values) / len(values)
    
    print(f"EMG: {avg:.0f}")
    time.sleep(0.05)
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
ALPHA = 0.15

# Filtered variables for the absolute angle
x_filtered = 0.0
y_filtered = 0.0
z_filtered = 0.0

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
    global x_filtered, y_filtered, z_filtered

    # Pre-fill filters so it starts smoothly
    x_filtered = mpu.accel.x * SCALE
    y_filtered = mpu.accel.y * SCALE
    z_filtered = mpu.accel.z * SCALE

    print("Band Ready! Waiting for Arm to connect...")

    while True:
        # 1. Read EMG
        emg_adc_val = emg_adc.read_u16()
        emg_values.append(emg_adc_val)
        if len(emg_values) > 5: emg_values.pop(0)
        avg_emg = sum(emg_values) / len(emg_values)

        # Apply a noise floor (anything under 500 becomes 0)
        if avg_emg < 500:
            emg_final = 0
        else:
            emg_final = int(avg_emg)

        # 2. Read IMU (Absolute Angle Math)
        x_raw = mpu.accel.x * SCALE
        y_raw = mpu.accel.y * SCALE
        z_raw = mpu.accel.z * SCALE
        
        # Smooth the raw gravity vectors
        x_filtered = x_filtered + ALPHA * (x_raw - x_filtered)
        y_filtered = y_filtered + ALPHA * (y_raw - y_filtered)
        z_filtered = z_filtered + ALPHA * (z_raw - z_filtered)

        # Calculate ABSOLUTE tilt (-180 to 180)
        roll_rad = math.atan2(x_filtered, y_filtered)
        roll_angle = int(roll_rad * 180 / math.pi)

        # 3. Send both values
        payload = f"{emg_final},{roll_angle}\n"
        data_char.write(payload.encode(), send_update=True)
        
        print(f"Sent -> EMG: {emg_final:5d} | Roll: {roll_angle}")
        
        # Transmit every 100ms
        await asyncio.sleep_ms(100)

async def main():
    await asyncio.gather(
        asyncio.create_task(peripheral_task()),
        asyncio.create_task(main_task())
    )

asyncio.run(main())