from distutils.core import setup, Extension
setup(name='catocryptpy', version='1.0', ext_modules=[Extension('catocryptpy', 
    sources = ['py_hooks.cc','blowfish.cc', 'base64.cc'])])
