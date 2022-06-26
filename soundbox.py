# The MIT License (MIT)
# Copyright (c) 2022 Mike Teachman
# https://opensource.org/licenses/MIT

# Purpose:  Play a WAV audio file out of a speaker or headphones
#
# - read audio samples from a WAV file stored on internal flash memory
# - write audio samples to an I2S amplifier or DAC module
# - the WAV file will play continuously in a loop until
#   a keyboard interrupt is detected or the board is reset
#
# Blocking version
# - the write() method blocks until the entire sample buffer is written to I2S
#
# Use a tool such as rshell or ampy to copy the WAV file "side-to-side-8k-16bits-stereo.wav"
# to internal flash memory

import os
from machine import I2S, Pin
import micropython
from utime import sleep

class SoundBox:
    def __init__(self,
                 i2s_id, sck_pin_no, ws_pin_no, sd_pin_no,
                 sample_size_in_bits, sample_format, sample_rate_in_hz, buffer_length,
                 filename
    ):
        self.PLAY = 0
        self.PAUSE = 1
        self.RESUME = 2
        self.STOP = 3

        self.audio_out = I2S(
            i2s_id,
            sck=Pin(sck_pin_no),
            ws=Pin(ws_pin_no),
            sd=Pin(sd_pin_no),
            mode=I2S.TX,
            bits=sample_size_in_bits,
            format=sample_format,
            rate=sample_rate_in_hz,
            ibuf=buffer_length,
        )
        self.audio_out.irq(self.i2s_callback)
        self.state = self.PAUSE

        self.wav_samples = bytearray(1000)
        self.wav_samples_mv = memoryview(self.wav_samples)

        self.wav = open(filename, "rb")
        _ = self.wav.seek(44)

        self.silence = bytearray(1000)
        
        _ = self.audio_out.write(self.silence)

    def i2s_callback(self, arg):
        print("i2s_callback ".self.state)
        if self.state == self.PLAY:
            num_read = self.wav.readinto(self.wav_samples_mv)

            # end of WAV file?
            if num_read == 0:
                pos = self.wav.seek(44)
                micropython.schedule(eof_callback, None)
            else:
                _ = self.audio_out.write(self.wav_samples_mv[:num_read])
                
        elif self.state == self.RESUME:
            self.state = self.PLAY
            _ = self.audio_out.write(self.silence)

        elif self.state == self.PAUSE:
            _ = self.audio_out.write(self.silence)
            
        elif self.state == self.STOP:
            # cleanup
            self.wav.close()
            self.audio_out.deinit()
            print("Audio stopped!")
            
        else:
            print(self.state + " is not a valid state. State ignored")

    def eof_callback(self, arg):
        print("End of audio file")
        self.state = self.STOP

state = 0
soundbox = SoundBox(0, 27, 28, 26, 16, I2S.STEREO, 8000, 5000, "engine_running.wav")
sleep(5)
