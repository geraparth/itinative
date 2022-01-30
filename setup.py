from setuptools import setup
import itinative

setup(
    name='itinerary-planner',
    version=itinative.__version__,
    packages=['itinative'],
    url='',
    license='MIT',
    author=itinative.__author__,
    author_email='mohitmhjn147@gmail.com',
    description=itinative.__doc__,
    install_requires=['googlemaps', 'pulp', 'numpy','geopy','pandas','scikit-learn']
)
