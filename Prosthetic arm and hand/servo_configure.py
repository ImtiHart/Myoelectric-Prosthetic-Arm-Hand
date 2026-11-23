''''from machine import Pin, I2C
import time
from servo import Servos

# 1. Setup I2C (GP4 & GP5)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)

# 2. Initialize Servos
servos = Servos(i2c, min_us=600, max_us=2400, degrees=180)

print("Starting full arm test...")

# Move everything to a safe starting position first
for i in range(6):
    servos.position(i, degrees=20)
servos.position(6, degrees=20)
time.sleep(1)

while True:
    # --- TEST 1: FINGERS (Channels 0 to 5) ---
    print("Fingers -> 180 (Closing)")
    for i in range(6): # This loops through 0, 1, 2, 3, 4, 5
        servos.position(i, degrees=180)
    time.sleep(1.5)
    
    print("Fingers -> 20 (Opening)")
    for i in range(6):
        servos.position(i, degrees=20)
    time.sleep(1.5)
    
    # --- TEST 2: WRIST (Channel 6) ---
    print("Wrist -> 140 (Left)")
    servos.position(6, degrees=140)
    time.sleep(1.5)
    
    print("Wrist -> 20 (Right)")
    servos.position(6, degrees=20)
    time.sleep(1.5)'''

##############################################
############################################
'''from machine import Pin, I2C
import time
from servo import Servos

# 1. Setup I2C on GP4 and GP5
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)

# 2. Initialize the Servos
servos = Servos(i2c, min_us=600, max_us=2400, degrees=180)

print("Moving all 5 fingers to 90 degrees simultaneously...")

# 3. Set all five fingers to 90 degrees back-to-back
servos.position(0, degrees=0) # Pinky
servos.position(1, degrees=180) # Ring
servos.position(2, degrees=90) # Middle
servos.position(3, degrees=180) # Index
servos.position(4, degrees=90) # Thumb

print("All fingers are holding at 90 degrees.")
print("You have 30 seconds to attach your tendons.")

# 4. Hold the position for 30 seconds so you can work
for i in range(30, 0, -1):
    print(f"Time left: {i}s")
    time.sleep(1)

print("Done. You can now run your sweeps.")'''

##############################################
'''from machine import Pin, PWM
import time

# Setup PWM on GP6
servo = PWM(Pin(6))
servo.freq(50) # 50Hz for standard servos

def set_angle(angle):
    # Maps 0-180 degrees to duty cycle
    # Pico PWM is 16-bit (0 to 65535)
    # 0.5ms = ~1638, 2.5ms = ~8192
    min_duty = 1638
    max_duty = 8192
    
    # Constrain to 0-180
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

print("Testing servo on GP6...")

while True:
    print("Moving to 20 degrees")
    set_angle(20)
    time.sleep(1.5)
    
    print("Moving to 0 degrees")
    set_angle(0)
    time.sleep(1.5)
    
    print("Moving to 90 degrees")
    set_angle(90)
    time.sleep(1.5)'''
'''
from machine import Pin, PWM
import time

# Setup PWM on GP6
servo = PWM(Pin(6))
servo.freq(50) # 50Hz for standard servos

def set_angle(angle):
    # Maps 0-180 degrees to duty cycle
    # Pico PWM is 16-bit (0 to 65535)
    # 0.5ms = ~1638, 2.5ms = ~8192
    min_duty = 1638
    max_duty = 8192
    
    # Constrain to 0-180
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

print("Testing servo on GP6...")

while True:
    print("Moving to 20 degrees")
    set_angle(20)
    time.sleep(1.5)
    
    print("Moving to 180 degrees")
    set_angle(180)
    time.sleep(1.5)'''
