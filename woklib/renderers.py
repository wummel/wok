# -*- coding: iso-8859-1 -*-
from __future__ import print_function
import logging
from .util import has_module

if not has_module('pygments'):
    logging.warn('Pygments not enabled.')

# List of available renderers
all = []

class Renderer(object):
    """Base renderer class."""
    extensions = []

    @classmethod
    def render(cls, plain):
        """Render text."""
        return plain
all.append(Renderer)

class Plain(Renderer):
    """Plain text renderer. Replaces new lines with html </br>s"""
    extensions = ['txt']

    @classmethod
    def render(cls, plain):
        """Render plain text."""
        return plain.replace('\n', '<br>')
all.append(Plain)

# Include markdown, if it is available.
if has_module('markdown'):
    from markdown import markdown
    class Markdown(Renderer):
        """Markdown renderer."""
        extensions = ['markdown', 'mkd', 'md']

        plugins = ['def_list', 'footnotes']
        if has_module('pygments'):
            plugins.extend(['codehilite(css_class=codehilite)', 'fenced_code'])

        @classmethod
        def render(cls, plain):
            """Render markdown text."""
            return markdown(plain, cls.plugins)

    all.append(Markdown)
else:
    logging.warn("markdown isn't available, trying markdown2")
    # Try Markdown2
    if has_module('markdown2'):
        import markdown2
        class Markdown2(Renderer):
            """Markdown2 renderer."""
            extensions = ['markdown', 'mkd', 'md']

            extras = ['def_list', 'footnotes']
            if has_module('pygments'):
                extras.append('fenced-code-blocks')

            @classmethod
            def render(cls, plain):
                """Render markdown text."""
                return markdown2.markdown(plain, extras=cls.extras)

        all.append(Markdown2)
    else:
        logging.warn('Markdown not enabled.')


# Include ReStructuredText Parser, if we have docutils
if has_module('docutils'):
    import docutils.core
    from docutils.writers.html4css1 import Writer as rst_html_writer
    from docutils.parsers.rst import directives

    if has_module('pygments'):
        from .rst_pygments import Pygments as RST_Pygments
        directives.register_directive('Pygments', RST_Pygments)

    class ReStructuredText(Renderer):
        """reStructuredText renderer."""
        extensions = ['rst']

        @classmethod
        def render(cls, plain):
            """Render reStructuredText text."""
            w = rst_html_writer()
            return docutils.core.publish_parts(plain, writer=w)['body']

    all.append(ReStructuredText)
else:
    logging.warn('reStructuredText not enabled.')


# Try Textile
if has_module('textile'):
    import textile
    class Textile(Renderer):
        """Textile renderer."""
        extensions = ['textile']

        @classmethod
        def render(cls, plain):
            """Render textile text."""
            return textile.textile(plain)

    all.append(Textile)
else:
    logging.warn('Textile not enabled.')


if len(all) <= 2:
    logging.error("You probably want to install either a Markdown library (one of "
          "'Markdown', or 'markdown2'), 'docutils' (for reStructuredText), or "
          "'textile'. Otherwise only plain text input will be supported.  You "
          "can install any of these with 'sudo pip install PACKAGE'.")
