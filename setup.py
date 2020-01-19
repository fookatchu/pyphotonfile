#!venv/Scripts/python

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='pyphotonfile',
      version='0.2.1',
      # packages=['pyphotonfile'],
      author="Heiko Westermann",
      author_email="heiko+pyphotonfile@orgizm.net",
      description="Library for reading and writing files for the Anycubic Photon 3D-Printer",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/fookatchu/pyphotonfile",
      packages=find_packages(),
      package_data={
        'pyphotonfile': ['newfile.photon'],
        },
      install_requires=['numpy', 'Pillow'],
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
      ],
     )
