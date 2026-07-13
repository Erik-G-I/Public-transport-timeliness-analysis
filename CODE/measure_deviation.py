# import libraries and methods
from typing import cast, Any
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

def measure_deviation_from_planned_time(line_dataframe:pd.DataFrame):
    """
    Measures the deviation from the planned departure time for all stops on the line in both directions.
    
    :param line_dataframe: DataFrame of the line data
    :type line_dataframe: pd.DataFrame

    :returns: Dictionary: A dictionary containing all stops in each direction mapped to a list of the calculated deviations

    """

    deviations = {}

    directions = line_dataframe["Retning"].dropna().unique()
    for dir in directions:
        stops = line_dataframe[line_dataframe["Retning"]==dir]["HoldeplassTilNavn"].dropna().unique()
        for stop in stops:
            seqs = line_dataframe[(line_dataframe["HoldeplassTilNavn"]==stop)& (line_dataframe["Retning"] == dir)]["SekvensHoldeplassTil"].unique()
            val = []
            for seq in seqs:
                key = (dir, stop, seq)
                deviations[key] = val

    avg1 = []
    avg2 = []
    for direction, stop, seq in deviations.keys():
        df = line_dataframe[(line_dataframe["HoldeplassTilNavn"] == stop) & (line_dataframe["Retning"] == direction) & (line_dataframe["SekvensHoldeplassTil"]==seq)]
        # planned_times = df["AvgangstidPlanlagt"].to_numpy()
        # actual_times = df["AvgangstidFaktisk"].to_numpy()
        planned_times = df['AnkomstHoldeplassTilPlanlagt'].to_numpy()
        actual_times = df['AnkomstHoldeplassTilFaktisk'].to_numpy()
        
        diff = (actual_times - planned_times)/np.timedelta64(1, "m")
        cleaned_diff = pd.Series(diff).dropna().values
        if direction == 1:
            avg1.extend(cleaned_diff)
        else:
            avg2.extend(cleaned_diff)
        deviations[(direction, stop, seq)] = cleaned_diff

    
    deviations[(1, "line_avg", 0)] = avg1
    if len(avg2) > 0:
        deviations[(2, "line_avg", 0)] = avg2
   
    return deviations


def plot_deviation(deviation_dict:dict, line:str, save_location:str):
    """
    :param deviation_dict: Dictinary containing measured deviations for each stop on a line
    :type deviation_dict: Dictionary
    :param line: The line to plot
    :type line: String
    :param save_location: String representation of the location to save plots
    :type save_location: String

    :returns: None: Saves plots to save_location 
    """

    keys = deviation_dict.keys()

    for key in keys:
        data = deviation_dict[key]
        direction = key[0]
        stop_name = key[1]
        if "." in stop_name:
            stop_name = stop_name.replace(".", "")
        sequence = key[2]

        var = np.var(data)
        mean = np.mean(data)
        median = np.median(data)
        n = len(data)
        data_array = np.asarray(data)
        inside_range = np.logical_and(data_array >= -1, data_array <= 3)
        percentage = (np.sum(inside_range) / n) * 100
        bin_width = 1
        print("plotting:", direction, stop_name, sequence)
        minimum = min(data)//bin_width
        maximum = -((max(data) + bin_width)// -bin_width)
        bin_edges = np.arange(minimum, maximum, bin_width)
        
        counts, bins, patches_raw = plt.hist(data, bins=bin_edges, density=True, edgecolor='black', linewidth=1, align="mid")
        # 3. Iterate through each patch (bar) and set its color based on the bin position
        patches = cast(list[Any], patches_raw)
        for i in range(len(patches)):
            # Calculate the midpoint of the current bin to determine its position
            bin_center = (bins[i] + bins[i+1]) / 2
                    
            if bin_center < -1:
                patches[i].set_facecolor('red')
            elif -1 <= bin_center <= 3:
                patches[i].set_facecolor('blue')
            else:
                patches[i].set_facecolor('red')

        plt.text(x=0.60, y=0.60, s=f"variance: {var:.1f}\nmean: {mean:.1f}\nmedian: {median:.1f}\nOn-time: {percentage:.1f}%\nN: {n}", transform=plt.gca().transAxes, fontsize="x-large")
        plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
        plt.title(label=f"Line {line}: {stop_name}, direction {direction}")
        plt.xlim(-5,15)
        plt.xticks(range(-2, 16, 2))
        plt.xlabel("Deviation in minutes")
        plt.ylabel("% of all departures")
        plt.savefig(f'{save_location}/direction_{direction}/{line}_{sequence}_{stop_name}_dir{direction}')
        # plt.show()
        plt.close()

    return None