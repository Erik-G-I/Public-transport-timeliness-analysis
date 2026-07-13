#%%
# import libraries and methods
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
from collections import Counter
import numpy as np
import pandas as pd


def clean_dataset(usecols, dtypes, path_to_dataset: str | list[str], national_holidays: list[str]):
        # Read and clean data set

        # Notes: Read entire data set. Store each bus line separatly. 

        # Columns in data set:
        # Rute; Rutenavn; DriftsDato; Ukedag; SekvensHoldeplassFra; HoldeplassFraNsrID; HoldeplassFraNavn; AvgangstidPlanlagt; AvgangstidFaktisk; AvgangstimeFaktisk; SekvensHoldeplassTil; HoldeplassTilNsrID; HoldeplassTilNavn; AnkomstHoldeplassTilPlanlagt; AnkomstHoldeplassTilFaktisk; TidSidenForrigeHoldeplassFaktiskSek; TidPåHoldeplassFaktiskSe; Retning; KjøretidPlanlagtSek; KjøretidFaktiskSek; Telle_Status; Time_Status; TurID;

        # Use only the columns neded for the analysis
    
    usecols = usecols 
        # Optimize memory usage by specifying data types for each column
    dtypes = dtypes
    
    if type(path_to_dataset) != type(str):
        dfs = []
        for dataset in path_to_dataset:
            dfs.append(pd.read_csv(dataset, sep=";", encoding="utf-8", usecols=usecols, dtype=dtypes))
        df = pd.concat(dfs)
    else:
        df = pd.read_csv(str(path_to_dataset), sep=";", encoding="utf-8", usecols=usecols, dtype=dtypes)
    
    original_size = len(df)

    df["Rute"] = df["Rute"].astype("category")

    df = df[(df.Ukedag != "7" ) & (df.Ukedag != "1")] # remove Weekends from dataset

    # Remove national holidays and days with extraordinary time tables: (christmas-new years day, easter)
    national_holidays = national_holidays
    post = []
    # IF YOU ARE ONLY USING DAYS AFTER THE SCHEDULE CHANGE FOR BUS NO. 81, COMMENT OUT LINE 43, AND UNCOMMENT LINE 44-46
    for holiday in national_holidays: # remove national holidays
        df = df[~df["DriftsDato"].str.contains(holiday)]
        #df2 = df[df["DriftsDato"].str.contains(holiday)]
        #post.append(df2)
    #df = pd.concat(post)

    df["DriftsDato"] = pd.to_datetime(df["DriftsDato"])
    df["AvgangstidPlanlagt"] = pd.to_datetime(df["AvgangstidPlanlagt"])
    df["AvgangstidFaktisk"] = pd.to_datetime(df["AvgangstidFaktisk"])
    df["AnkomstHoldeplassTilPlanlagt"] = pd.to_datetime(df["AnkomstHoldeplassTilPlanlagt"])
    df["AnkomstHoldeplassTilFaktisk"] = pd.to_datetime(df["AnkomstHoldeplassTilFaktisk"])


    cleaned_size = len(df)
    print("")
    print(f"Size before cleaning: {original_size}\nSize after cleaning: {cleaned_size}\nReduced size by {100-((cleaned_size/original_size)*100)}%")
    print(f"Removed weekends and national holidays")

    return df


#%%

# Get direction of trip
def get_direction(line:pd.DataFrame, from_place, to_place):
    """
    Given a valid set of parameters, returns the direction of the trip.
    
    :param line: DataFrame of the line data
    :type line: pd.DataFrame
    :param from_place: Name of the start stop
    :type from_place: String
    :param to_place: Name of the end stop
    :type to_place: String
    """

    opposite_direction = {1:2,
                         2:1}
    
    x = line[line["HoldeplassFraNavn"]==from_place].iloc[0]
    x_id = x.get("TurID")
    x_direction = x.get("Retning")
    x_sequence = x.get("SekvensHoldeplassFra")

    y = line[(line["HoldeplassTilNavn"]==to_place) & (line["TurID"]== x_id)]
    if len(y) >= 1:
        for row in y.iterrows():
            y_sequence = row[1].get("SekvensHoldeplassTil")
            if x_sequence < y_sequence:
                return x_direction

    return opposite_direction[x_direction]

