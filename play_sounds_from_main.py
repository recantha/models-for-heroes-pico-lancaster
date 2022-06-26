
'''
def play_sounds():
    global running
    while running:
        try:
            soundbox = SoundBox(0, 27, 28, 26, 16, I2S.STEREO, 8000, 5000)
            soundbox.play("engine_start_up.wav")
            soundbox.finish()

            # Reinitialise
            soundbox = SoundBox(0, 27, 28, 26, 16, I2S.STEREO, 8000, 5000)
            while True:
                soundbox.play("engine_running.wav")

        except (KeyboardInterrupt, Exception) as e:
            print("Caught exception in play_sounds() {} {}".format(type(e).__name__, e))
            soundbox.finish()
            running = False
            _thread.exit()
'''
