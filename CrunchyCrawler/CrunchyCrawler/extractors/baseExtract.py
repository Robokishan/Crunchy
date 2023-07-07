from abc import ABC, abstractmethod

'''
    Base Extractor class
'''


class BaseExtract(ABC):
    @abstractmethod
    def getTitle(self):
        pass

    @abstractmethod
    def getValue(self, text):
        pass
