# Planning a trip?

When it comes to trip planning, we tend to go search for a travel blog to find out 
what are the places to visit, things to do etc. by the time we look at 2-3 pages we 
already have a list of things in our head. Things we care about are:

- Where to stay?
- How should we set the plan?
- We do not want to commute much, Can we visit some places in one go?

This creeps in a lot of confusion and more often than not we tend to 
procrastinate on our planning and travel. You're imagining a lot of back and forth with
google maps, Isn't it?

Itinative is a python package built on top of google API's which intend to automate 
trip planning with the least amount of information and create a recommendation of an 
itinerary with several considerations: 

1. Maximize the prominence covered in the available time (must visit important places)
2. Consolidate nearby places together
3. Won't go to a place when it's not open
4. Allocate some time at each place of visit
5. Recommend hotels at the city hotspot
6. Don't start too early don't finish too late
7. ... and a few more ...

_Name your city_ and _No. of days_ and let itinative be your travel planner!

## Installation

While we get this to pypi, use the following: 
```
pip install git+https://github.com/geraparth/itinative.git@v1.10
```

## Usage:
1. Import packge and initialize it with an API key
    ```python
   import itinative
   agent = itinative.initialize(api_key= "YOUR API KEY" )
    ```
    Read the instructions 
[here](https://developers.google.com/maps/documentation/javascript/get-api-key#creating-api-keys) 
to obtain your personal API key

3. Give two things to start the planner:

   - `Enter the location:` _Which city you want to visit?_
   - `How many days are you planning for?:` _1,2,3.. whatever_


3. And finally, call generate function that does the job.

    ```python
   agent.generate()
    ```
## Demo

- Check this [jupyter-notebook](https://github.com/geraparth/itinative/blob/main/examples/Demo.ipynb)
- [Video](https://drive.google.com/file/d/1ipLp0wxH7c0ujVEsFsnYZe3syHVy1-c3/view?usp=sharing)

### Some common configurations
All the configurations can be done on the agent before calling the `generate()` method.

1. Itinative retrieves opening times and closing time for the places from Google but it 
doesn't know when you start/want to start your trip and call it a day. Itinative assumes local time
8 AM for opening and 7 PM for closing.

   However, you can configure it (if needed) using the utility methods:
   ```python
    agent = itinative.initialize()
    agent.configure_opening_time( <new opening time> )
    agent.configure_closing_time( <new closing time> )
   ```
   Note: The package follows an easy [military time format](https://militaryconnection.com/military-time/). 
   If not familiar, get available examples using: `print(agent.time_format)`
2. Change waiting time, due to places API restrictions itinative in the current version cannot retrieve
the "time usually spent" values from google. So we've assumed that the user plans to stay for about 90 minutes at
a place. This can be configured as shown below:
   ```python
   agent = itinative.initialize()
   agent.waiting_time = <new waiting time in minutes>
   ```

## Citations
- [Google Maps Platform](https://developers.google.com/maps)
- [Prize Collecting TSP](https://github.com/pigna90/PCTSPTW)
- [Spectral Clustering](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.SpectralClustering.html)

## Science
[Linked](https://drive.google.com/file/d/1hDT6tTc8spL4AIZB8JFZzpFQvc58PbYM/view?usp=sharing)

