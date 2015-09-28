import sys
import os
from unittest import TestCase
from . import wok_cmd, run_checked


def run_with_options(options, cmd=wok_cmd):
    """Run dosage with given options."""
    run_checked([sys.executable, cmd] + options)


class TestWok(TestCase):
    """Test the wok commandline client."""

    def test_wok(self):
        # display version
        run_with_options(["--version"])
        # display help
        for option in ("-h", "--help"):
            run_with_options([option])
        # unknown option
        self.assertRaises(OSError, run_with_options, ['--imadoofus'])
        # create test site
        os.chdir("test_site")
        try:
            run_with_options(["-v"])
        finally:
            os.chdir("..")
        # create documentation
        os.chdir("docs")
        try:
            run_with_options(["-v"])
        finally:
            os.chdir("..")
