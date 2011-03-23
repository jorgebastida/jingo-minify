# -*- coding: utf-8 -*-
from jinja2 import nodes
from jinja2.ext import Extension
from jinja2 import Markup

from django.conf import settings

class JSCSSTagBase(Extension):
    """ Base class used for JS and CSS tags"""
    
    def parse(self, parser):
        stream = parser.stream
        
        tag = stream.next()
        
        # get view name
        if stream.current.test('string'):
            bundle_name = parser.parse_primary()
        else:
            bundle_name = parser.parse_expression()
            
        # get arguments
        args = []
        kwargs = []
        while not stream.current.test_any('block_end', 'name:as'):
            if args or kwargs:
                stream.expect('comma')
            if stream.current.test('name') and stream.look().test('assign'):
                key = nodes.Const(stream.next().value)
                stream.skip()
                value = parser.parse_expression()
                kwargs.append(nodes.Pair(key, value, lineno=key.lineno))
            else:
                args.append(parser.parse_expression())
        
        make_call_node = lambda *kw: \
            self.call_method('_build_tag',
                             args=[bundle_name,
                             nodes.List(args), nodes.Dict(kwargs)],
                             kwargs=kw)
                             
        # if an as-clause is specified, write the result to context...
        if stream.next_if('name:as'):
            var = nodes.Name(stream.expect('name').value, 'store')
            call_node = make_call_node(nodes.Keyword('fail', nodes.Const(False)))
            return nodes.Assign(var, call_node)
        # ...otherwise print it out.
        else:
            return nodes.Output([make_call_node()]).set_lineno(tag.lineno)
    
    @classmethod
    def _build_tag(cls, bundle_name, args, kwargs, fail=True):
        """
        If we are in debug mode, just output a single script tag for each file.
        If we are not in debug mode, return a script that points at bundle-min.
        """
        media_type = cls.media_type
        if settings.TEMPLATE_DEBUG:
            items = settings.MINIFY_BUNDLES[media_type].get(bundle_name, [])
        else:
            bundle_map = settings.MINIFY_BUNDLES_MAP.get(media_type, {})
            
            bundle = bundle_map.get(bundle_name, None)
            
            name_split = bundle['compressed'].split('.')
            file_name, ext = '.'.join(name_split[:-1]), name_split[-1:][0]
            items = ('%s/%s.%s.%s' % (media_type, file_name, bundle['hash'], ext),)
        
        items = items or []
        
        if media_type == 'js':
            wrapper = cls.wrapper
        else:
            wrapper = (cls.wrapper % kwargs.get('media', 'all'))
        
        return Markup("\n".join((wrapper % (settings.MEDIA_URL + item)
                            for item in items)))


class JS(JSCSSTagBase):
    """
        For outputting JS bundles
        
        {% js "bundle_name" debug=False %}
        
    """
    
    tags = set(['js'])
    media_type = 'js'
    wrapper = """<script src="%s"></script>"""


class CSS(JSCSSTagBase):
    """
        For outputting CSS bundles
        
        {% css "bundle_name" media="all",debug=False %}
        
    """
    
    tags = set(['css'])
    media_type = 'css'
    wrapper = """<link rel="stylesheet" media="%s" href="%%s" />"""