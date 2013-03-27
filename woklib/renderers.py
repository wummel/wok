# -*- coding: iso-8859-1 -*-
from __future__ import print_function
from .util import has_module


if not has_module('pygments'):
    print('Pygments not enabled.')

# List of available renderers
all = []

class Renderer(object):
    extensions = []

    @classmethod
    def render(cls, plain):
        return plain
all.append(Renderer)

class Plain(Renderer):
    """Plain text renderer. Replaces new lines with html </br>s"""
    extensions = ['txt']

    @classmethod
    def render(cls, plain):
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
            plugins.append('codehilite(css_class=codehilite)')
            plugins.append('fenced_code')

        @classmethod
        def render(cls, plain):
            return markdown(plain, cls.plugins)

    all.append(Markdown)
else:
    print("markdown isn't available, trying markdown2")
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
                return markdown2.markdown(plain, extras=cls.extras)

        all.append(Markdown2)
    else:
        print('Markdown not enabled.')


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
            w = rst_html_writer()
            return docutils.core.publish_parts(plain, writer=w)['body']

    all.append(ReStructuredText)
else:
    print('reStructuredText not enabled.')


# Try Textile
if has_module('textile'):
    import textile
    class Textile(Renderer):
        """Textile renderer."""
        extensions = ['textile']

        @classmethod
        def render(cls, plain):
            return textile.textile(plain)

    all.append(Textile)
else:
    print('Textile not enabled.')


if len(all) <= 2:
    print("You probably want to install either a Markdown library (one of "
          "'Markdown', or 'markdown2'), 'docutils' (for reStructuredText), or "
          "'textile'. Otherwise only plain text input will be supported.  You "
          "can install any of these with 'sudo pip install PACKAGE'.")
