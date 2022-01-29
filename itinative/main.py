from itinative.helper_functions import PlacesDataRetriever
from itinative.dayPlanner import bestpriceColletingRoute


class ItineraryPlanner(object):
    def __init__(self, days, location):
        self.location = location
        self.days = days
        self.maxCoverage = 50000
        self.default_opening_time = 480  # 8 AM * 60
        self.default_closing_time = 1140  # 7 PM * 60
        self.waiting_time = 90  # Minutes
        self.maxVisits_in_a_day = 7
        self.extract_from_file = False

    def generate(self):
        # Retrieve Data >>
        # Perform Clustering on the fly
        # Generate Distance Matrix
        processor = PlacesDataRetriever(self.location, self.maxCoverage,
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
            print(f"Determining best route for day {i+1}")
            _trip = bestpriceColletingRoute(i, cluster, processor)
            _trip.waiting_time = self.waiting_time
            _trip.max_number_of_visits = self.maxVisits_in_a_day
            _trip.solve()

    def __repr__(self):
        return f"Itinerary planner for {self.days} in {self.location}"


def initialize():
    location = input("Enter the location:")
    number_of_days = input("How many days are you planning for?")
    return ItineraryPlanner(int(number_of_days), location)


if __name__ == "__main__":
    planner = initialize()
    planner.generate()
