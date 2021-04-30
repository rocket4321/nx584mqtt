from setuptools import setup

from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rd'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='nx584mqtt',
      version='0.1.2',
      description='NX584/NX8E Interface Library and Server with MQTT client',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='rocket4321',
      url='http://github.com/rocket4321/nx584mqtt',
      packages=['nx584mqtt'],
      install_requires=['paho-mqtt', 'requests', 'pyserial'],
      extras_require={
        'full': ['flask', 'prettytable'],
        'http': ['flask'],
        'client': ['prettytable'],
      },
      scripts=['nx584_server', 'nx584_client'],
  )