############################################
'''from machine import Pin, PWM
import time

# ==========================================
# 1. SETUP THE 4 DIRECT PICO PINS
# ==========================================
# We will use GP15, GP16, GP17, and GP18
servo1 = PWM(Pin(15)) # E.g., Ring
servo2 = PWM(Pin(16)) # E.g., Middle
servo3 = PWM(Pin(17)) # E.g., Index (or Thumb if Index is broken)
servo4 = PWM(Pin(18)) # E.g., Thumb

# Set all to 50Hz (Standard for servos)
servo1.freq(50)
servo2.freq(50)
servo3.freq(50)
servo4.freq(50)

def set_angle(pwm_pin, angle):
    # Maps 0-180 degrees to duty cycle for standard PWM
    min_duty = 1638  # ~0.5ms
    max_duty = 8192  # ~2.5ms
    
    # Constrain angle
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

# ==========================================
# 2. TEST SEQUENCE
# ==========================================
print("Testing 4 servos on GP15, GP16, GP17, GP18...")

# Move all to center first
set_angle(servo1, 90)
set_angle(servo2, 90)
set_angle(servo3, 90)
set_angle(servo4, 90)
time.sleep(2)

while True:
    print("Moving to 180 (Closing)")
    set_angle(servo1, 180)
    set_angle(servo2, 180)
    set_angle(servo3, 180)
    set_angle(servo4, 180)
    time.sleep(2)
    
    print("Moving to 20 (Opening)")
    set_angle(servo1, 20)
    set_angle(servo2, 20)
    set_angle(servo3, 20)
    set_angle(servo4, 20)
    time.sleep(2)'''
    ##############################
'''from machine import Pin, I2C, PWM
import time
from servo import Servos

# ==========================================
# 1. PCA9685 SETUP (Pinky & Wrist)
# ==========================================
# SDA on GP4, SCL on GP5
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
pca_servos = Servos(i2c, min_us=600, max_us=2400, degrees=180)

# ==========================================
# 2. DIRECT PICO PINS (Ring & Middle)
# ==========================================
ring_pwm = PWM(Pin(15))   # Ring finger
middle_pwm = PWM(Pin(16)) # Middle finger

ring_pwm.freq(50)
middle_pwm.freq(50)

def set_pico_angle(pwm_pin, angle):
    # Maps 0-180 to duty cycle
    min_duty = 1638
    max_duty = 8192
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

# ==========================================
# 3. TEST SEQUENCE
# ==========================================
print("Starting Test for Pinky, Wrist, Ring, and Middle...")

# Move everything to center (90 degrees) first
pca_servos.position(0, degrees=90) # Pinky
pca_servos.position(5, degrees=80) # Wrist (Center)
set_pico_angle(ring_pwm, 90)
set_pico_angle(middle_pwm, 90)
time.sleep(2)

while True:
    print("--- CLOSING ---")
    # PCA Servos
    pca_servos.position(0, degrees=160) # Pinky Close
    pca_servos.position(5, degrees=140) # Wrist Left
    
    # Direct Pico Servos
    set_pico_angle(ring_pwm, 160)
    set_pico_angle(middle_pwm, 160)
    
    time.sleep(2)
    
    print("--- OPENING ---")
    # PCA Servos
    pca_servos.position(0, degrees=20) # Pinky Open
    pca_servos.position(5, degrees=20) # Wrist Right
    
    # Direct Pico Servos
    set_pico_angle(ring_pwm, 20)
    set_pico_angle(middle_pwm, 20)
    
    time.sleep(2)'''
#####################
'''from machine import Pin, I2C
import time
from servo import Servos

# 1. Setup I2C (SDA on GP4, SCL on GP5)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)

# 2. Initialize the PCA9685
pca_servos = Servos(i2c, min_us=600, max_us=2400, degrees=180)

print("Testing Pinky Servo ONLY (Channel 0)...")

# Move Pinky to center first
pca_servos.position(0, degrees=90)
time.sleep(1.5)

while True:
    print("Pinky -> 160 degrees (Close)")
    pca_servos.position(0, degrees=160)
    time.sleep(1.5)
    
    print("Pinky -> 20 degrees (Open)")
    pca_servos.position(0, degrees=20)
    time.sleep(1.5)'''
