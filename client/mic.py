# -*- coding: utf-8-*-
"""
    The Mic class handles all interactions with the microphone and speaker.
"""
import logging
import tempfile
import wave
import audioop
import pyaudio
import os


# ---------------------------------------------------------------------------------------
# Functions to adjust the text before it is spoken
# ---------------------------------------------------------------------------------------
import re

def detectYears(input):
    YEAR_REGEX = re.compile(r'(\b)(\d\d)([1-9]\d)(\b)')
    return YEAR_REGEX.sub('\g<1>\g<2> \g<3>\g<4>', input)

def clean(input):
    """
        Manually adjust output text before it's translated into speech by the TTS system. 
        This is to fix  idiomatic issues, for example, that 1901 is pronounced "nineteen oh one".
    """
    return detectYears(input)


    
# ---------------------------------------------------------------------------------------
# The Mic class, used to listen and speak
# ---------------------------------------------------------------------------------------
class Mic:

    def __init__(self, speaker, active_stt_engine, ENVIRON):
        """
        Arguments:
        speaker -- handles platform-independent audio output
        acive_stt_engine -- performs STT while in active listen mode
        """
        self.ENVIRON = ENVIRON
        TOPDIR = ENVIRON["topdir"]
        logLevel = ENVIRON["loglvl"]
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(level=logLevel)
        self.speaker = speaker
        self.active_stt_engine = active_stt_engine
        self.beep_hi = os.path.join(TOPDIR, "static/audio/beep_hi.wav")
        self.beep_lo = os.path.join(TOPDIR, "static/audio/beep_lo.wav")


    def getScore(self, data):
        rms = audioop.rms(data, 2)
        #this was the old setting when we took 1 second of sound for THRESHOLD
        #score = rms / 3
        score = rms 
        return score



    # Records until a second of silence or times out after 10 seconds. 
    # Lee added param SEND so we can listen but not send to the STT engine when needed
    #------------------------------------------------------------------------------------------------------------
    def activeListenToAllOptions(self, THRESHOLD=None, LISTEN=True, MUSIC=False, SEND=True):

        _audio = pyaudio.PyAudio()
        self._logger.info("Initialization of PyAudio completed.")

        self._logger.debug("Active listen starting with STT = " + str(SEND))
        RATE = 16000
        CHUNK = 1024
        LISTEN_TIME = 10

        # Set threshold to the current average background noise
        THRESHOLD = self.ENVIRON["avg_noise"] 

        self.speaker.play(self.beep_hi)

        self._logger.debug("Opening pyaudio recording stream")
        # prepare recording stream
        stream = _audio.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

        frames = []

        # waitVal determines the pause before a command is expected. (A value of 10 is around 1 second)
        waitVal = 30
        lastN = [THRESHOLD * waitVal for i in range(waitVal)]

        for i in range(0, int(RATE / CHUNK * LISTEN_TIME)):
            data = stream.read(CHUNK)
            frames.append(data)
            score = self.getScore(data)

            lastN.pop(0)
            lastN.append(score)
            average = sum(lastN) / float(len(lastN))

            #If average sound level is below cutoff then we have silence
            if average < THRESHOLD:
                break

        self.speaker.play(self.beep_lo)

        # save the audio data
        stream.stop_stream()
        stream.close()
        self._logger.debug("Closed pyaudio recording stream")

        #Lee only send to convert STT if we need to
        if SEND == True:
            with tempfile.SpooledTemporaryFile(mode='w+b') as f:
                wav_fp = wave.open(f, 'wb')
                wav_fp.setnchannels(1)
                wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
                wav_fp.setframerate(RATE)
                wav_fp.writeframes(b''.join(frames))
                wav_fp.close()
                f.seek(0)
                self._logger.debug("Calling self.active_stt_engine.transcribe(f)")
                return self.active_stt_engine.transcribe(f)



    def say(self, phrase, OPTIONS=" -vdefault+m3 -p 40 -s 160 --stdout > say.wav"):
        # alter phrase before speaking
        #phrase = alteration.clean(phrase)
        phrase = clean(phrase)
        self.speaker.say(phrase)


    def play(self, filepath):
        self.speaker.play(filepath)


