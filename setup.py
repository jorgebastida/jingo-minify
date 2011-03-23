from setuptools import setup, find_packages

setup(
    name='jingo_minify',
    version='0.5',
    description='A Django app that will concat and minify JS and CSS.',
    author='Dave Dash, James Socol, Ross Lawley',
    author_email='dd@mozilla.com, james@mozilla.com, ross.lawley@streetlife.com',
    url='http://github.com/sbook/django-jinga2-minify',
    license='BSD',
    packages=find_packages(exclude=['examples.*']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Environment :: Web Environment :: Mozilla',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