#%% 
# Function for measuring time of trip
def measure_all_trips(pattern:list, departure_time:datetime, transfer_buffer:int, all_bus_lines_dict:dict):
    """
    Takes a trip pattern as input and measures total time\n 
    for all instances of this trip pattern in the dataset.
    Outputs a dictionary mapping days to the list of trips with their respective travel time
    
    :param pattern:List of all legs of a trip in the format: [{expectedStartTime, expectedEndTime, line, fromPlace, toPlace}, {...}]
    :type pattern: list
    :param departure_time: Time of departure from the starting point
    :type departure_time: datetime
    :param transfer_buffer: How many minutes needed for a line transfer
    :type transfer_buffer: int
    :param all_bus_lines_dict: Dictionary with dataframes of each bus line available
    :type all_bus_lines_dict: dict
    """
    start_time = departure_time
    all_days = next(iter(all_bus_lines_dict.values()))["DriftsDato"].unique()
    pattern_dict = {}
    
    for day in all_days:
        current_time = datetime(year=day.year, month=day.month, day=day.day, hour=start_time.hour, minute=start_time.minute, second=start_time.second)
        
        for leg in pattern:
            line = leg.get("line")
            from_place = leg.get("fromPlace")
            to_place = leg.get("toPlace")

            if line == "walk":
                exp_start = list(map(lambda x: int(x), str(leg.get("expectedStartTime")).split(":")))
                exp_end = list(map(lambda x: int(x), str(leg.get("expectedEndTime")).split(":")))
                expected_depart = datetime(year=day.year, month=day.month, day=day.day, hour=exp_start[0], minute=exp_start[1], second=exp_start[2]) 
                expected_arrival = datetime(year=day.year, month=day.month, day=day.day, hour=exp_end[0], minute=exp_end[1], second=exp_end[2]) 
                actual_depart = current_time
                actual_arrival = actual_depart + (expected_arrival - expected_depart)
            else:
                if "/" in line:
                    lines = line.split("/")
                    dfs = []
                    for l in lines:
                        df = all_bus_lines_dict[l]
                        direction = get_direction(df, from_place, to_place)
                        df1 = df[df["Retning"] == direction]
                        dfs.append(df1)
                    line_df = pd.concat(dfs)

                else:
                    df1 = all_bus_lines_dict[line]
                    dir_dict = {"inbound": 1,
                                "outbound": 2}
                    direction = get_direction(df1, from_place, to_place)
                    #direction = dir_dict[leg.get("directionType")]
                    line_df = df1[df1["Retning"] == direction]

                # If the current stop is the starting point in the trip pattern, do not add transfer buffer.
                # If the current stop is not the start, add a transfer buffer
                if(from_place != pattern[0]["fromPlace"]):
                    current_time = current_time.__add__(timedelta(minutes=transfer_buffer))
                possible_rows = line_df[(line_df["AvgangstidFaktisk"] >= current_time) & (line_df["DriftsDato"] == day) & (line_df["HoldeplassFraNavn"] == from_place)]
                possible_rows = possible_rows.sort_values(by="AvgangstidFaktisk")
                # If the first instance in the possible rows does not have real-time data, 
                # remove this instance from the pattern_dict
                try:
                    trip_id = possible_rows["TurID"].iloc[0]
                    actual_depart = possible_rows["AvgangstidFaktisk"].iloc[0]
                    actual_arrival = line_df[(line_df["TurID"] == trip_id) & (line_df["HoldeplassTilNavn"]==to_place)]["AnkomstHoldeplassTilFaktisk"].iloc[0]
                    if ((type(actual_depart) == pd.api.typing.NaTType) or (type(actual_arrival) == pd.api.typing.NaTType)):
                        print(f"Null value found; Dropping departure for {day}")
                        raise Exception()


                except Exception as e:
                    print("pop")
                    pattern_dict.pop(day, None)
                    continue
                
            current_time = actual_arrival
            x = pattern_dict.get(day, [])
            x.append((from_place, to_place, actual_depart, actual_arrival))
            pattern_dict.update({day : x})

    
    result = {k: v for k, v in pattern_dict.items() if len(v) == len(pattern)}
    
    return result
#%%
# Get scheduled total time function

