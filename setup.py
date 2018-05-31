from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='asynapplicationinsights',
      version='0.1',
      description='Azure Application Insights client using asyncio',
      long_description=readme(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.6.5',
          'Topic :: Azure Application Insights :: Telemetry :: async',
      ],
      url='https://github.com/RobertoPrevato/asynapplicationinsights',
      author='Roberto Prevato',
      author_email='roberto.prevato@gmail.com',
      keywords='asyncio aiohttp azure application insights telemetry',
      license='MIT',
      packages=['asynapplicationinsights'],
      install_requires=[
          'aiohttp',
      ],
      include_package_data=True,
      zip_safe=False)