##########################
'''from machine import Pin, I2C, PWM
import time
from servo import Servos

# ==========================================
# 1. PCA9685 SETUP (Pinky)
# ==========================================
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
pca_servos = Servos(i2c, min_us=600, max_us=2400, degrees=180)

# ==========================================
# 2. DIRECT PICO PINS (Ring, Middle, Index, Thumb)
# ==========================================
ring_pwm = PWM(Pin(15))   # Ring
middle_pwm = PWM(Pin(16)) # Middle
index_pwm = PWM(Pin(18))  # Index
thumb_pwm = PWM(Pin(20))  # Thumb

ring_pwm.freq(50)
middle_pwm.freq(50)
index_pwm.freq(50)
thumb_pwm.freq(50)

def set_pico_angle(pwm_pin, angle):
    min_duty = 1638
    max_duty = 8192
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

# ==========================================
# 3. TEST SEQUENCE
# ==========================================
print("Starting Sequential Finger Test...")

while True:
    # --- PINKY ---
    print("Pinky -> 90")
    pca_servos.position(0, degrees=90)
    time.sleep(1)
    print("Pinky -> 180")
    pca_servos.position(0, degrees=0)
    time.sleep(1)
    
    # --- RING ---
    print("Ring -> 90")
    set_pico_angle(ring_pwm, 90)
    time.sleep(1)
    print("Ring -> 180")
    set_pico_angle(ring_pwm, 0)
    time.sleep(1)
    
    # --- MIDDLE ---
    print("Middle -> 90")
    set_pico_angle(middle_pwm, 90)
    time.sleep(1)
    print("Middle -> 180")
    set_pico_angle(middle_pwm, 180)
    time.sleep(1)
    
    # --- INDEX ---
    print("Index -> 90")
    set_pico_angle(index_pwm, 90)
    time.sleep(1)
    print("Index -> 180")
    set_pico_angle(index_pwm, 180)
    time.sleep(1)
    
    # --- THUMB ---
    print("Thumb -> 90")
    set_pico_angle(thumb_pwm, 90)
    time.sleep(1)
    print("Thumb -> 180")
    set_pico_angle(thumb_pwm, 80)
    time.sleep(1)
    
    print("--- CYCLE COMPLETE ---")
    time.sleep(2)'''
#######################################
'''
from machine import Pin, I2C, PWM
import time
from servo import Servos

# ==========================================
# 1. PCA9685 SETUP (Pinky)
# ==========================================
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
pca_servos = Servos(i2c, min_us=600, max_us=2400, degrees=180)

# ==========================================
# 2. DIRECT PICO PINS (Ring, Middle, Index, Thumb)
# ==========================================
ring_pwm = PWM(Pin(15))   # Ring
middle_pwm = PWM(Pin(16)) # Middle
index_pwm = PWM(Pin(18))  # Index
thumb_pwm = PWM(Pin(20))  # Thumb

ring_pwm.freq(50)
middle_pwm.freq(50)
index_pwm.freq(50)
thumb_pwm.freq(50)

def set_pico_angle(pwm_pin, angle):
    min_duty = 1638
    max_duty = 8192
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

# ==========================================
# 3. TEST SEQUENCE
# ==========================================
print("Starting Simultaneous Finger Test...")

while True:
    print("--- ALL FINGERS -> 90 DEGREES ---")
    pca_servos.position(0, degrees=90) # Pinky   90 - 0
    set_pico_angle(ring_pwm, 90)  # 90 - 180
    set_pico_angle(middle_pwm, 90) # 90 - 180
    set_pico_angle(index_pwm, 90) # 90 - 180
    set_pico_angle(thumb_pwm, 80)
    time.sleep(2)
    
    print("--- ALL FINGERS -> 180 DEGREES ---")
    pca_servos.position(0, degrees=0) #Pinky
    set_pico_angle(ring_pwm, 0)
    set_pico_angle(middle_pwm, 180)
    set_pico_angle(index_pwm, 180)
    set_pico_angle(thumb_pwm, 180)
    
    time.sleep(2)
    '''
    ########################################
