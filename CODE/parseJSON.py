import json


def parseTripPatterns(filename:str):
    """
    parseTripPatterns reads a JSON file with trip patterns generated from a GraphQL query.

    :param filename: String representation of file path

    :return results: List of all trip patterns. Each trip pattern is a List of dictionaries
    """

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    tripPatterns = data.get("data", {}).get("trip", {}).get("tripPatterns", [])

    results = []

    for pattern in tripPatterns:
        trip = []
        for leg in pattern.get("legs", []):
            start = leg.get("expectedStartTime")[11:19]
            end = leg.get("expectedEndTime")[11:19]
            fromPlace = leg.get("fromPlace", {}).get("name")
            toPlace = leg.get("toPlace", {}).get("name")
            expected_start_time = start
            expected_end_time = end
            line = leg.get("line", {})

            if line == None:
                line = "walk"
            else:
                line = line.get("publicCode")
            
                
            if expected_start_time and line:
                trip.append({"expectedStartTime": expected_start_time,
                                "expectedEndTime": expected_end_time,
                                "line": line,
                                "fromPlace": fromPlace,
                                "toPlace": toPlace,})
        if len(trip) > 0:
            results.append(trip)
    
    return results


print(parseTripPatterns("midtun-aasane.json"))


