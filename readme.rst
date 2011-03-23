====================
Django-Jinja2-Minify
====================

:Info: A Django jinja2 based JS and CSS minification app. Adapted from: jingo-minify_

Introduction
=============

Django-Jinja2-Minify is a *simple* wrapper for YUI_Compressor_ which allows you
to compress your JS and CSS with a Django_ management command `compress_assets`.

Heres what happens:

1. `MINIFY_BUNDLES` is iterated.
2. `MINIFY_NAMESPACE` (optional setting) is used as the relative directory to store the assets.
3. `MINIFY_BUNDLES_MAP` is created mapping the bundle names to the files and there versions.
4. `MINIFY_YAML_FILE` is written to with the stored versions and names.

Warning
=======

If you use relative paths for css images - this will not handle rewriting them.
Either use full paths and manually version if required (see nginx section below)
or provide a patch to rewrite the css image locations to include a hash in the 
filename.

Configuration
=============

Assuming you've got Django_ installed and your using Jinja2_ 
(Read more on: Django_Jinja2_integration_) then all you need to configure
the creation of assets eg:

`MINIFY_BUNDLES` in `settings.py` eg::

    MINIFY_BUNDLES = {
        'css': {
            'common': ['reset.css', 'main.css'],
            'ie-common': ['reset.css', 'main.css', 'ie.css],
            'landing': ['landing.css']
        },
        'js': {
            'common': ['jquery.js', 'site.js'],
        },
    }

Add `MINIFY_YAML_FILE` location to settings.py - this will be where we store 
the bundle mapping. 

Load the `MINIFY_BUNDLES_MAP` into your settings by adding the following code
to `settings.py`::

    import yaml
    try:
        MINIFY_BUNDLES_MAP = yaml.load(open(MINIFY_YAML_FILE))
    except:
        MINIFY_BUNDLES_MAP = None


Django Management Command
=========================

Create compressed JS / CSS like so:

``./manage.py compress_assets``

I store mine in the repository and so they can be tested locally before going
on to UAT and Staging and as such aren't part of the automated build process.
That is my preference you may want do this everytime.


Jinja2
======

Load the Jinja2_ extensions `jinjo_minify/extensions.py` in your jinja environment.
Heres and example environment configuration::

    env = jinja2.Environment(
        loader=loader,
        extensions=(
            'jinja2.ext.with_',
            'jinja2.ext.loopcontrols',
            'jingo_minify.extensions.JS',
            'jingo_minify.extensions.CSS',
        ),
        trim_blocks=False,
        autoescape=True,
    )

Then in your template you do something like this::
    
    <head>
        <!--[if !IE]><!--> 
            {% css "common" media="all" %}
            {% css "handheld" media="handheld" %}
            {% css "print" media="print" %}
        <!--<![endif]--> 
        <!--[if gt IE 6]>
            {% css "ie-common" media="all" %}
            {% css "handheld" media="handheld" %}
            {% css "print" media="print" %}
        <![endif]-->

           {% js "common" %}
    </head>


Nginx
======

The outputted filenames are versioned like so::

    { file_name }__{ hash }.{ ext }

We don't use querystrings as: 
    
    "According the letter of the HTTP caching specification, 
     user agents should never cache URLs with query strings. 
     While Internet Explorer and Firefox ignore this, 
     Opera and Safari don't - To make sure all user agents can cache your 
     resources, we need to keep query strings out of their URLs."
     
     Cal Handerson

So you need to configure your Nginx / Apache / web server, to serve these
assets with forever future expires and to ignore the 8 digits hash code.
In Nginx you can do that like so::

    rewrite "/static/(.*)__([\w]{8})\.(.*)" /static/$1.$3;
    location /static {
            access_log off;
            alias /home/your_website/static;
            expires max;
            add_header Cache-Control public;
        }

Gotchas
=======

The library uses `cat` to join the files together so please ensure there is a 
new line at the end of the file as it can cause problems.

YUI_Compressor_ will report JS errors the bundle_name.all.js is saved on creation
and can be used for debugging.  Always make sure you lint your JS - it makes 
compression easier.

Todos
=====

* Fix tests
* Version images in css - rewrite the css to include the hash of local images.
* Add support for other compressors


.. _jingo-minify: https://github.com/jsocol/jingo-minify
.. _Jinja2: http://jinja.pocoo.org/2/
.. _Django: http://djangoproject.com
.. _Django_Jinja2_integration: http://rosslawley.co.uk/2010/07/django-12-and-jinja2-integration.html
.. _YUI_Compressor: http://developer.yahoo.com/yui/compressor/
