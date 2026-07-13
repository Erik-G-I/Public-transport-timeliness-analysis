#%%
from cdfFromTripPattern import plot_cdf_for_trip_patterns, clean_dataset
from measure_deviation import measure_deviation_from_planned_time, plot_deviation
import pandas as pd
import itertools
import threading
import time
import sys

# TRIP PATTERN TO ANALYZE
# Needs to be a feasible trip, and on the format: [[{expectedStartTime, expectedEndTime, line, fromPlace, toPlace}, {...}],[...]]
# More trip patterns are found in TRIP_PATTERNS.txt
TRIP_PATTERN = [[{'expectedStartTime': '08:13:00', 'expectedEndTime': '08:19:00', 'line': '12', 'fromPlace': 'Florida', 'toPlace': 'Langhaugen'}, {'expectedStartTime': '08:22:00', 'expectedEndTime': '08:28:00', 'line': '6/20', 'fromPlace': 'Langhaugen', 'toPlace': 'Mannsverk'}, {'expectedStartTime': '08:35:00', 'expectedEndTime': '08:41:00', 'line': '81', 'fromPlace': 'Mannsverk', 'toPlace': 'Nattlandsfjellet'}], [{'expectedStartTime': '16:02:00', 'expectedEndTime': '16:12:00', 'line': 'walk', 'fromPlace': 'Florida', 'toPlace': 'Krohnsminde'}, {'expectedStartTime': '16:12:00', 'expectedEndTime': '16:22:00', 'line': '20', 'fromPlace': 'Krohnsminde', 'toPlace': 'Mannsverk'}, {'expectedStartTime': '16:35:00', 'expectedEndTime': '16:41:00', 'line': '81', 'fromPlace': 'Mannsverk', 'toPlace': 'Nattlandsfjellet'}]] 


# UNIQUE DEPARTURE TIMES FROM STARTING PLACE
# Must be a list of string, representing time stamps on the format: 'hh:mm:ss'
# Departure times for certain lines can be found in DEPARTURE_TIMES_FROM_START.txt
DEPARTURE_TIMES_FROM_START = [ ['06:17:00', '06:27:00', '06:37:00', '06:47:00', '06:57:00', '07:18:00','07:28:00','07:38:00','07:48:00','07:58:00','08:08:00','08:18:00','08:28:00','08:38:00','08:48:00','08:58:00','09:08:00','09:18:00','09:38:00','10:03:00','10:23:00','10:43:00','11:03:00','11:23:00','11:43:00','12:03:00','12:23:00','12:43:00','13:03:00','13:23:00','13:43:00','14:03:00','14:18:00','14:28:00','14:38:00','14:48:00','14:58:00','15:08:00','15:18:00','15:28:00','15:38:00','15:48:00','15:58:00','16:08:00','16:18:00','16:28:00','16:38:00','16:48:00','17:08:00','17:33:00','17:53:00','18:13:00','18:33:00','18:53:00','19:13:00','19:33:00','19:53:00', '20:13:00', '20:33:00', '20:53:00', '21:13:00', '21:28:00', '21:58:00', '22:28:00', '22:58:00', '23:28:00', '23:57:00','00:27:00','00:57:00'], ['06:13:00', '06:33:00', '06:48:00', '07:03:00', '07:19:00', '07:29:00', '07:39:00', '07:49:00', '08:04:00', '08:18:00', '08:33:00', '08:48:00', '09:02:00', '09:17:00', '09:32:00', '09:47:00', '10:02:00', '10:17:00', '10:32:00', '10:47:00', '11:02:00', '11:17:00', '11:32:00', '11:47:00', '12:02:00', '12:17:00', '12:32:00', '12:47:00', '13:02:00', '13:18:00', '13:33:00', '13:48:00', '14:03:00', '14:18:00', '14:34:00', '14:49:00', '15:04:00', '15:19:00', '15:34:00', '15:49:00', '16:04:00', '16:18:00', '16:33:00', '16:48:00', '17:03:00', '17:33:00', '18:03:00', '18:33:00', '19:03:00', '19:29:00', '19:59:00', '20:29:00', '20:59:00', '21:29:00', '21:59:00', '22:29:00', '22:59:00', '23:29:00', '00:29:00']]



# TRANSFER BUFFER IS AN ARBITRARY INTEGER TO ADD SLACK (IN MINUTES) BETWEEN BUS CHANGES
# Standard is set to 2 (two minutes)
TRANSFER_BUFFER = 2     

# PATH TO SAVE LOCATION WHERE PLOTS ARE TO BE SAVED (SHOULD BE AN APTLY NAMED FOLDER):
# Leave empty or None if you dont want to save the plots
SAVE_LOCATION = [None, None]

#%%
# FOR CLEANING THE DATASET:

USECOLS = ['Rute', 'DriftsDato', 'Ukedag', 'SekvensHoldeplassFra', 'HoldeplassFraNavn', 'AvgangstidPlanlagt', 'AvgangstidFaktisk', 'SekvensHoldeplassTil', 'HoldeplassTilNavn', 'AnkomstHoldeplassTilPlanlagt', 'AnkomstHoldeplassTilFaktisk', 'Retning', 'TurID']
DTYPES = {'Rute': str, 'DriftsDato': str,  'Ukedag': str, 'SekvensHoldeplassFra': pd.Int8Dtype(), 'HoldeplassFraNavn': str,  'AvgangstidPlanlagt': str, 'AvgangstidFaktisk': str, 'SekvensHoldeplassTil': pd.Int8Dtype(), 'HoldeplassTilNavn': str, 'AnkomstHoldeplassTilPlanlagt': str, 'AnkomstHoldeplassTilFaktisk': str, 'Retning': pd.Int8Dtype(), 'TurID': pd.Int32Dtype()}
PATH_TO_DATASET = ["./DATASETS/20250505_BS_202411-202505.csv", "./DATASETS/20250505_6_81_202411-202505.csv"]
NATIONAL_HOLIDAYS = ["-12-24 00:00:00", "-12-25 00:00:00", "-12-26 00:00:00", "-12-27 00:00:00", "-12-28 00:00:00", "-12-29 00:00:00", "-12-30 00:00:00", "-12-31 00:00:00","-01-01 00:00:00","-04-16 00:00:00", "-04-17 00:00:00", "-04-18 00:00:00", "-04-19 00:00:00", "-04-20 00:00:00", "-04-21 00:00:00"]

