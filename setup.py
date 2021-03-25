from setuptools import setup

setup(name='nx584mqtt',
      version='1.1',
      description='NX584/NX8E Interface Library and Server',
      author='rocket4321',
      url='http://github.com/rocket4321/nx584mqtt',
      packages=['nx584mqtt'],
      install_requires=['paho-mqtt', 'requests', 'prettytable', 'pyserial'],
      extras_require={
        'full': ['flask'],
      },
      scripts=['nx584_server', 'nx584_client'],
  )
