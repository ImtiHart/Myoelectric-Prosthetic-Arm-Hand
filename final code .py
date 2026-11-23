'''import aioble
import bluetooth
import asyncio
import time
from machine import Pin, PWM

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# ==========================================
# 1. SERVO SETUP
# ==========================================
pinky_pwm  = PWM(Pin(14))
ring_pwm   = PWM(Pin(15))
middle_pwm = PWM(Pin(16))
index_pwm  = PWM(Pin(17)) # Controls Index & Thumb
wrist_pwm  = PWM(Pin(18)) 

# Set all to 50Hz
for pwm in [pinky_pwm, ring_pwm, middle_pwm, index_pwm, wrist_pwm]:
    pwm.freq(50)

def set_angle(pwm_pin, angle):
    min_duty = 1638
    max_duty = 8192
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

def set_all_fingers(state):
    # State 0 = Open (Relaxed), State 1 = Closed (Contract)
    if state == 0:
        set_angle(pinky_pwm, 90)
        set_angle(ring_pwm, 90)
        set_angle(middle_pwm, 90)
        set_angle(index_pwm, 90)
    elif state == 1:
        set_angle(pinky_pwm, 0)    # Pinky goes to 0
        set_angle(ring_pwm, 180)   # Ring goes to 180
        set_angle(middle_pwm, 180) # Middle goes to 180
        set_angle(index_pwm, 180)  # Index & Thumb go to 180

# ==========================================
# 2. BLUETOOTH CONNECTION
# ==========================================
async def main():
    print("Scanning for ProstheticBand...")
    device = None
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == "ProstheticBand":
                device = result.device
                break

    if not device:
        print("Band not found. Is it powered on?")
        return

    connection = await device.connect()
    print("Connected to band!")

    service = await connection.service(_SERVICE_UUID)
    data_char = await service.characteristic(_DATA_CHAR_UUID)

    # --- STATE MACHINE VARIABLES ---
    FLEX_THRESHOLD = 8000   # Adjust this based on your muscle strength
    COOLDOWN_MS = 1000      # 1 second cooldown between flexes
    
    is_closed = False       # Tracks if hand is currently closed
    ignore_until = 0        # Cooldown timer
    is_flexed = False       # Prevents continuous triggering
    
    # Set initial hand state (Open)
    set_all_fingers(0)

    while connection.is_connected():
        data = await data_char.read()
        decoded = data.decode('utf-8').strip()
        
        try:
            emg_str, roll_str = decoded.split(',')
            emg_val = int(emg_str)
            roll_angle = int(roll_str)
            
            now = time.ticks_ms()

            # ==========================================
            # 3. FINGER TOGGLE LOGIC
            # ==========================================
            # Only check for a flex if we are past the cooldown
            if time.ticks_diff(now, ignore_until) > 0 and not is_flexed:
                if emg_val > FLEX_THRESHOLD:
                    is_flexed = True
                    ignore_until = time.ticks_add(now, COOLDOWN_MS)
                    
                    # Toggle state
                    is_closed = not is_closed
                    if is_closed:
                        print(">>> CONTRACT: Closing Fingers")
                        set_all_fingers(1)
                    else:
                        print(">>> RELAX: Opening Fingers")
                        set_all_fingers(0)

            # Reset the flex flag when the muscle drops below threshold
            if emg_val < (FLEX_THRESHOLD * 0.5):
                is_flexed = False

            # ==========================================
            # 4. WRIST MAPPING LOGIC
            # ==========================================
            # Map IMU Range (0 to 60) -> Servo Range (20 to 140)
            # Formula: servo = ((imu - 0) / 60) * (140 - 20) + 20
            
            # Constrain IMU angle to 0-60
            if roll_angle < 0: roll_angle = 0
            if roll_angle > 60: roll_angle = 60
            
            wrist_angle = int((roll_angle / 60) * 120) + 20
            set_angle(wrist_pwm, wrist_angle)

            # Print readout
            state_text = "CLOSED" if is_closed else "OPEN"
            print(f"EMG: {emg_val:5d} | IMU: {roll_angle:3d}° | Wrist: {wrist_angle:3d}° | Hand: {state_text}")

        except ValueError:
            pass
            
        await asyncio.sleep_ms(100) # 10Hz readout

asyncio.run(main())'''
'''import aioble
import bluetooth
import asyncio

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

async def main():
    print("Scanning for ProstheticBand...")
    device = None
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == "ProstheticBand":
                device = result.device
                break

    if not device:
        print("Band not found. Is it powered on?")
        return

    connection = await device.connect()
    print("Connected to band!")

    service = await connection.service(_SERVICE_UUID)
    data_char = await service.characteristic(_DATA_CHAR_UUID)

    print("Receiving Data...")

    while connection.is_connected():
        # Read the data from the Band
        data = await data_char.read()
        decoded = data.decode('utf-8').strip()
        
        try:
            # The Band sends data in the format "EMG,ROLL"
            emg_str, roll_str = decoded.split(',')
            emg_val = int(emg_str)
            roll_angle = int(roll_str)
            
            # Print the received values
            print(f"Received -> EMG: {emg_val:5d} | IMU Roll: {roll_angle:3d}°")

        except ValueError:
            pass # Ignore malformed data packets
            
        await asyncio.sleep_ms(100) # Read 10 times a second

asyncio.run(main())'''
'''import aioble
import bluetooth
import asyncio
from machine import Pin, PWM

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# --- WRIST SERVO SETUP (GP18) ---
wrist_pwm = PWM(Pin(18))
wrist_pwm.freq(50)

def set_wrist_angle(angle):
    min_duty = 1638
    max_duty = 8192
    # Constrain the servo to its mechanical limits
    if angle < 20: angle = 20
    if angle > 140: angle = 140
    
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    wrist_pwm.duty_u16(duty)

# Set initial wrist position (Center)
set_wrist_angle(80)

async def main():
    print("Scanning for ProstheticBand...")
    device = None
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == "ProstheticBand":
                device = result.device
                break

    if not device:
        print("Band not found. Is it powered on?")
        return

    connection = await device.connect()
    print("Connected to band!")

    service = await connection.service(_SERVICE_UUID)
    data_char = await service.characteristic(_DATA_CHAR_UUID)

    print("Receiving Data...")

    while connection.is_connected():
        # Read the data from the Band
        data = await data_char.read()
        decoded = data.decode('utf-8').strip()
        
        try:
            # The Band sends data in the format "EMG,ROLL"
            emg_str, roll_str = decoded.split(',')
            emg_val = int(emg_str)
            roll_angle = int(roll_str)
            
            # ==========================================
            # WRIST MAPPING LOGIC
            # IMU: -60 to +60  -->  Servo: 20 to 140
            # ==========================================
            
            # 1. Constrain the IMU angle to prevent math errors if you over-rotate
            if roll_angle < -60: roll_angle = -60
            if roll_angle > 60: roll_angle = 60
            
            # 2. Map the range
            # Formula: ((value - from_min) / (from_max - from_min)) * (to_max - to_min) + to_min
            wrist_angle = int(((roll_angle + 60) / 120) * 120) + 20
            
            # 3. Move the servo
            set_wrist_angle(wrist_angle)

            # Print the received values
            print(f"Received -> EMG: {emg_val:5d} | IMU: {roll_angle:3d}° | Wrist Servo: {wrist_angle:3d}°")

        except ValueError:
            pass # Ignore malformed data packets
            
        await asyncio.sleep_ms(100) # Read 10 times a second

asyncio.run(main())'''
'''import aioble
import bluetooth
import asyncio
import time
from machine import Pin, PWM

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# ==========================================
# 1. SERVO SETUP
# ==========================================
pinky_pwm  = PWM(Pin(14))
ring_pwm   = PWM(Pin(15))
middle_pwm = PWM(Pin(16))
index_pwm  = PWM(Pin(17)) # Controls Index & Thumb
wrist_pwm  = PWM(Pin(18)) 

for pwm in [pinky_pwm, ring_pwm, middle_pwm, index_pwm, wrist_pwm]:
    pwm.freq(50)

def set_angle(pwm_pin, angle):
    min_duty = 1638
    max_duty = 8192
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

def set_all_fingers(state):
    if state == 0: # RELAX (Open)
        set_angle(pinky_pwm, 90)
        set_angle(ring_pwm, 90)
        set_angle(middle_pwm, 90)
        set_angle(index_pwm, 90)
    elif state == 1: # CONTRACT (Close)
        set_angle(pinky_pwm, 0)
        set_angle(ring_pwm, 180)
        set_angle(middle_pwm, 180)
        set_angle(index_pwm, 180)
    elif state == 2: # PAUSE (Hold current position)
        # We do nothing here. The servos will maintain their last position automatically.
        pass

# ==========================================
# 2. MAIN LOOP
# ==========================================
async def main():
    print("Scanning for ProstheticBand...")
    device = None
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == "ProstheticBand":
                device = result.device
                break

    if not device:
        print("Band not found. Is it powered on?")
        return

    connection = await device.connect()
    print("Connected to band!")

    service = await connection.service(_SERVICE_UUID)
    data_char = await service.characteristic(_DATA_CHAR_UUID)

    # --- STATE MACHINE VARIABLES ---
    FLEX_THRESHOLD = 5000   # Trigger point for the hand
    COOLDOWN_MS = 1000      # 1 second delay between flexes
    
    hand_state = 0          # 0 = Relax, 1 = Contract, 2 = Pause
    ignore_until = 0        
    is_flexed = False       
    
    # Initial State
    set_all_fingers(0)
    set_angle(wrist_pwm, 80) # Wrist Center

    while connection.is_connected():
        data = await data_char.read()
        decoded = data.decode('utf-8').strip()
        
        try:
            emg_str, roll_str = decoded.split(',')
            emg_val = int(emg_str)
            roll_angle = int(roll_str)
            
            now = time.ticks_ms()

            # ==========================================
            # 3-STEP FINGER STATE MACHINE
            # ==========================================
            if time.ticks_diff(now, ignore_until) > 0 and not is_flexed:
                if emg_val > FLEX_THRESHOLD:
                    is_flexed = True
                    ignore_until = time.ticks_add(now, COOLDOWN_MS)
                    
                    # Cycle to the next state
                    if hand_state == 0:
                        hand_state = 1
                        print(">>> [STATE 1] CONTRACT (Closing Hand)")
                        set_all_fingers(1)
                    elif hand_state == 1:
                        hand_state = 2
                        print(">>> [STATE 2] PAUSE (Holding Position)")
                        set_all_fingers(2)
                    elif hand_state == 2:
                        hand_state = 0
                        print(">>> [STATE 0] RELAX (Opening Hand)")
                        set_all_fingers(0)

            # Reset flex flag when muscle relaxes
            if emg_val < (FLEX_THRESHOLD * 0.5):
                is_flexed = False

            # ==========================================
            # WRIST ROTATION LOGIC
            # ==========================================
            # Map IMU Range (-60 to +60) -> Servo Range (20 to 140)
            if roll_angle < -60: roll_angle = -60
            if roll_angle > 60: roll_angle = 60
            
            wrist_angle = int(((roll_angle + 60) / 120) * 120) + 20
            set_angle(wrist_pwm, wrist_angle)

            # --- READOUT ---
            state_names = ["RELAX", "CONTRACT", "PAUSE"]
            print(f"EMG: {emg_val:5d} | IMU: {roll_angle:3d}° | Wrist: {wrist_angle:3d}° | State: {state_names[hand_state]}")

        except ValueError:
            pass
            
        await asyncio.sleep_ms(100) 

asyncio.run(main())'''
import aioble
import bluetooth
import asyncio
import time
from machine import Pin, PWM