def get_scheduled_total_time(trip_pattern: list, departure_time: datetime, transfer_buffer, all_bus_lines_dict:dict):
    current_time = departure_time
    for leg in trip_pattern:
        line = leg.get("line")
        from_place = leg.get("fromPlace")
        to_place = leg.get("toPlace")
        if line == "walk":
            exp_start = list(map(lambda x: int(x), str(leg.get("expectedStartTime")).split(":")))
            exp_end = list(map(lambda x: int(x), str(leg.get("expectedEndTime")).split(":")))
            expected_depart = datetime(year=2026, month=1, day=1, hour=exp_start[0], minute=exp_start[1], second=exp_start[2]) 
            expected_arrival = datetime(year=2026, month=1, day=1, hour=exp_end[0], minute=exp_end[1], second=exp_end[2])
            current_time += (expected_arrival - expected_depart)
        else:
            if "/" in line:
                lines = line.split("/")
                dfs = []
                for l in lines:
                    df = all_bus_lines_dict[l]
                    direction = get_direction(df, from_place, to_place)
                    df1 = df[(df["Retning"] == direction)]
                    dfs.append(df1)
                line_df = pd.concat(dfs)
            else:
                df1 = all_bus_lines_dict[line]
                dir_dict = {"inbound": 1,
                            "outbound": 2}
                direction = get_direction(df1, from_place, to_place)
                line_df = df1[(df1["Retning"] == direction)]
            
            if(from_place != trip_pattern[0]["fromPlace"]):
                    current_time = current_time.__add__(timedelta(minutes=transfer_buffer))
            possible_rows = line_df[(line_df["AvgangstidPlanlagt"] >= current_time) & (df1["HoldeplassFraNavn"] == from_place)]
            possible_rows = possible_rows.sort_values(by="AvgangstidPlanlagt")
            # If the first instance in the possible rows does not have scheduled-time data, 
            # remove this instance from the pattern_dict
            try:
                trip_id = possible_rows["TurID"].iloc[0]
                current_time = line_df[(line_df["TurID"] == trip_id) & (line_df["HoldeplassTilNavn"]==to_place)]["AnkomstHoldeplassTilPlanlagt"].iloc[0]
            except:
                continue

    total_time = current_time - departure_time
    return total_time


#%%

