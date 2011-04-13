import os
import hashlib
import yaml
import re
import shutil

from subprocess import call, PIPE
	
from django.conf import settings
from django.core.management.base import BaseCommand


path = lambda *a: os.path.join(settings.MEDIA_ROOT, *a)

CSS_ASSET_PATTERN = re.compile('(?P<url>url(\([\'"]?(?P<filename>[^)]+\.[a-z]{3,4})(?P<fragment>#\w+)?[\'"]?\)))')

class Command(BaseCommand):  #pragma: no cover
    help = ("Compresses css and js assets defined in settings.MINIFY_BUNDLES")

    requires_model_validation = False

    def handle(self, **options):
        jar_path = (os.path.dirname(__file__), '..', '..', 'bin',
                'yuicompressor-2.4.4.jar')
        path_to_jar = os.path.realpath(os.path.join(*jar_path))

        v = ''
        if 'verbosity' in options and options['verbosity'] == '2':
            v = '-v'
        
        bundle_versions = {}
        
        for ftype, bundle in settings.MINIFY_BUNDLES.iteritems():
            
            # Create the bundle file type dictonary
            if ftype not in bundle_versions:
                bundle_versions[ftype] = {}
            
            for name, files in bundle.iteritems():
                
                namespace = getattr(settings, 'MINIFY_NAMESPACE', '')
                
                concatted_file_name = '%s%s-all.%s' % (namespace, name, ftype,)
                compressed_file_name = '%s%s-min.%s' % (namespace, name, ftype,)
                
                concatted_file = path(ftype, concatted_file_name)
                compressed_file = path(ftype, compressed_file_name)
                real_files = [path(f.lstrip('/')) for f in files]
                
                if real_files:
                    dir_name = os.path.dirname(compressed_file)
                    if not os.path.exists(dir_name):
                        os.makedirs(dir_name)
                    
                    # Concats the files.
                    call("cat %s > %s" % (' '.join(real_files), concatted_file),
                         shell=True)
                    
                    # Rewrite image paths in css
                    if ftype == 'css':
                        self.rewrite_asset_paths_in_css(concatted_file)
                        
                    # # Compresses the concatenation.
                    call("%s -jar %s %s %s -o %s" % (settings.JAVA_BIN, path_to_jar,
                         v, concatted_file, compressed_file), shell=True, stdout=PIPE)
                    
                    file_hash = self.file_hash(compressed_file)
                    
                    bundle_versions[ftype][name] = {
                        'hash': self.file_hash(compressed_file),
                        'concatted': concatted_file_name,
                        'compressed': compressed_file_name,}
        
        # Write settings to file
        settings_yaml = open(settings.MINIFY_YAML_FILE, "w")
        yaml.dump(bundle_versions, settings_yaml)
        settings_yaml.close()
        
    def rewrite_asset_paths_in_css(self, filename):
        tmp = os.tmpfile()
        rel_filename = os.path.join(settings.MEDIA_ROOT, filename)
        css = open(rel_filename, mode='r')
        
        self.asset_hashs = {}
        
        for line in css:
            matches = []
            for match in re.finditer(CSS_ASSET_PATTERN, line):
                try:
                    grp = match.groupdict()
                    absolute = grp['filename'].startswith('/')
                    
                    if absolute:
                        asset_path = os.path.join(settings.MEDIA_ROOT, '.'+grp['filename'])
                    else:
                        asset_path = os.path.join(os.path.dirname(rel_filename), grp['filename'])
                        
                    asset = os.path.relpath(asset_path, settings.MEDIA_ROOT)
                    
                    asset_hash = self.get_asset_hash(asset)
                    
                    asset = grp['filename'].rsplit('.',1)
                    asset[0]+= '__%s' % asset_hash
                    asset = '.'.join(asset)
                    
                    asset_version = 'url(%s)' % asset
                    matches.append((grp['url'], asset_version))
                    
                except KeyError:
                    print "Failed to find %s in version map. Is it an absolute path?" % asset
                    raise SystemExit(1)
                    
            for old, new in matches:
                line = line.replace(old, new)
            
            tmp.write(line)
            
        tmp.flush()
        tmp.seek(0)
        css.close()
        
        css = open(rel_filename, mode='wb')
        shutil.copyfileobj(tmp, css)
    
    def get_asset_hash(self, asset):
        asset_hash = self.asset_hashs.get(asset, None)
        if not asset_hash:
            try:
                asset_hash = self.file_hash(asset)
                self.asset_hashs.update({asset:asset_hash})
            except:
                print 'Asset "%s" referenced in css and not found.' % asset
                asset_hash = ''
        return asset_hash
                
    def file_hash(self, filename):
        f = open(filename, mode='rb')
        try:
            return hashlib.md5(f.read()).hexdigest()[:8]
        finally:
            f.close()