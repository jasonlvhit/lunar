from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()
    
version='0.0.1'

setup(
    name='lunar',
    version=version,
    packages=['lunar'],
    author="jasonlyu",
    author_email="jasonlvhit@gmail.com",
    description="lunar is a WSGI based webframework in pure Python, without any third-party dependency.",
    classifiers=[
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
            'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    long_description=long_description,
)