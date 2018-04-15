# -*- coding: utf-8-*-
"""
A Speaker handles audio output to the user.
Internet based TTS modules have been removed for the moment. eSpeak, Flite and Pico options remain.

Speaker methods:
    say - output 'phrase' as speech
    play - play the audio in 'filename'
    is_available - returns True if the platform supports this implementation
"""
#import app_utils
import os
import pkgutil
#import platform
import re
import tempfile
import subprocess
import pipes
import logging
import wave
#import urllib
#import urlparse
#import requests
from abc import ABCMeta, abstractmethod
import argparse
import sys
if sys.version_info < (3, 3):
    from distutils.spawn import find_executable
else:
    from shutil import which as find_executable

try:
    import mad
except ImportError:
    pass


# Helper function to check if an executable exists
#----------------------------------------------------
def check_executable(executable):
    logger = logging.getLogger(__name__)
    logger.debug("Checking executable '%s'...", executable)
    executable_path = find_executable(executable)
    found = executable_path is not None
    if found:
        logger.debug("Executable '%s' found: '%s'", executable, executable_path)
    else:
        logger.debug("Executable '%s' not found", executable)
    return found


# Helper function to check if an python pkg exists
#----------------------------------------------------
def check_python_import(package_or_module):
    logger = logging.getLogger(__name__)
    logger.debug("Checking python import '%s'...", package_or_module)
    loader = pkgutil.get_loader(package_or_module)
    found = loader is not None
    if found:
        logger.debug("Python %s '%s' found: %r",
                     "package" if loader.is_package(package_or_module)
                     else "module", package_or_module, loader.get_filename())
    else:
        logger.debug("Python import '%s' not found", package_or_module)
    return found




class AbstractTTSEngine(object):
    """
    Generic parent class for all speakers
    """
    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        config = cls.get_config()
        instance = cls(**config)
        return instance

    @classmethod
    @abstractmethod
    def is_available(cls):
        return check_executable('aplay')

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def say(self, phrase, *args):
        pass

    def play(self, filename):
        # FIXME: Use platform-independent audio-output here
        cmd = ['aplay', str(filename)]
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                     for arg in cmd]))
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)



class AbstractMp3TTSEngine(AbstractTTSEngine):
    """
    Generic class that implements the 'play' method for mp3 files
    """
    @classmethod
    def is_available(cls):
        return (super(AbstractMp3TTSEngine, cls).is_available() and
                check_python_import('mad'))

    def play_mp3(self, filename):
        mf = mad.MadFile(filename)
        with tempfile.NamedTemporaryFile(suffix='.wav') as f:
            wav = wave.open(f, mode='wb')
            wav.setnchannels(1 if mf.mode() == mad.MODE_SINGLE_CHANNEL else 2)
            wav.setframerate(mf.samplerate())
            # 4L is the sample width of 32 bit audio (for python 3 we no longer need the L)
            #wav.setsampwidth(4L)
            wav.setsampwidth(4)
            frame = mf.read()
            while frame is not None:
                wav.writeframes(frame)
                frame = mf.read()
            wav.close()
            self.play(f.name)



# If no speaker is available then you can set the TTS engine to dummy-tts to output to console
#---------------------------------------------------------------------------------------------
class DummyTTS(AbstractTTSEngine):
    SLUG = "dummy-tts"

    @classmethod
    def is_available(cls):
        return True

    def say(self, phrase):
        self._logger.info(phrase)

    def play(self, filename):
        self._logger.debug("Playback of file '%s' requested")
        pass



# Use the eSpeak synthesizer that comes with Debian - sounds very much like a robot!
#---------------------------------------------------------------------------------------------
class EspeakTTS(AbstractTTSEngine):
    SLUG = "espeak-tts"

    def __init__(self, voice='default+m3', pitch_adjustment=50, words_per_minute=170):
        super(self.__class__, self).__init__()
        self.voice = voice
        self.pitch_adjustment = pitch_adjustment
        self.words_per_minute = words_per_minute

    @classmethod
    def get_config(cls):
        # no config available below chose TTS at the moment
        config = {}
        return config

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                check_executable('espeak'))

    # Lee modified to not use files based on https://github.com/Ghostbird/jasper-client/commit/b1266b5f8b16c243bdda20489cf3736d64cfc598
    def say(self, phrase):
        self._logger.debug("Saying '%s' with '%s'", phrase, self.SLUG)
        #cmd = ['espeak', '-v', self.voice,
        #                 '-p', self.pitch_adjustment,
        #                 '-s', self.words_per_minute,
        #                 phrase, ' --stdout | aplay']
        #cmd = [str(x) for x in cmd]
        #self._logger.debug('Executing %s', ' '.join([pipes.quote(arg) for arg in cmd]))
        #p = subprocess.Popen(cmd)
        #output, error = p.communicate()
        #if output:
        #    self._logger.debug("Output was: '%s'", output)
        #if error:
        #    self._logger.debug("Error was: '%s'", output)

        # Lee espeak stuttering bug has rendered the code above impractical. switching to simple os.system(cmd) as used below
        cmd = "espeak --stdout -p %s -s %s \"%s\" | aplay -q" % (self.pitch_adjustment, self.words_per_minute, phrase)
        os.system(cmd)




