import time
from datetime import datetime
from collections import defaultdict
from math import radians, cos, sin, asin, sqrt

try:
    import pandas as pd
    import numpy as np
    import googlemaps
    from geopy.geocoders import Nominatim
    from sklearn.cluster import SpectralClustering
except ModuleNotFoundError:
    raise Exception("Missing dependencies!")


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r


def latlon_to_xy(input_lat, input_lon, centerlat, centerlon, earthradius=6371):
    # earthradius and units default to km
    output_lat = input_lat * np.pi / 180
    output_lon = input_lon * np.pi / 180
    centerlat = centerlat * np.pi / 180
    centerlon = centerlon * np.pi / 180
    (dlat, dlon) = (output_lat - centerlat, output_lon - centerlon)
    (dx, dy) = (earthradius * np.cos(centerlat) * dlon, earthradius * dlat)
    return dx, dy


class placeDetails(object):
    def __init__(self):
        self.place_id = None
        self.name = None
        self.rating = None
        self.user_ratings_total = None
        self.lat = None
        self.lng = None
        # self.place_opening = None
        self.opening_time = None
        self.closing_time = None
        self.cluster_id = 0
        self.dx = None
        self.dy = None

    @property
    def prominence(self):
        return self.rating * self.user_ratings_total

    def __repr__(self):
        return self.name


