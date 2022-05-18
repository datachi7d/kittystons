from setuptools import setup

setup(name='kittystons',
      version='0.1',
      description='Zoneminder events published to slack',
      author='Sean Kelly',
      author_email='seandtkelly@gmail.com',
      packages=['kittystons'],
      scripts=['bin/kittystons'],
      install_requires=[
          'slack-sdk>=3.4.2',
          'pyzm>=0.3.38',
          'opencv-python>=4.5.1.48',
          'paho-mqtt>=1.5.1'
      ]
)