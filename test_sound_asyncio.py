import os
from utime import sleep
from machine import I2S, Pin
import uasyncio as asyncio
from motor import Motor

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

async def led_task(leds, freq):
    print("In LED task")
    while True:
        for led in leds:
            led.toggle()
        await asyncio.sleep(freq)

async def motor_task(motors, initial_speed):
    print("In motor task")

    for motor in motors:
        motor.enable()

    while True:
        for motor in motors:
            motor.forward(initial_speed)
            await asyncio.sleep(0.2)

async def main(audio_out, wav, leds, motors, initial_speed):
    sound_play = asyncio.create_task(continuous_play(audio_out, wav))
    #led_play = asyncio.create_task(led_task(leds, 0.2))
    motor_play = asyncio.create_task(motor_task(motors, initial_speed))

    # keep the event loop active
    while True:
        await asyncio.sleep_ms(10)

try:
    # Define I2S audio out device
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

    # Define motors
    motorA = Motor(21, 20, 17)
    # motorB = Motor(19, 18, 16)
    motors = [motorA]
    initial_speed = 0.3

    # Define LEDs here
    led_onboard = Pin(25, Pin.OUT)
    leds = [led_onboard]

    # Define two wav clips
    wav_start_up = open("engine_start_up.wav", "rb")
    wav_engine = open("engine_running.wav", "rb")

    # Turn LEDs on
    for led in leds:
        led(1)

    # Turn all motors on
    for motor in motors:
        motor.enable()

    for motor in motors:
        motor.forward(initial_speed)

    # Play initial engine start-up sound
    play_one_off(audio_out, wav_start_up)

    # Play looped engine running sound, flash LEDs and run the motors
    asyncio.run(main(audio_out, wav_engine, leds, motors, initial_speed))

except (KeyboardInterrupt, Exception) as e:
    print("Exception in main {} {}\n".format(type(e).__name__, e))
    
finally:
    # cleanup of audio
    wav_start_up.close()
    wav_engine.close()
    audio_out.deinit()
    
    # cleanup of motors
    for motor in motors:
        motor.stop()
        motor.disable()

    # cleanup of led
    led_onboard(0)
    ret = asyncio.new_event_loop()
    print("Done playback")