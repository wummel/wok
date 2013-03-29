# -*- coding: iso-8859-1 -*-
from unittest import TestCase

from woklib.util import get_rooturl

class TestRooturl(TestCase):

    def test_absolute(self):
        url = '/'
        self.assertEqual(get_rooturl(url), '.')
        url = '/a/'
        self.assertEqual(get_rooturl(url), '..')
        url = '/a/b.html'
        self.assertEqual(get_rooturl(url), '..')
        url = '/a/b/'
        self.assertEqual(get_rooturl(url), '../..')

    def test_relative(self):
        url = 'a.html'
        self.assertEqual(get_rooturl(url), '.')
        url = 'a/'
        self.assertEqual(get_rooturl(url), '..')
        url = 'a/a.html'
        self.assertEqual(get_rooturl(url), '..')
        url = 'a/b/'
        self.assertEqual(get_rooturl(url), '../..')
        url = 'a/b/c.html'
        self.assertEqual(get_rooturl(url), '../..')