# The days affected by the schedule change for Line 81:
schedulechange81 = ["-03-01 00:00:00","-03-02 00:00:00","-03-03 00:00:00","-03-04 00:00:00","-03-05 00:00:00","-03-06 00:00:00","-03-07 00:00:00","-03-08 00:00:00","-03-09 00:00:00","-03-10 00:00:00","-03-11 00:00:00","-03-12 00:00:00","-03-13 00:00:00","-03-14 00:00:00","-03-15 00:00:00","-03-16 00:00:00","-03-17 00:00:00","-03-18 00:00:00","-03-19 00:00:00","-03-20 00:00:00","-03-21 00:00:00","-03-22 00:00:00","-03-23 00:00:00","-03-24 00:00:00","-03-25 00:00:00","-03-26 00:00:00","-03-27 00:00:00","-03-28 00:00:00","-03-29 00:00:00","-03-30 00:00:00","-03-31 00:00:00","-04-01 00:00:00","-04-02 00:00:00","-04-03 00:00:00","-04-04 00:00:00","-04-05 00:00:00","-04-06 00:00:00","-04-07 00:00:00","-04-08 00:00:00","-04-09 00:00:00","-04-10 00:00:00","-04-11 00:00:00","-04-12 00:00:00","-04-13 00:00:00","-04-14 00:00:00","-04-15 00:00:00","-04-16 00:00:00","-04-17 00:00:00","-04-18 00:00:00","-04-19 00:00:00","-04-20 00:00:00","-04-21 00:00:00","-04-22 00:00:00","-04-23 00:00:00","-04-24 00:00:00","-04-25 00:00:00","-04-26 00:00:00","-04-27 00:00:00","-04-28 00:00:00","-04-29 00:00:00","-04-30 00:00:00","-04-31 00:00:00"] 

# Days to use when testing trip patterns after 81 schedule change:
#NATIONAL_HOLIDAYS = ["-03-01 00:00:00","-03-02 00:00:00","-03-03 00:00:00","-03-04 00:00:00","-03-05 00:00:00","-03-06 00:00:00","-03-07 00:00:00","-03-08 00:00:00","-03-09 00:00:00","-03-10 00:00:00","-03-11 00:00:00","-03-12 00:00:00","-03-13 00:00:00","-03-14 00:00:00","-03-15 00:00:00","-03-16 00:00:00","-03-17 00:00:00","-03-18 00:00:00","-03-19 00:00:00","-03-20 00:00:00","-03-21 00:00:00","-03-22 00:00:00","-03-23 00:00:00","-03-24 00:00:00","-03-25 00:00:00","-03-26 00:00:00","-03-27 00:00:00","-03-28 00:00:00","-03-29 00:00:00","-03-30 00:00:00","-03-31 00:00:00","-04-01 00:00:00","-04-02 00:00:00","-04-03 00:00:00","-04-04 00:00:00","-04-05 00:00:00","-04-06 00:00:00","-04-07 00:00:00","-04-08 00:00:00","-04-09 00:00:00","-04-10 00:00:00","-04-11 00:00:00","-04-12 00:00:00","-04-13 00:00:00","-04-14 00:00:00","-04-15 00:00:00","-04-16 00:00:00","-04-22 00:00:00","-04-23 00:00:00","-04-24 00:00:00","-04-25 00:00:00","-04-26 00:00:00","-04-27 00:00:00","-04-28 00:00:00","-04-29 00:00:00","-04-30 00:00:00","-04-31 00:00:00"] 

NATIONAL_HOLIDAYS.extend(schedulechange81)
def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        sys.stdout.write('\rrunning script ' + c)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\rDone!')

DATASET = clean_dataset(USECOLS, DTYPES, PATH_TO_DATASET, NATIONAL_HOLIDAYS)

#%%
DEVIATION_SAVE_LOCATION = "path/to/save/location"

#PLOT DEVIATION FROM SCHEDULE:
for line in DATASET["Rute"].unique():
    print(line)
    if(line == "310"): # Line 310, created some unsolved problems when plotting deviations
        print("skipping",line)
        continue
    devs = measure_deviation_from_planned_time(DATASET[DATASET["Rute"] == line])
    
    plot_deviation(devs, line, f"{DEVIATION_SAVE_LOCATION}/{line}")
#%%
#PLOT CDFS
# if __name__ == "__main__":
print("Starting ...")
done = False
start = time.time()
t = threading.Thread(target=animate)
t.start()
N = len(TRIP_PATTERN)
for i in range(N):
    plot_cdf_for_trip_patterns(TRIP_PATTERN[i], DEPARTURE_TIMES_FROM_START[i], TRANSFER_BUFFER, SAVE_LOCATION[i], DATASET)

done = True
print("--- %s seconds ---" % (time.time() - start))
