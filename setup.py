from setuptools import setup
from itinative import __version__, __author__, __doc__

setup(
    name='itinerary-planner',
    version=__version__,
    packages=['itinative'],
    url='',
    license='MIT',
    author=__author__,
    author_email='mohitmhjn147@gmail.com',
    description=__doc__,
    install_requires=['googlemaps', 'pulp', 'numpy', 'geopy', 'pandas', 'scikit-learn']
)
