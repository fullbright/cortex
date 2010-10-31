from app import latinToAscii
from app.config.cplog import CPLog
from string import ascii_letters, digits
from urllib2 import URLError
import cherrypy
import math
import re
import time
import unicodedata
import urllib2
import xml.etree.ElementTree as XMLTree

log = CPLog(__name__)

class rss:

    timeout = 10

    lastUse = 0
    timeBetween = 1

    available = True
    availableCheck = 0

    def toSaveString(self, string):
        string = latinToAscii(string)
        string = ''.join((c for c in unicodedata.normalize('NFD', unicode(string)) if unicodedata.category(c) != 'Mn'))
        safe_chars = ascii_letters + digits + '_ -.,\':!?'
        r = ''.join([char if char in safe_chars else ' ' for char in string])
        return re.sub('\s+' , ' ', r)

    def toSearchString(self, string):
        string = latinToAscii(string)
        string = ''.join((c for c in unicodedata.normalize('NFD', unicode(string)) if unicodedata.category(c) != 'Mn'))
        safe_chars = ascii_letters + digits + ' \''
        r = ''.join([char if char in safe_chars else ' ' for char in string])
        return re.sub('\s+' , ' ', r).replace('\'s', 's').replace('\'', ' ')

    def simplifyString(self, original):
        split = re.split('\W+', original.lower())
        return ' '.join(split)

    def gettextelements(self, xml, path):
        ''' Find elements and return tree'''

        textelements = []
        try:
            elements = xml.findall(path)
        except:
            return
        for element in elements:
            textelements.append(element.text)
        return textelements

    def gettextelement(self, xml, path):
        ''' Find element and return text'''

        try:
            return xml.find(path).text
        except:
            return

    def getItems(self, data, path = 'channel/item'):
        try:
            return XMLTree.parse(data).findall(path)
        except Exception, e:
            log.error('Error parsing RSS. %s' % e)
            return []

    def wait(self):
        now = time.time()
        wait = math.ceil(self.lastUse - now + self.timeBetween)
        if wait > 0:
            log.debug('Waiting for %s, %d seconds' % (self.name, wait))
            time.sleep(self.lastUse - now + self.timeBetween)

    def isAvailable(self, testUrl):

        if cherrypy.config.get('debug'): return True

        now = time.time()

        if self.availableCheck < now - 900:
            self.availableCheck = now
            try:
                self.urlopen(testUrl, 30)
                self.available = True
            except (IOError, URLError):
                log.error('%s unavailable, trying again in an 15 minutes.' % self.name)
                self.available = False

        return self.available

    def urlopen(self, url, timeout = 10):

        self.wait()
        data = urllib2.urlopen(url, timeout = timeout)
        self.lastUse = time.time()

        return data

    def correctName(self, checkName, movieName):

        checkWords = re.split('\W+', self.toSearchString(checkName).lower())
        movieWords = re.split('\W+', self.toSearchString(movieName).lower())

        found = 0
        for word in movieWords:
            if word in checkWords:
                found += 1

        return found == len(movieWords)

    class feedItem(dict):
        ''' NZB item '''

        def __getattr__(self, attr):
            return self.get(attr, None)

        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__
