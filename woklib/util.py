import re
import os
from unicodedata import normalize
from datetime import date, time, datetime
import importlib


def has_module (name):
    """Test if given module can be imported."""
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def is_sane_outdir(dirname, site_root):
    """Check if a directory can be used as output dir."""
    if not os.path.isdir(dirname):
        return False
    # since all content will be removed in the output dir,
    # add some extrac precautions
    d = os.path.realpath(os.path.abspath(dirname))
    s = os.path.realpath(os.path.abspath(site_root))
    if d in s:
        # if d is a substring of s, we would remove the site root
        # except if it starts with a dot
        rest = s[len(d):]
        if not rest.startswith('.'):
            return False
    return True


# From http://flask.pocoo.org/snippets/5/
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text, delim=u'-'):
    """
    Generates a slug that will only use ASCII, be all lowercase, have no
    spaces, and otherwise be nice for filenames, identifiers, and urls.
    """
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', unicode(word)).encode('ascii', 'ignore')
        if word:
            result.append(word)

    result = delim.join(result)
    if result[0] == '-':
        result = result[1:]
    if result[-1] == '-':
        result = result[:-1]

    return unicode(result)


def chunk(li, n):
    """Yield succesive n-size chunks from l."""
    for i in xrange(0, len(li), n):
        yield li[i:i+n]

def date_and_times(meta):

    date_part = None
    time_part = None

    if 'date' in meta:
        date_part = meta['date']

    if 'time' in meta:
        time_part = meta['time']

    if 'datetime' in meta:
        if date_part is None:
            if isinstance(meta['datetime'], datetime):
                date_part = meta['datetime'].date()
            elif isinstance(meta['datetime'], date):
                date_part = meta['datetime']

        if time_part is None and isinstance(meta['datetime'], datetime):
            time_part = meta['datetime'].time()

    if isinstance(time_part, int):
        seconds = time_part % 60
        minutes = (time_part / 60) % 60
        hours = (time_part / 3600)

        time_part = time(hours, minutes, seconds)

    meta['date'] = date_part
    meta['time'] = time_part

    if date_part is not None and time_part is not None:
        meta['datetime'] = datetime(date_part.year, date_part.month,
                date_part.day, time_part.hour, time_part.minute,
                time_part.second, time_part.microsecond, time_part.tzinfo)
    elif date_part is not None:
        meta['datetime'] = datetime(date_part.year, date_part.month, date_part.day)
    else:
        meta['datetime'] = None
