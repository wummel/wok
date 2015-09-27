# -*- coding: iso-8859-1 -*-
import os
import sys
import shutil
import fnmatch
from datetime import datetime
import logging

from . import renderers, util
from .page import Page, Author
from .dev_server import DevServer
from .yamlutil import load_file, write_file


class Engine(object):
    """
    The main engine of wok. Upon initialization, it generates a site from the
    source files.
    """
    default_options = {
        'content_dir': 'content',
        'template_dir': 'templates',
        'output_dir': 'output',
        'output_exclude': [],
        'media_dir': 'media',
        'site_title': 'Some random Wok site',
        'url_pattern': '/{category}/{slug}{page}.{ext}',
        'url_include_index': True,
        'slug_from_filename': False,
        'relative_urls': False,
        'markdown_extra_plugins': [],
    }

    def __init__(self, site_root=None, config='wokconfig'):
        """Setup the site root and config filename."""
        if site_root is None:
            self.site_root = os.getcwd()
        else:
            self.site_root = site_root
        self.config = config

    def run(self, server=None, init_site_title=None):
        """Generate site or run dev server."""
        orig_dir = os.getcwd()
        try:
            os.chdir(self.site_root)
            if init_site_title:
                self.init_site(init_site_title)
            self.read_options()
            self.sanity_check()
            if server:
               self.start_server(server)
            else:
               self.generate_site()
        finally:
            os.chdir(orig_dir)

    def init_site(self, site_title):
        ''' Create the config file and the required directories.'''
        # check if config is already present
        if os.path.isfile(self.config):
            logging.warn("Config file %r found; site is already initialized." % self.config)
            return

        # create config
        options = self.default_options.copy()
        options['site_title'] = site_title
        write_file(self.config, options)

        # create required dirs
        required_dirs = [options['content_dir'], options['template_dir']]
        for required_dir in required_dirs:
            if not os.path.isdir(required_dir):
                os.mkdir(required_dir)

    def start_server(self, hostport):
        ''' Run the dev server if the user said to, and watch the specified
        directories for changes. The server will regenerate the entire wok
        site if changes are found after every request.
        '''
        if ':' in hostport:
            host, port = hostport.split(':', 1)
            port = int(port)
        else:
            host = hostport
            port = 8000
        server = DevServer(serv_dir=self.options['output_dir'], host=host, port=port,
            dir_mon=True,
            watch_dirs=[
                self.options['media_dir'],
                self.options['template_dir'],
                self.options['content_dir']
            ],
            change_handler=self.generate_site)
        server.run()

    def generate_site(self):
        """Generate the wok site"""
        self.all_pages = []
        self.load_hooks()
        self.load_renderers()
        self.renderer_options()

        self.run_hook('site.start')
        self.prepare_output()
        self.load_pages()
        self.make_tree()
        self.render_site()
        self.run_hook('site.done')

    def read_options(self):
        """Load options from the config file."""
        self.options = Engine.default_options.copy()
        self.options.update(load_file(self.config))

        # Make authors a list, even when only a single author was specified.
        authors = self.options.get('authors', self.options.get('author', None))
        if isinstance(authors, list):
            self.options['authors'] = [Author.parse(a) for a in authors]
        elif isinstance(authors, str):
            csv = authors.split(',')
            self.options['authors'] = [Author.parse(a) for a in csv]
            if len(self.options['authors']) > 1:
                logging.warning('Deprecation Warning: Use YAML lists instead of '
                        'CSV for multiple authors. i.e. ["John Doe", "Jane '
                        'Smith"] instead of "John Doe, Jane Smith". In config '
                        'file.')

        if '{type}' in self.options['url_pattern']:
            logging.warning('Deprecation Warning: You should use {ext} instead '
                    'of {type} in the url pattern specified in the config '
                    'file.')

        # expand user for directories
        for name in ('template_dir', 'content_dir', 'output_dir', 'media_dir'):
            if name in self.options:
                self.options[name] = os.path.expanduser(self.options[name])

    def renderer_options(self):
        """Add extra plugins in markdown renderers from config file."""
        markdown_extra_plugins = self.options.get('markdown_extra_plugins', [])
        if markdown_extra_plugins:
            if hasattr(renderers, 'Markdown'):
                renderers.Markdown.plugins.extend(markdown_extra_plugins)
                logging.debug('Activated extra Markdown plugins %s' % markdown_extra_plugins)
            elif hasattr(renderers, 'Markdown2'):
                renderers.Markdown2.plugins.extend(markdown_extra_plugins)
                logging.debug('Activated extra Markdown2 plugins %s' % markdown_extra_plugins)
            else:
                logging.warning('Extra markdown plugins %s but no Markdown or Markdown2 renderer found.' % markdown_extra_plugins)

    def sanity_check(self):
        """Basic sanity checks."""
        # Make sure that this is (probabably) a wok source directory.
        for name in ('template_dir', 'content_dir'):
            if not os.path.isdir(self.options[name]):
                logging.critical("%s %r not found at %s, aborting" % (name, self.options[name], self.site_root))
                sys.exit(1)
        # always exclude dotfiles
        self.options['output_exclude'].append(".*")
        logging.debug("Using options %s" % self.options)

    def load_hooks(self):
        """Load site hooks."""
        try:
            sys.path.append('hooks')
            import __hooks__
            self.hooks = __hooks__.hooks
            logging.debug('Loaded {0} hooks: {0}'.format(self.hooks))
        except ImportError as e:
            if "__hooks__" in str(e):
                logging.debug('No hooks module found.')
            else:
                # don't catch import errors raised within a hook
                logging.info('Import error within hooks.')
                raise

    def load_renderers(self):
        self.renderers = {}
        for renderer in renderers.all:
            self.renderers.update((ext, renderer) for ext in renderer.extensions)

        try:
            sys.path.append('renderers')
            import __renderers__
            self.renderers.update(__renderers__.renderers)
            logging.info('Loaded {0} renderers'.format(len(__renderers__.renderers)))
        except ImportError as e:
            if "__renderers__" in str(e):
                logging.info('No renderers module found.')
            else:
                # don't catch import errors raised within a renderer
                logging.info('Import error within renderers.')
                raise

    def run_hook(self, hook_name, *args):
        """ Run specified hook functions if they exist """
        funcs = self.hooks.get(hook_name, [])
        logging.debug('Running hook {0} with {1} functions'.format(hook_name, len(funcs)))
        return [hook(self.options, *args) for hook in funcs]

    def exclude_output(self, filename):
        """Determine if output filename should be excluded."""
        if filename.startswith("."):
            # exclude dotfiles per default
            return True
        return any(fnmatch.fnmatch(filename, pattern)
            for pattern in self.options['output_exclude'])

    def prepare_output(self):
        """
        Prepare the output directory. Remove any contents there already, and
        then copy over the media files, if they exist.
        """
        output = self.options['output_dir']
        self.clean_output(output)
        self.run_hook('site.output.pre', output)
        self.copy_media(output)
        self.run_hook('site.output.post', output)

    def clean_output(self, output):
        """Remove files in output directory."""
        if util.is_sane_outdir(output, self.site_root):
            for name in os.listdir(output):
                if self.exclude_output(name):
                    continue
                path = os.path.join(output, name)
                if os.path.isfile(path):
                    os.unlink(path)
                else:
                    shutil.rmtree(path)
        else:
            os.makedirs(output)

    def copy_media(self, output):
        """Copy the media directory to the output folder"""
        media_dir = self.options['media_dir']
        if not os.path.isdir(media_dir):
            # no media directory found
            return
        logging.info("Copying media files.")
        for name in os.listdir(media_dir):
            path = os.path.join(media_dir, name)
            if os.path.isdir(path):
                shutil.copytree(
                        path,
                        os.path.join(output, name),
                        symlinks=True
                )
            else:
                shutil.copy(path, output)

    def load_pages(self):
        """Load all the content files."""
        # Load pages from hooks (pre)
        for pages in self.run_hook('site.content.gather.pre'):
            if pages:
                self.all_pages.extend(pages)

        # Load files
        for root, dirs, files in os.walk(self.options['content_dir']):
            # Grab all the parsable files
            for f in files:
                # Don't parse hidden files.
                if f.startswith('.'):
                    continue

                ext = f.split('.')[-1]
                renderer = self.renderers.get(ext)

                if renderer is None:
                    logging.warning('No parser found '
                            'for {0}. Using default renderer.'.format(f))
                    renderer = renderers.Renderer

                p = Page.from_file(os.path.join(root, f), self.options, self, renderer)
                if p and p.meta['published']:
                    self.all_pages.append(p)

        # Load pages from hooks (post)
        for pages in self.run_hook('site.content.gather.post', self.all_pages):
            if pages:
                self.all_pages.extend(pages)

    def make_tree(self):
        """
        Make the category pseudo-tree.

        In this structure, each node is a page. Pages with sub pages are
        interior nodes, and leaf nodes have no sub pages. It is not truly a
        tree, because the root node doesn't exist.
        """
        self.categories = {}
        site_tree = []
        # We want to parse these in a approximately breadth first order
        self.all_pages.sort(key=lambda p: len(p.meta['category']))

        # For every page
        for p in self.all_pages:
            # If it has a category (ie: is not at top level)
            if len(p.meta['category']) > 0:
                top_cat = p.meta['category'][0]
                if not top_cat in self.categories:
                    self.categories[top_cat] = []

                self.categories[top_cat].append(p.meta)

            try:
                # Put this page's meta in the right place in site_tree.
                siblings = site_tree
                for cat in p.meta['category']:
                    # This line will fail if the page is an orphan
                    parent = [subpage for subpage in siblings
                                 if subpage['slug'] == cat][0]
                    siblings = parent['subpages']
                siblings.append(p.meta)
            except IndexError:
                logging.error('It looks like the page "{0}" is an orphan! '
                        'This will probably cause problems.'.format(p.path))

    def render_site(self):
        """Render every page and write the output files."""
        # Gather tags
        tag_set = set()
        for p in self.all_pages:
            tag_set = tag_set.union(p.meta['tags'])
        tag_dict = dict()
        for tag in tag_set:
            # Add all pages with the current tag to the tag dict
            tag_dict[tag] = [p.meta for p in self.all_pages
                                if tag in p.meta['tags']]

        # Gather slugs
        slug_dict = dict((p.meta['slug'], p.meta) for p in self.all_pages)

        for p in self.all_pages:
            # Construct this every time, to avoid sharing one instance
            # between page objects.
            templ_vars = {
                'site': {
                    'title': self.options.get('site_title', 'Untitled'),
                    'datetime': datetime.now(),
                    'date': datetime.now().date(),
                    'time': datetime.now().time(),
                    'tags': tag_dict,
                    'pages': self.all_pages[:],
                    'categories': self.categories,
                    'slugs': slug_dict,
                },
            }

            for k, v in self.options.items():
                if k not in ('site_title', 'output_dir', 'content_dir',
                        'templates_dir', 'media_dir', 'url_pattern'):

                    templ_vars['site'][k] = v

            if 'author' in self.options:
                templ_vars['site']['author'] = self.options['author']

            # Rendering the page might give us back more pages to render.
            new_pages = p.render(templ_vars)

            if p.meta['make_file']:
                p.write()

            if new_pages:
                logging.debug('found new_pages')
                # XXX find a better way to do this
                self.all_pages += new_pages

if __name__ == '__main__':
    Engine()
    exit(0)
