import os
import time
import micropython
from machine import I2S
from machine import Pin

PLAY = 0
PAUSE = 1
RESUME = 2
STOP = 3

def eof_callback(arg):
    global state
    print("end of audio file")
    # state = STOP  # uncomment to stop looping playback

def i2s_callback(arg):
    global state
    if state == PLAY:
        num_read = wav.readinto(wav_samples_mv)
        # end of WAV file?
        if num_read == 0:
            # end-of-file, advance to first byte of Data section
            pos = wav.seek(44)
            _ = audio_out.write(silence)
            micropython.schedule(eof_callback, None)
        else:
            _ = audio_out.write(wav_samples_mv[:num_read])
    elif state == RESUME:
        state = PLAY
        _ = audio_out.write(silence)
    elif state == PAUSE:
        _ = audio_out.write(silence)
    elif state == STOP:
        # cleanup
        wav.close()
        audio_out.deinit()
        print("Done")
    else:
        print("Not a valid state.  State ignored")


audio_out = I2S(
    0,
    sck=Pin(27),
    ws=Pin(28),
    sd=Pin(26),
    mode=I2S.TX,
    bits=16,
    format=I2S.STEREO,
    rate=8000,
    ibuf=5000
)

audio_out.irq(i2s_callback)
state = PAUSE

wav = open("engine_running.wav", "rb")
_ = wav.seek(44)  # advance to first byte of Data section in WAV file

# allocate a small array of blank samples
silence = bytearray(1000)

# allocate sample array buffer
wav_samples = bytearray(10000)
wav_samples_mv = memoryview(wav_samples)

_ = audio_out.write(silence)

# add runtime code here ....
# changing 'state' will affect playback of audio file

print("starting playback for 10s")
state = PLAY
time.sleep(10)
print("pausing playback for 10s")
state = PAUSE
time.sleep(10)
print("resuming playback for 15s")
state = RESUME
time.sleep(15)
print("stopping playback")
state = STOP