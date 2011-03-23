import os
import hashlib
import yaml

from subprocess import call, PIPE
	
from django.conf import settings
from django.core.management.base import BaseCommand


path = lambda *a: os.path.join(settings.MEDIA_ROOT, *a)


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

    def file_hash(self, filename):
        f = open(filename, mode='rb')
        try:
            return hashlib.md5(f.read()).hexdigest()[:8]
        finally:
            f.close()