# Use the Flite TTS engine. A little too quiet, but more like a human and has different voices
# ---------------------------------------------------------------------------------------------
class FliteTTS(AbstractTTSEngine):
    SLUG = "flite-tts"

    def __init__(self, voice='default+m3', pitch_adjustment=40, words_per_minute=160):
        super(self.__class__, self).__init__()
        self.voice = voice
        self.pitch_adjustment = pitch_adjustment
        self.words_per_minute = words_per_minute

    @classmethod
    def get_config(cls):
        # FIXME: Add other voices as options later
        config = {}
        return config

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                check_executable('flite'))

    # Lee modified to not use files based on https://github.com/Ghostbird/jasper-client/commit/b1266b5f8b16c243bdda20489cf3736d64cfc598
    def say(self, phrase):
        self._logger.debug("Saying '%s' with '%s'", phrase, self.SLUG)
        cmd = ['flite', '-voice', 'awb',
               '-t', phrase]
        cmd = [str(x) for x in cmd]
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                     for arg in cmd]))
        p = subprocess.Popen(cmd)
        output, error = p.communicate()
        if output:
            self._logger.debug("Output was: '%s'", output)
        if error:
            self._logger.debug("Error was: '%s'", output)



# Use the Pico TTS engine. Much more human like but uses a female voice. Multi-Lang available
#---------------------------------------------------------------------------------------------
class PicoTTS(AbstractTTSEngine):
    SLUG = "pico-tts"

    def __init__(self, language="en-US"):
        super(self.__class__, self).__init__()
        self.language = language

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                check_executable('pico2wave'))

    @classmethod
    def get_config(cls):
        # no config below chosen TTS at this stage
        config = {}
        return config

    @property
    def languages(self):
        cmd = ['pico2wave', '-l', 'NULL',
                            '-w', os.devnull,
                            'NULL']
        with tempfile.SpooledTemporaryFile() as f:
            subprocess.call(cmd, stderr=f)
            f.seek(0)
            output = f.read()
        pattern = re.compile(r'Unknown language: NULL\nValid languages:\n' +
                             r'((?:[a-z]{2}-[A-Z]{2}\n)+)')
        matchobj = pattern.match(output)
        if not matchobj:
            raise RuntimeError("pico2wave: valid languages not detected")
        langs = matchobj.group(1).split()
        return langs

    def say(self, phrase):
        #Pico speaks sentence case better than capitals
        phrase = phrase.capitalize()
        self._logger.debug("Saying '%s' with '%s'", phrase, self.SLUG)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            fname = f.name
        cmd = ['pico2wave', '--wave', fname]
        #if self.language not in self.languages:
        #        raise ValueError("Language '%s' not supported by '%s'", self.language, self.SLUG)
        cmd.extend(['-l', self.language])
        cmd.append(phrase)
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                     for arg in cmd]))
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)
        self.play(fname)
        os.remove(fname)




# Return eSpeak as the default if nothing is configured (should this be the dummy one?)
#-------------------------------------------------------------------------------
def get_default_engine_slug():
    return 'espeak-tts'


# A speaker implementation available on the current platform based on the config
#-------------------------------------------------------------------------------
def get_engine_by_slug(slug=None):
    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_engines = filter(lambda engine: hasattr(engine, "SLUG") and engine.SLUG == slug, get_engines())
    selected_engines = list(selected_engines)
    if len(selected_engines) == 0:
        raise ValueError("No TTS engine found for slug '%s'" % slug)
    else:
        if len(selected_engines) > 1:
            print("WARNING: Multiple TTS engines found for slug '%s'. This is most certainly a bug." % slug)
        engine = selected_engines[0]
        if not engine.is_available():
            raise ValueError(("TTS engine '%s' is not available (due to missing dependencies, etc.)") % slug)
        return engine


# Return list of available engines
#-------------------------------------------------------------------------------
def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses
    return [tts_engine for tts_engine in list(get_subclasses(AbstractTTSEngine))
            if hasattr(tts_engine, 'SLUG') and tts_engine.SLUG]



# Testing script
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RobotAI TTS module')
    parser.add_argument('--debug', action='store_true', help='Show debug messages')
    args = parser.parse_args()

    logging.basicConfig()
    if args.debug:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

    engines = get_engines()
    available_engines = []
    for engine in get_engines():
        if engine.is_available():
            available_engines.append(engine)
    disabled_engines = list(set(engines).difference(set(available_engines)))
    
    print("Available TTS engines:")
    for i, engine in enumerate(available_engines, start=1):
        print("%d. %s" % (i, engine.SLUG))

    print("Disabled TTS engines:")
    for i, engine in enumerate(disabled_engines, start=1):
        print("%d. %s" % (i, engine.SLUG))

    print("Testing each engine:")
    for i, engine in enumerate(available_engines, start=1):
        print("%d. Testing engine '%s'..." % (i, engine.SLUG))
        engine.get_instance().say("This is a test.")
    print("Done.")
