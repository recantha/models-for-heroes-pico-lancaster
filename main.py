import os
from utime import sleep
from machine import I2S, Pin, PWM
import uasyncio as asyncio
from motor import Motor
import sys

def fade_in(leds):
    print("Initialising LEDs frequencies")
    for led in leds:
        led.freq(1000)

    print("Increasing LED duties")
    for duty in range(0,65535, 100):
        for led in leds:
            led.duty_u16(duty)
            sleep(0.001)

def play_one_off(audio_out, wav):
    wav_samples = bytearray(10000)
    wav_samples_mv = memoryview(wav_samples)

    _ = wav.seek(44)

    running = True

    while running:
        num_read = wav.readinto(wav_samples_mv)

        # end of WAV file?
        if num_read == 0:
            running = False
        else:
            _ = audio_out.write(wav_samples_mv[:num_read])

async def continuous_play(audio_out, wav):
    swriter = asyncio.StreamWriter(audio_out)

    _ = wav.seek(44)  # advance to first byte of Data section in WAV file

    # allocate sample array
    # memoryview used to reduce heap allocation
    wav_samples = bytearray(10000)
    wav_samples_mv = memoryview(wav_samples)

    # continuously read audio samples from the WAV file
    # and write them to an I2S DAC
    print("==========  START PLAYBACK ==========")

    while True:
        num_read = wav.readinto(wav_samples_mv)
        # end of WAV file?
        if num_read == 0:
            # end-of-file, advance to first byte of Data section
            _ = wav.seek(44)
        else:
            # apply temporary workaround to eliminate heap allocation in uasyncio Stream class.
            # workaround can be removed after acceptance of PR:
            #    https://github.com/micropython/micropython/pull/7868
            # swriter.write(wav_samples_mv[:num_read])
            swriter.out_buf = wav_samples_mv[:num_read]
            await swriter.drain()

async def motor_task(motors, initial_speed):
    print("In motor task")

    for motor in motors:
        motor.enable()

    while True:
        for motor in motors:
            motor.forward(initial_speed)
            await asyncio.sleep(0.2)

async def main(audio_out, wav, motors, initial_speed):
    sound_play = asyncio.create_task(continuous_play(audio_out, wav))
    motor_play = asyncio.create_task(motor_task(motors, initial_speed))

    # keep the event loop active
    while True:
        await asyncio.sleep_ms(10)

# For turning off various things, it helps to know whether or not they CAN be turned off,
# so we keep initialisation booleans to help us.
motors_triggered = False
leds_triggered = False
sound_setup = False
sound_triggered = False
async_triggered = False

try:
    # Define I2S audio out device
    print("Setting up audio")
    audio_out = I2S(
        0,
        sck=Pin(27),
        ws=Pin(28),
        sd=Pin(26),
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=8000,
        ibuf=40000
    )

    # Define two wav clips
    print("Opening sound files for later use")
    wav_start_up = open("engine_start_up.wav", "rb")
    wav_engine = open("engine_running.wav", "rb")
    sound_setup = True

    # Define LEDs here
    print("Setting up LEDs")
    led_onboard = Pin(25, Pin.OUT)

    # Effect LEDs
    led_cockpit = Pin(2, Pin.OUT)
    led_cabin_1 = PWM(Pin(6))
    led_cabin_2 = PWM(Pin(10))
    led_cabin_3 = PWM(Pin(14))
    leds_cabin = [led_cabin_1,led_cabin_2,led_cabin_3]

    # First, turn on the cockpit LED then wait half a second then FADE in the cabin LEDs
    print("Cockpit light on")
    led_cockpit(1)
    sleep(1)
    print("Fading in cabin lights")
    fade_in(leds_cabin)

    leds_triggered = True

    # Define motors
    motorA = Motor(21, 20, 17)
    # motorB = Motor(19, 18, 16)
    motors = [motorA]
    initial_speed = 0.3

    # Turn all motors on and run them
    for motor in motors:
        motor.enable()
    for motor in motors:
        motor.forward(initial_speed)

    motors_triggered = True

    # Play initial engine start-up sound
    play_one_off(audio_out, wav_start_up)
    sound_triggered = True

    # Play looped engine running sound, flash LEDs and run the motors
    asyncio.run(main(audio_out, wav_engine, motors, initial_speed))
    async_triggered = True

except (KeyboardInterrupt, Exception) as e:
    print("Exception in main {} {}\n".format(type(e).__name__, e))
    
finally:
    # cleanup of audio
    if sound_triggered:
        print("Closed sound files")
        wav_start_up.close()
        wav_engine.close()
        
    if sound_setup:
        print("De-initialised the I2S")
        audio_out.deinit()
    
    # cleanup of motors
    if motors_triggered:
        print("Stopping and disabling motors")
        for motor in motors:
            motor.stop()
            motor.disable()

    if leds_triggered:
        print("Turning off LEDs")
        # cleanup of led
        led_onboard(0)
        for led in leds_cabin:
            led.duty_u16(0)
        led_cockpit(0)

    # Important to only do this if it's been triggered.
    if async_triggered:
        print("Stopping asyncio")
        ret = asyncio.new_event_loop()

    print("All finished. Exiting.")
