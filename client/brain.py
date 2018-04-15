# -*- coding: utf-8-*-
import logging
import pkgutil
import os


class brain(object):

    def __init__(self, mic, ENVIRON):
        """
        Instantiates a new Brain object, which cross-references user input with a list of modules.
        Note that the order of brain.modules matters, as the Brain will cease execution on the first module
        that accepts a given input.

        Arguments:
        mic -- used to interact with the user (for both input and output)
        ENVIRON -- info about the current config and robot environment
        """
        self.mic = mic
        self.ENVIRON = ENVIRON
        TOPDIR = ENVIRON["topdir"]
        logLevel = ENVIRON["loglvl"]
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(level=logLevel)
        self.modules = self.get_modules(self._logger, TOPDIR)

    @classmethod
    def get_modules(cls, logger, TOPDIR):
        """
        Dynamically loads all the modules in the modules folder and sorts them by the PRIORITY key.
        If no PRIORITY is defined for a given module, a priority of 0 is assumed.
        """
        location = os.path.join(TOPDIR, "client/modules")
        logger.debug("Looking for modules in: " + location)
        #need a list object for the walk_packages function
        locations = [location]
        modules = []
        for finder, name, ispkg in pkgutil.walk_packages(locations):
            try:
                loader = finder.find_module(name)
                mod = loader.load_module(name)
                modules.append(mod)
            except:
                logger.warning("Skipped module '%s' due to an error.", name, exc_info=True)
            else:
                logger.debug("Found and loaded module '%s' ", name)
        modules.sort(key=lambda mod: mod.PRIORITY if hasattr(mod, 'PRIORITY') else 0, reverse=False)
        return modules


    def query(self, text):
        """
        Passes input text to the appropriate module by testing it against each module's isValid function.
        """
        for module in self.modules:
            if hasattr(module, 'isValid'):
                if module.isValid(text):
                    self._logger.debug("'%s' is a valid phrase for module '%s'", text, module.__name__)

                    try:
                        module.handle(text, self.mic, self.ENVIRON)
                    except Exception:
                        self._logger.error('Failed to execute module',  exc_info=True)
                        self.mic.say("I'm sorry. I had some trouble with that operation. Please try again later.")
                    else:
                        self._logger.debug("Handling of phrase '%s' by module '%s' completed", text,   module.__name__)
                    finally:
                        return
        self._logger.debug("No module was able to handle the phrase: %r", text)