_SERVICE_UUID = bluetooth.UUID(0x1848)
_DATA_CHAR_UUID = bluetooth.UUID(0x2A6E) 

# ==========================================
# 1. SERVO SETUP
# ==========================================
pinky_pwm  = PWM(Pin(14))
ring_pwm   = PWM(Pin(15))
middle_pwm = PWM(Pin(16))
index_pwm  = PWM(Pin(17)) # Controls Index & Thumb
wrist_pwm  = PWM(Pin(18)) 

for pwm in [pinky_pwm, ring_pwm, middle_pwm, index_pwm, wrist_pwm]:
    pwm.freq(50)

def set_angle(pwm_pin, angle):
    min_duty = 1638
    max_duty = 8192
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

def set_all_fingers(is_closed):
    if is_closed:
        # CONTRACT
        set_angle(pinky_pwm, 0)
        set_angle(ring_pwm, 180)
        set_angle(middle_pwm, 180)
        set_angle(index_pwm, 180)
    else:
        # RELAX
        set_angle(pinky_pwm, 90)
        set_angle(ring_pwm, 90)
        set_angle(middle_pwm, 90)
        set_angle(index_pwm, 90)

# ==========================================
# 2. MAIN LOOP
# ==========================================
async def main():
    print("Scanning for ProstheticBand...")
    device = None
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == "ProstheticBand":
                device = result.device
                break

    if not device:
        print("Band not found. Is it powered on?")
        return

    connection = await device.connect()
    print("Connected to band!")

    service = await connection.service(_SERVICE_UUID)
    data_char = await service.characteristic(_DATA_CHAR_UUID)

    # --- STATE VARIABLES ---
    FLEX_THRESHOLD = 5000   
    COOLDOWN_MS = 1000      
    
    is_closed = False       # Tracks if hand is currently closed
    ignore_until = 0        # Cooldown timer
    is_flexed = False       # Prevents continuous triggering
    
    # Initial State
    set_all_fingers(False)
    set_angle(wrist_pwm, 80) # Wrist Center

    while connection.is_connected():
        data = await data_char.read()
        decoded = data.decode('utf-8').strip()
        
        try:
            emg_str, roll_str = decoded.split(',')
            emg_val = int(emg_str)
            roll_angle = int(roll_str)
            
            now = time.ticks_ms()

            # ==========================================
            # TOGGLE LOGIC (Contract / Relax)
            # ==========================================
            if time.ticks_diff(now, ignore_until) > 0 and not is_flexed:
                if emg_val > FLEX_THRESHOLD:
                    is_flexed = True
                    ignore_until = time.ticks_add(now, COOLDOWN_MS)
                    
                    # Toggle the state
                    is_closed = not is_closed
                    
                    if is_closed:
                        print(">>> CONTRACT: Closing Fingers")
                        set_all_fingers(True)
                    else:
                        print(">>> RELAX: Opening Fingers")
                        set_all_fingers(False)

            # Reset the flex flag when the muscle relaxes
            if emg_val < (FLEX_THRESHOLD * 0.5):
                is_flexed = False

            # ==========================================
            # WRIST ROTATION LOGIC
            # ==========================================
            # Map IMU Range (-60 to +60) -> Servo Range (20 to 140)
            if roll_angle < -60: roll_angle = -60
            if roll_angle > 60: roll_angle = 60
            
            wrist_angle = int(((roll_angle + 60) / 120) * 120) + 20
            set_angle(wrist_pwm, wrist_angle)

            state_text = "CLOSED" if is_closed else "OPEN"
            print(f"EMG: {emg_val:5d} | IMU: {roll_angle:3d}° | Wrist: {wrist_angle:3d}° | Hand: {state_text}")

        except ValueError:
            pass
            
        await asyncio.sleep_ms(100) 

asyncio.run(main())