class PlacesDataRetriever(object):

    def __init__(self, api_key, location, coverage, default_open, default_close, extract_from_file=False):
        self.location = location
        self.coverage = coverage  # in Meters
        self.pin_lat = 41.8781
        self.pin_lng = 87.6298
        self.default_opening_time = default_open
        self.default_closing_time = default_close
        self.extract_from_file = extract_from_file
        self.client = googlemaps.Client(key=api_key)
        self.place_details = []
        self.places_index_for_id = {}
        self.distance_matrix = {}
        self.hotel = None

        # Clustering Metadata
        self.largest_cluster = None
        self.number_of_clusters = None
        self.hotel_lat = None
        self.hotel_lng = None
        self.cluster_order_by_avg_prominence = []

    def get_lat_long(self, location):
        geolocator = Nominatim(user_agent="Your_Name")
        _location = geolocator.geocode(location)
        self.pin_lat = _location.latitude
        self.pin_lng = _location.longitude
        return

    def data_fetch_placesAPI(self):
        token = None  # page token for going to next page of search
        desirable_places_dict = {}
        # One request returns 20 records
        for i in range(2):
            desirable_places = self.client.places_nearby(type='tourist_attraction',
                                                         location=(self.pin_lat, self.pin_lng),
                                                         radius=self.coverage,
                                                         rank_by='prominence',
                                                         page_token=token)  # type = 'tourist_attraction'
            time.sleep(2)
            # token for searching next page; to be used in a loop
            token = desirable_places['next_page_token']
            desirable_places_dict[i] = desirable_places
        return desirable_places_dict

    def data_conversion(self, desirable_places_dict):

        for k, val in desirable_places_dict.items():
            for i, result in enumerate(val["results"]):
                thisLocation = placeDetails()
                thisLocation.place_id = result.get('place_id')
                thisLocation.name = result.get('name', "Name not Available!")
                thisLocation.rating = result.get('rating', 3)
                thisLocation.user_ratings_total = result.get('user_ratings_total', 100)
                thisLocation.lat = result['geometry']['location'].get('lat')
                thisLocation.lng = result['geometry']['location'].get('lng')
                self.place_details.append(thisLocation)

        return

    def retrieve_open_close_times(self):
        print("Looking up operating hours ...")

        for i, place in enumerate(self.place_details):
            place_details = self.client.place(place_id=place.place_id)
            if (place_details['result'].get('opening_hours') == None):
                int_open_time = self.default_opening_time
                int_close_time = self.default_closing_time
            elif (place_details['result']['opening_hours'].get('periods') == None):
                int_open_time = self.default_opening_time
                int_close_time = self.default_closing_time
            elif ((place_details['result']['opening_hours']['periods'][0].get('open') == None) | (
                    place_details['result']['opening_hours']['periods'][0].get('close') == None)):
                int_open_time = self.default_opening_time
                int_close_time = self.default_closing_time
            else:
                # Time conversion
                open_time = place_details['result']['opening_hours']['periods'][0]['open']['time']
                datetime_str = open_time[0:2] + ':' + open_time[2:4]
                datetime_object = datetime.strptime(datetime_str, '%H:%M')
                int_open_time = datetime_object.hour * 60 + datetime_object.minute

                # Time conversion
                close_time = place_details['result']['opening_hours']['periods'][0]['close']['time']
                datetime_str = close_time[0:2] + ':' + close_time[2:4]
                datetime_object = datetime.strptime(datetime_str, '%H:%M')
                # close_times[i] = datetime_object
                int_close_time = datetime_object.hour * 60 + datetime_object.minute
            place.opening_time = int_open_time
            place.closing_time = max(int_close_time, self.default_closing_time, int_open_time)
            # sometime places close at crazy times
            time.sleep(2)
        return

    def MakeDataset(self):
        records = []
        for item in self.place_details:
            records.append({
                "place_id": item.place_id,
                "name": item.name,
                "rating": item.rating,
                "user_ratings_total": item.user_ratings_total,
                "lat": item.lat,
                "lng": item.lng,
                "opening_time": item.opening_time,
                "closing_time": item.closing_time,
                "cluster_id": item.cluster_id
            })
        return pd.DataFrame(records)

    def distance_calculation(self, origin, destination):
        # Requires cities name
        my_dist = self.client.distance_matrix(origin, destination)
        return my_dist['rows'][0]['elements'][0]['distance']['value']

    def get_places_api_data(self):
        print("Looking for places ...")
        if self.extract_from_file:
            places_df = pd.read_csv("test/places.csv")
            places_df["opening_time"].fillna(self.default_opening_time, inplace=True)
            places_df["closing_time"].fillna(self.default_closing_time, inplace=True)

            for i, row in places_df.iterrows():
                _place = placeDetails()
                _place.place_id = row["place_id"]
                _place.name = row["name"]
                _place.rating = row["rating"]
                _place.user_ratings_total = row["user_ratings_total"]
                _place.lat = row["lat"]
                _place.lng = row["lng"]
                _place.opening_time = row["opening_time"]
                _place.closing_time = row["closing_time"]
                _place.cluster_id = row["cluster_id"]
                self.place_details.append(_place)
                self.places_index_for_id[_place.place_id] = i

        else:
            self.get_lat_long(self.location)
            desirable_places_dict = self.data_fetch_placesAPI()
            self.data_conversion(desirable_places_dict)
            self.retrieve_open_close_times()

    def set_cluster_metadata(self):
        df = self.MakeDataset()
        df["prominence"] = df["rating"] * df["user_ratings_total"]
        grouped_df = df.groupby("cluster_id").agg({"lat": "mean", "lng": "mean", "name": "count", "prominence": "sum"})
        grouped_df["avg_prominence"] = grouped_df["prominence"] / grouped_df["name"]
        grouped_df.reset_index(inplace=True, drop=False)
        grouped_df.sort_values(by=["avg_prominence"], ascending=False, inplace=True)
        self.number_of_clusters = grouped_df.shape[0]
        self.cluster_order_by_avg_prominence = grouped_df["cluster_id"].to_list()
        grouped_df.sort_values(by=["name"], ascending=False, inplace=True)
        self.largest_cluster = grouped_df.loc[0, "cluster_id"]
        self.hotel_lat = grouped_df.loc[0, "lat"]
        self.hotel_lng = grouped_df.loc[0, "lng"]
        return

    def perform_location_clustering(self, days):
        print("Thinking about your itinerary ...")
        if self.extract_from_file:
            # Add clustering code  - update place_details.cluster_id >>
            clustering_data = []
            for place in self.place_details:
                _x, _y = latlon_to_xy(place.lat, place.lng, self.pin_lat, self.pin_lng)
                clustering_data.append([_x, _y])
            sc = SpectralClustering(n_clusters=days)
            sc.fit(clustering_data)
            for i, place in enumerate(self.place_details):
                place.cluster_id = sc.labels_[i]
        else:
            # Add clustering code  - update place_details.cluster_id >>
            clustering_data = []
            for place in self.place_details:
                _x, _y = latlon_to_xy(place.lat, place.lng, self.pin_lat, self.pin_lng)
                clustering_data.append([_x, _y])
            sc = SpectralClustering(n_clusters=days)
            sc.fit(clustering_data)
            for i, place in enumerate(self.place_details):
                place.cluster_id = sc.labels_[i]
        self.set_cluster_metadata()
        return

    def retrieve_hotels(self):
        print("Searching for top hotels ...")
        if self.extract_from_file:
            hotel_recommendations = pd.read_csv("test/hotel_data.csv")[
                ["place_id", "name", "rating", "user_ratings_total", "address"]]
            hotel_recommendations["prominence_score"] = hotel_recommendations["rating"] * hotel_recommendations[
                "user_ratings_total"]
            hotel_recommendations.sort_values(by=["prominence_score"], ascending=False, inplace=True)
            hotel_recommendations.drop(columns=["prominence_score", "place_id"], inplace=True)

        else:
            desirable_hotels_dict = {}
            desirable_hotels = self.client.places_nearby(type='lodging', location=(self.hotel_lat, self.hotel_lng),
                                                         radius=5000,
                                                         rank_by='prominence')
            desirable_hotels_dict[1] = desirable_hotels
            token = desirable_hotels['next_page_token']
            hotel_records = []

            for i, result in enumerate(desirable_hotels_dict[1]['results']):
                record = defaultdict()
                record["place_id"] = result.get('place_id')
                record["name"] = result.get("name")
                record["rating"] = result.get('rating')
                record["user_ratings_total"] = result.get('user_ratings_total')
                record["address"] = result.get("vicinity")
                hotel_records.append(record)

            hotel_recommendations = pd.DataFrame(hotel_records)
            hotel_recommendations["prominence_score"] = hotel_recommendations["rating"] * hotel_recommendations[
                "user_ratings_total"]
            hotel_recommendations.sort_values(by=["prominence_score"], ascending=False, inplace=True)
            hotel_recommendations.drop(columns=["place_id", "prominence_score"], inplace=True)

        print("******************************** RECOMMENDED LODGING ******************")
        print(hotel_recommendations.to_string(index=False))
        print("***********************************************************************")
        hotel = placeDetails()
        hotel.place_id = "hotel"
        hotel.name = "hotel"
        hotel.opening_time = 480
        hotel.closing_time = 1290
        hotel.rating = 0
        hotel.user_ratings_total = 0
        hotel.lat = self.hotel_lat
        hotel.lng = self.hotel_lng
        self.hotel = hotel
        return

    def retrieve_distance_matrix(self):
        print("Computing distances and transit times ...")
        if self.extract_from_file:
            distances_df = pd.read_csv("test/distances.csv")
            self.distance_matrix = distances_df.set_index(["place_id_x", "place_id_y"])["road_distance"].to_dict()
        else:
            # Haversine distances and conversion to minutes >
            for i in self.place_details + [self.hotel]:
                for j in self.place_details + [self.hotel]:
                    dist = haversine(i.lng, i.lat, j.lng, j.lat)
                    transit_time = round(dist, 2) * 1000  # distance in meters
                    # In minutes >> km - miles - (avg speed 30 miles/hr - 0.5 miles/min)
                    self.distance_matrix[(i.place_id, j.place_id)] = transit_time
        return

        # Add Maps API Code