# Plotting function
def plot_cdf_for_trip_patterns(trip_pattern:list, departure_times:list[str], transfer_buffer:int, save_location:str|None, dataset:pd.DataFrame):
    '''
    plotCDFforTripPatterns measures and plots the total times for the given trip pattern
    
    :param trip_patterns: List of trip patterns in the format: [[{expectedStartTime, expectedEndTime, line, fromPlace, toPlace}, {...}],[...]]
    :type trip_patterns: list
    :param transfer_buffer: How many minutes needed for a line transfer
    :type transfer_buffer: int
    '''
    
    cmap = plt.get_cmap("rainbow", len(departure_times)).reversed()
    
    all_bus_lines_dict = dict(tuple(dataset.groupby("Rute")))

    #for pattern in trip_patterns:
    plt.figure()
    from_to = trip_pattern[0].get("fromPlace") + "-" + trip_pattern[-1].get("toPlace")
    trip_string = []
    save_name = []
    for leg in trip_pattern:
        leg_line = leg.get("line")
        if "/" in leg_line:
            new_leg_line = "or".join(leg_line.split("/"))
            trip_string.append(leg_line)
            save_name.append(new_leg_line)
        else:
            save_name.append(leg_line)
            trip_string.append(leg_line)

    combined_plot_xy = []
    combined_data = []
    combined_end_to_end = []

    percentiles = [95, 90, 80, 70]
    departure_csv = []
    save_to_csv = {
        "Departure" : [],
        95 : [],
        90 : [],
        80 : [],
        70 : [],
    }

    # For each departure in the timetable from the first stop
    for i, departureTime in enumerate(departure_times):
    #assume arrival at first bus stop 2 minutes before expected departure

        expected_start_time = datetime.strptime(departureTime, "%H:%M:%S") 
        start_time = expected_start_time - timedelta(seconds=120)

        total_times = []
        leg_times = []

        pattern_dict = measure_all_trips(trip_pattern, start_time, transfer_buffer, all_bus_lines_dict)
        

        # For each day in the dataset, calculate the total travel time for the trip pattern on this date
        # pattern_dict is in the format: {Timestep(ServiceDate) : List[(from_place, to_place, Timestamp(actual_departFrom), Timestamp(actual_arrivalTo) )]}
        for _, value in pattern_dict.items():
            actual_start = value[0][-2]
            start_time = start_time.replace(year= actual_start.year, month=actual_start.month, day=actual_start.day)
            actual_end = value[-1][-1]

            
            # Total travel time is rounded down to nearest minute
            totalTime = (actual_end - start_time).total_seconds()/60
            total_times.append(totalTime)

            # Store each departure and arrival for the trip pattern in a list
            legTime = []
            for v in value:
                legTime.append(v[2])
                legTime.append(v[3])

            # calculate time of each leg in trip patters (including waiting legs)
            leg_times.append(list(zip(legTime, legTime[1:])))
        
        departure_time = expected_start_time.replace(year= start_time.year, month=start_time.month, day=start_time.day)
        scheduled_total_time = get_scheduled_total_time(trip_pattern, departure_time, transfer_buffer, all_bus_lines_dict).total_seconds()/60


        if len(total_times) > 30:
            end_to_end_trip_time_data = list(map(lambda l: list(map(lambda tup: (tup[1] - tup[0]).total_seconds() // 60, l[1::2])), leg_times))
            data = total_times
            median = np.nanmedian(data)
            mean = np.nanmean(data)
            if mean > 120:
                print("Dropped plot: median time > 120 minutes")
                continue

            departure_csv.append(departure_time.strftime("%H:%M"))
            for p in percentiles:
                x_percentile = np.percentile(total_times, p)
                percentile_csv = save_to_csv.get(p, [])
                percentile_csv.append(x_percentile)
                save_to_csv.update({p : percentile_csv})

            median_wait = np.nanmedian(end_to_end_trip_time_data)
            mean_wait = np.nanmean(end_to_end_trip_time_data)
            
            combined_data.extend(data)
            combined_end_to_end.extend(end_to_end_trip_time_data)

            counts = Counter(data)
            total = len(data)

            x = sorted(counts.keys())
            cum = 0
            y = []
            for time in x:
                cum += counts[time] 
                y.append(cum / total)

            combined_plot_xy.append((x, y))

            #Individual plot
            plt.figure()
            plt.scatter(x, y, color = cmap(i), marker="x", label="Actual total time")
            plt.axvline(scheduled_total_time, color='k', linestyle='--', linewidth=2, label="Scheduled total time")
            plt.xlabel("Total time (minutes)")
            plt.ylabel("P(X ≤ total time)")
            plt.title(f"CDF: {from_to} Pattern: {"->".join(trip_string)}\n Expected Start Time: {expected_start_time.time()}")
            #dummy plot to add text to legend
            plt.plot([], [], ' ', label=f"Mean total time: {mean:.1f}\nMedian total time: {median:.1f}\nMean wait time: {mean_wait:.1f}\nMedian wait time: {median_wait:.1f}\nData points: {len(total_times)}\nScheduled total time: {scheduled_total_time:.1f}")
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            plt.grid(True)
            plt.ylim(0, 1)
            plt.yticks([0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
            plt.xlim(0, 50)
            plt.xticks(range(0,50,10))
            plt.tight_layout()
            if save_location:
                plt.savefig(f'{save_location}/CDF_{expected_start_time.time()}_{"-".join(save_name)}.pdf')
            #plt.show()
            plt.close()
        else:
            print(f"Dropped plot for: {departureTime}, less than 30 data points")

    # ===================================
    #   save percentiles to csv file
    save_to_csv.update({"Departure" : departure_csv})

    df_to_csv = pd.DataFrame(save_to_csv)
    df_to_csv.to_csv(f"./csv-3/{"-".join(save_name)}.csv")
    # ===================================

    for i, (x, y) in enumerate(combined_plot_xy):

        #Combined plot
        plt.plot(x, y, color = cmap(i))

    plt.xlabel("Total time (minutes)")
    plt.ylabel("P(X ≤ total time)")
    plt.title(f"CDF: {from_to} Pattern: {"->".join(trip_string)}")
    median = np.nanmedian(combined_data)
    mean = np.nanmean(combined_data)
    median_wait = np.nanmedian(combined_end_to_end)
    mean_wait = np.nanmean(combined_end_to_end)
    plt.text(x=51, y=0.4, s=f"Mean total time: {mean:.1f}\nMedian total time: {median:.1f}\nMean waiting time: {mean_wait:.1f}\nMedian waiting time: {median_wait:.1f}")
    plt.subplots_adjust(right=0.75)
    plt.grid(True)
    plt.ylim(0, 1)
    plt.yticks([0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
    plt.xlim(0, 50)
    plt.xticks(range(0,50,10))
    plt.tight_layout()
    if save_location:
        plt.savefig(f'{save_location}/CDF_combined_{"-".join(save_name)}.pdf')
    #plt.show()