'''from machine import Pin, PWM
import time

# ==========================================
# 1. SETUP FINGER PINS
# ==========================================
pinky_pwm  = PWM(Pin(14))
ring_pwm   = PWM(Pin(15))
middle_pwm = PWM(Pin(16))
index_pwm  = PWM(Pin(17))


# Set all to 50Hz


def set_angle(pwm_pin, angle):
    min_duty = 1638
    max_duty = 8192
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

# ==========================================
# 2. TEST SEQUENCE
# ==========================================
print("Starting Finger Test...")

while True:
    # --- RELAXED STATE ---
    print("Moving to RELAXED position (90 degrees)")
    
    set_angle(pinky_pwm, 90)
    
    set_angle(ring_pwm, 90)
    
    set_angle(middle_pwm, 90)
    
    set_angle(index_pwm, 90)
    
    
    time.sleep(2)
    
    # --- CONTRACTED STATE ---
    print("Moving to CONTRACTED position")
    
    ##set_angle(pinky_pwm, 0)    # Pinky goes to 0
    
    ##set_angle(ring_pwm, 90)   # Ring goes to 180
    
   ## set_angle(middle_pwm, 90) # Middle goes to 180
    
    set_angle(index_pwm, 180)  # Index goes to 180
    
    time.sleep(2)'''
##################################################
'''
from machine import Pin, PWM
import time

# Setup
index_pwm  = PWM(Pin(18))
index_pwm.freq(50)

def set_angle(pwm_pin, angle):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

print("Testing Index Finger on GP18...")

while True:
    print("Index -> 90 (Relaxed)")
    set_angle(index_pwm, 90)
    time.sleep(2)
    
    print("Index -> 180 (Contract)")
    set_angle(index_pwm, 90)
    time.sleep(2)
  '''
################################
'''from machine import Pin, PWM
import time

# ==========================================
# 1. SETUP
# ==========================================
middle_pwm = PWM(Pin(16)) # Middle finger
wrist_pwm  = PWM(Pin(18)) # Wrist

middle_pwm.freq(50)
wrist_pwm.freq(50)

def set_angle(pwm_pin, angle):
    min_duty = 1638
    max_duty = 8192
    # Constrain angle to prevent breaking the servo
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm_pin.duty_u16(duty)

print("Testing Middle Finger and Wrist...")

while True:
    # --- RELAXED STATE ---
    print("Middle -> 90 (Relaxed) | Wrist -> 20 (Right)")
    set_angle(middle_pwm, 90)
    ##set_angle(wrist_pwm, 20)
    time.sleep(2)
    
    # --- CONTRACTED STATE ---
    print("Middle -> 180 (Contract) | Wrist -> 140 (Left)")
    set_angle(middle_pwm, 180)
    ##set_angle(wrist_pwm, 140)
    time.sleep(2)'''
######################################
from machine import Pin, PWM
import time

# ==========================================
# 1. SETUP PICO PINS
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

print("Testing Full Hand Simultaneous Movement...")

while True:
    # --- RELAXED STATE ---
    print("Moving ALL to RELAXED position")
    set_angle(pinky_pwm, 90)
    set_angle(ring_pwm, 90)
    set_angle(middle_pwm, 90)
    set_angle(index_pwm, 90)
    ##set_angle(wrist_pwm, 20) # Wrist Right
    time.sleep(2)
    
    # --- CONTRACTED STATE ---
    print("Moving ALL to CONTRACTED position")
    set_angle(pinky_pwm, 0)    # Pinky goes to 0
    set_angle(ring_pwm, 180)   # Ring goes to 180
    set_angle(middle_pwm, 180) # Middle goes to 180
    set_angle(index_pwm, 180)  # Index & Thumb go to 180
    ##set_angle(wrist_pwm, 140)  # Wrist Left
    time.sleep(2)