from itinative.helper_functions import PlacesDataRetriever
from itinative.day_scheduler import bestpriceColletingRoute


class Agent(object):
    def __init__(self, days, location, api_key):
        self.location = location
        self.days = days
        self.maxCoverage = 50000
        self.default_opening_time = 480  # 8 AM * 60
        self.default_closing_time = 1140  # 7 PM * 60
        self.waiting_time = 90  # Minutes
        self.maxVisits_in_a_day = 7
        self.extract_from_file = False  # debugging tool
        self.api_key = api_key
        self.time_format = """
        Itinative accepts a time value in military format. Here are a few examples:
        
        - 08:00 AM = 800
        - 12:00 PM = 1200
        - 01:00 PM = 1300
        - 09:00 PM = 2100
        - 12:00 AM = 0 
        """

    def configure_opening_time(self, new_opening_time):
        assert isinstance(new_opening_time,
                          int), "Provide a time value in military format, check agent.time_format for details"
        assert 2359 >= new_opening_time >= 0, "Time value in invalid domain (0, 2359)"
        assert new_opening_time % 100 < 60, "Invalid time value!"
        self.default_opening_time = 60 * (new_opening_time // 100) + new_opening_time % 100

    def configure_closing_time(self, new_closing_time):
        assert isinstance(new_closing_time,
                          int), "Provide a time value in military format, check agent.time_format for details"
        assert 2359 >= new_closing_time >= 0, "Time value in invalid domain (0, 2359)"
        assert self.default_opening_time < new_closing_time, "Closing time must be after opening time, modify that first"
        assert new_closing_time % 100 < 60, "Invalid time value!"
        self.default_closing_time = 60 * (new_closing_time // 100) + new_closing_time % 100

    def generate(self):
        # Retrieve Data >>
        # Perform Clustering on the fly
        # Generate Distance Matrix
        processor = PlacesDataRetriever(self.api_key, self.location, self.maxCoverage,
                                        self.default_opening_time,
                                        self.default_closing_time, extract_from_file=self.extract_from_file)
        processor.get_places_api_data()
        processor.perform_location_clustering(self.days)
        print("Looking for hotels ... ")
        processor.retrieve_hotels()
        processor.retrieve_distance_matrix()

        print("Generating itinerary ... ")

        # First find the cluster with highest avg prominence -
        for i, cluster in enumerate(processor.cluster_order_by_avg_prominence):
            print(f"Determining best route for day {i + 1}")
            _trip = bestpriceColletingRoute(i, cluster, processor)
            _trip.waiting_time = self.waiting_time
            _trip.max_number_of_visits = self.maxVisits_in_a_day
            _trip.solve()

    def __repr__(self):
        return f"Itinerary planner for {self.days} in {self.location}"


def initialize(api_key="<Need an API key>"):
    assert isinstance(api_key, str), "API key must be a string type. Refer to documentation to obtain your API key"
    assert api_key != "<Need an API key>", "Obtain a Google API key, Refer to documentation"
    location = input("Enter the location:")
    number_of_days = input("How many days are you planning for?")
    return Agent(int(number_of_days), location, api_key)


if __name__ == "__main__":
    agent = initialize(api_key="AIzaSyAhBURl7DjEgDonyF3RZboLvrgkYAzpjOE")
    agent.generate()
