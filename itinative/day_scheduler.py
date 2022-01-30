import datetime

try:
    import pandas as pd
    from pulp import *
except ModuleNotFoundError:
    print("Missing dependencies!")
    pass


class bestpriceColletingRoute(object):
    def __init__(self, day, cluster_id, processor):
        self.day = day

        self.waiting_time = None
        self.solv = "GUROBI"
        self.timeout = 99
        self.max_number_of_visits = 7
        self.msg = 0

        self.route_visits = [processor.hotel] + [self.prize for self.prize in processor.place_details
                                                 if self.prize.cluster_id == cluster_id] + [processor.hotel]
        # Elegant stuff >>
        self.NODES = [i + 1 for i, loc in enumerate(self.route_visits[1:-1])]
        self.opening_times = {i: loc.opening_time for i, loc in enumerate(self.route_visits)}
        self.closing_times = {i: loc.closing_time for i, loc in enumerate(self.route_visits)}
        self.prize = {i: loc.prominence for i, loc in enumerate(self.route_visits)}
        self.distances = []
        for loc_i in self.route_visits:
            _dist_row = []
            for loc_j in self.route_visits:
                _dist_row.append(processor.distance_matrix[(loc_i.place_id, loc_j.place_id)] / 1000 * 0.8)
            self.distances.append(_dist_row)

    def solve(self):

        # Origin
        o = 0
        # Arrive
        d = len(self.NODES) + 1

        prob = LpProblem("PCTSPTW", LpMaximize)  # Maximize problem
        y = LpVariable.dicts("y", self.NODES, 0, 1, LpBinary)  # y as decision variable for PoI
        T = LpVariable.dicts("T", ([o] + self.NODES + [d]), None, None, LpContinuous)
        # T as visit time at specific node
        x = LpVariable.dicts("x", [(i, j)
                                   for i in ([o] + self.NODES)
                                   for j in (self.NODES + [d])
                                   if i != j], 0, 1, LpBinary)  # x as decision variable for an arc between two nodes

        prob += lpSum(self.prize[i] * y[i] for i in self.NODES)  # Objective function

        # Constraint (1)
        for i in self.NODES:
            prob += lpSum(x[(i, j)] for j in ([d] + self.NODES) if i != j) == y[i]

        # Constraint (2)
        for j in self.NODES:
            prob += lpSum(x[(i, j)] for i in ([o] + self.NODES) if i != j) == y[j]

        # Constraint (3)
        prob += lpSum(x[(o, j)] for j in self.NODES) == 1

        # Constraint (4)
        prob += lpSum(x[(i, d)] for i in self.NODES) == 1

        # Constraint (5)
        for i in ([o] + self.NODES):
            for j in ([d] + self.NODES):
                if (i != j):
                    prob += (T[i] + self.waiting_time + self.distances[i][j] - T[j]) <= max(
                        self.closing_times[i] + self.distances[i][j] - self.opening_times[j], 0) * (1 - x[(i, j)])
                    prob += x[(i, j)] >= 0

        # Constraint (6)
        for i in ([o] + self.NODES + [d]):
            prob += T[i] >= self.opening_times[i]
            prob += T[i] + self.waiting_time <= self.closing_times[i]

        # Constraint (7)
        prob += lpSum(y[i] for i in self.NODES) <= self.max_number_of_visits

        if self.solv == "GUROBI":
            prob.solve(GUROBI(TimeLimit=self.timeout, msg=self.msg))
        else:
            print(self.solv + " solver doesn't exists")
            quit()

        # prob.writeLP("/tmp/prob/"+ inst + ".lp")

        # Print problem status
        # print("Status solution: ", LpStatus[prob.status])
        if self.msg == 1:
            print("--------")
            # Print PoI visited
            print("PoI visited")
            for i in self.NODES:
                if (value(y[i]) >= 1):
                    print("y_" + str(i), "=", 1)
            print("--------")

        edges = []
        # # Printing archs used
        for i in [o] + self.NODES:
            for j in [d] + self.NODES:
                if (i != j):
                    if (value(x[(i, j)]) >= 1):
                        if j != d:
                            if self.msg == 1:
                                print("x(" + str(i) + "_" + str(j) + ") =", 1)
                            edges.append((i, j))
                        else:
                            if self.msg == 1:
                                print("x(" + str(i) + "_" + str(o) + ") =", 1)
                            edges.append((i, o))
        if self.msg:
            print("--------")

        # # Printing path
        path = []
        node = 0
        for i in range(0, len(edges)):
            for j in edges:
                if node == j[0]:
                    path.append(node)
                    node = j[1]
                    edges.remove(j)
        path.append(0)

        itinerary_records = [{
            "Point of Interest": "Start at the hotel",
            "Arrive at": "Have Breakfast",
            "Depart at": "-"
            # datetime.time(hour=round((value(T[path[0]]) + self.waiting_time) / 60),
            #                        minute=round((value(T[path[0]]) + self.waiting_time) % 60)).strftime("%H:%M")
        }]

        for p in path[1:-1]:
            itinerary_records.append({"Point of Interest": self.route_visits[p].name,
                                      "Arrive at": datetime.time(hour=round(value(T[p]) // 60),
                                                                 minute=min(round(value(T[p]) % 60), 59)).strftime(
                                          "%H:%M"),
                                      "Depart at": datetime.time(
                                          hour=round((value(T[p]) + self.waiting_time) // 60),
                                          minute=min(round((value(T[p]) + self.waiting_time) % 60), 59)).strftime(
                                          "%H:%M")
                                      })
        itinerary_records.append({
            "Point of Interest": "Arrive at the hotel",
            "Arrive at": "-",
            # datetime.time(hour=round(value(T[path[-1]]) / 60),
            #                        minute=round(value(T[path[-1]]) % 60)).strftime("%H:%M"),
            "Depart at": "Take Rest!"
        })

        if self.msg:
            print("--------")
            print("\nPath:")
            print(*path, sep="->")

        print(f"\n###################### DAY {self.day + 1} ######################")
        itinerary_df = pd.DataFrame(itinerary_records)
        print(itinerary_df.to_string(index=False))
        print("###############################################################\n")
