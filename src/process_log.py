# Import modules

import pandas as pd
import numpy as np
import datetime
from operator import itemgetter, attrgetter
import sys



# Define command line arguments

input_file = sys.argv[1]
host_output = sys.argv[2]
resources_output = sys.argv[3]
hours_output = sys.argv[4]
blocked_output = sys.argv[5]
verbose = sys.argv[6]



# Preprocessing

def read_clean_preprocess(file):
    
    if sys.argv[6]:
        print "Reading and preprocessing data started at" + " " + str(datetime.datetime.now())

    # Read the input and specify " " as a separator between the different fields
    df = pd.read_table(file, header = None, sep = " ", error_bad_lines = False, warn_bad_lines = False)
    
    # Drop irrelevant columns
    df = df.drop(1, axis=1)
    df = df.drop(2, axis=1)
    
    # Do some cleaning
    df[3] = df[3].str.replace('[', '')
    df[4] = df[4].str.replace(']', '')
    
    # Split total resource into is_sent, resource, and protocol
    df = df.join(df[5].str.split(' ', 1, expand = True).rename(columns={0:'is_sent', 1:'resource_protocol'}))
    df = df.join(df['resource_protocol'].str.split(' ', 1, expand = True).rename(columns={0:'resource1', 1:'protocol'}))
    
    # Give final names to the columns, these names will be used throughout the rest of the implementation
    df.columns = ['host', 'datetime', 'timezone', 'total_resource', "http", 'byte', 'is_sent', 'resource_protocol', 'resource', 'protocol']
    
    # Add a very critical timestamp column
    df['timestamps'] = pd.Series(pd.to_datetime(df['datetime'], format='%d/%b/%Y:%H:%M:%S'), index = df.index)

    # Print undates in case the user checks verbose as True in the run.sh script
    if sys.argv[6]:
        print 'Cleaning and organizing the input were done at ' + str(datetime.datetime.now())
    return df
    

# Run the preprocessing and name the output as df
df = read_clean_preprocess(input_file)



# Feature-1: hosts

def get_hosts(df):
    hosts = df['host'].value_counts()
    if len(hosts) > 10:
        hosts1 = hosts[0:10]
        hosts1.to_csv(sys.argv[2], header = None, index = True, sep=',', mode='w')
    else:
        hosts.to_csv(sys.argv[2], header = None, index = True, sep=',', mode='w')
    
    if sys.argv[6]:
        print 'hosts.txt was written at ' + str(datetime.datetime.now())


# Run Feature-1 using df as a solo input
get_hosts(df)



# Feature-2: resources

def get_resources(df):
    
    # This is a dictionary based method that allows fast execution.
    resource_array = {}
    
    ##  These are lists that are fast to access to get a given value
    resource = np.array(df['resource'])
    byte = np.array(df['byte'], dtype = 'int64')

    # Loop over all the resources in the resource list and populate the resource_array accordingly.
    for n in range(0, len(resource)):
        if resource[n] not in resource_array:
            resource_array[resource[n]] = byte[n]

        else:
            resource_array[resource[n]] += byte[n]

    # resource_array is a dictionary and can't be sorted. We make a list of tuples and sort it based on the byte values
    bandwidth_consumption = [(k, v) for k, v in resource_array.iteritems()]
    bandwidth_consumption.sort(key = itemgetter(1), reverse = True)
    
    # output
    with open(sys.argv[3], "w") as resources_output:
        if len(bandwidth_consumption) > 10:
            resources_output.write(''.join(str(t[0]) + '\n' for t in bandwidth_consumption[0:10]))
        else:
            resources_output.write(''.join(str(t[0]) + '\n' for t in bandwidth_consumption))

    if sys.argv[6]:
        print 'resources.txt was written at ' + str(datetime.datetime.now())
    #return bandwidth_consumption, if you want to look at.

# Run Feature-2 using df as a solo input
get_resources(df)



# Feature-3: hours

def get_hours(df):

    # First, we need to compute the number of clicks for every unique timestamp in the dataset.
    total_clicks_per_timestamp = df['timestamps'].value_counts(sort = False)
    total_clicks_per_timestamp = [(k, v) for k, v in total_clicks_per_timestamp.iteritems()]
    total_clicks_per_timestamp.sort(key = itemgetter(0))


    # Map total_clicks_per_timestamp into clicks_at_every_second including periods of inactivity
    date_range_by_second = pd.date_range(start = total_clicks_per_timestamp[0][0], end = total_clicks_per_timestamp[len(total_clicks_per_timestamp)-1][0], freq='S')
    clicks_at_every_second = [0] * len(date_range_by_second)
    clicks_at_every_second.extend([0] * (3599))

    for n in range(0, len(total_clicks_per_timestamp)):
        index_of_click_date = date_range_by_second.slice_locs(start = total_clicks_per_timestamp[n][0])[0]
        clicks_at_every_second[index_of_click_date] += total_clicks_per_timestamp[n][1]


    # Map clicks_at_every_second into hourly_cumulative_clicks. We use a simple formula along with different arrays in order to quickly and efficiently compute the hourly_cumulative_clicks.
    clicks_at_every_second = np.array(clicks_at_every_second)

    hourly_cumulative_clicks = [0] * len(date_range_by_second)
    hourly_cumulative_clicks[0] = np.sum(clicks_at_every_second[0:3599], axis=0)


    for n in range(1, len(hourly_cumulative_clicks)):
        hourly_cumulative_clicks[n] = hourly_cumulative_clicks[n-1] - clicks_at_every_second[n-1] + clicks_at_every_second[n+3599] # The most critical formula for feature-3

    # Most straightforward way to sort two lists together, zip and sort.
    hourly_cumulative_clicks = zip(date_range_by_second, hourly_cumulative_clicks)
    hourly_cumulative_clicks.sort(key = itemgetter(1), reverse = True)

    # output
    with open(sys.argv[4], "w") as hours_output:
        for n in range(0, 10):
            line = hourly_cumulative_clicks[n][0]
            line = line.strftime('%d/%b/%Y:%H:%M:%S')
            line = line + ' -0400,' + str(hourly_cumulative_clicks[n][1])
            hours_output.write(line + '\n')

    if sys.argv[6]:
        print 'hours.txt was written at ' + str(datetime.datetime.now())

# Run Feature-3 using df as a solo input
get_hours(df)



# Feature-4


# This is a helper function for converting a dictionary to a list and then sorting the list. This function helps keep the number of lines in phase_1_blocked_assessment under control.
def process_dict_into_sorted_lists(input_dict, sorting_index):
    
    output_list = [(k, v) for k, v in input_dict.iteritems()]
    output_list.sort(key = itemgetter(sorting_index))
    indices, output_array = map(list,zip(*output_list))
    return output_array


# This is phase-1 of feature-4. The goal of this phase is to locate and output any case in which the SAME host attemped to LOGIN and FAILED for THREE CONSECUTIVE times in 20 seconds.
def phase_1_blocked_assessment(df):
    
    # All right, we only need to focus on cases of users attempting to ligin, so, we subset the input dataframe to include only these cases.
    login_df = df[(df['resource'] ==  '/login')][['host', 'timestamps', 'http']]
    
    # We need to work with arrays cause it is much faster than working with dataframes. The following 4-arrays have similar indices to similar cases. This enables us to check several conditions simultaneously.
    http_array = np.array(login_df['http'], dtype = int)
    host_array = np.array(login_df['host'], dtype = str)
    timestamps_array = np.array(login_df['timestamps'], dtype = 'datetime64[ns]')
    timestamps_tsl_array = np.array(login_df['timestamps'] + pd.Timedelta('20 seconds'), dtype = 'datetime64[ns]') # tsl stands for 20 seconds limit!
    
    # We need empty dictionaries to retrieve the most important information; the host and the timestamp of his/her last/third consecutive failed login attempt in 20 seconds.
    three_consecutive_failures_host = {}
    third_consecutive_failures_timestamps = {}
    
    # We will crawl around every case of login and evaluate against all the conditions.
    for n in range(0, login_df.shape[0]-3):
        if (http_array[n] != 200 and
            http_array[n+1] != 200 and
            http_array[n+2] != 200 and
            host_array[n] == host_array[n+1] and
            host_array[n+1] == host_array[n+2] and
            timestamps_array[n+2] < timestamps_tsl_array[n]):
            
            three_consecutive_failures_host[n+2] = host_array[n+2]
            third_consecutive_failures_timestamps[n+2] = timestamps_array[n+2]

    # Now, we process the dictionaries using the helper function defined above in order to have a neat output
    host = process_dict_into_sorted_lists(three_consecutive_failures_host, 0)
    timestamps = process_dict_into_sorted_lists(third_consecutive_failures_timestamps, 0)
    
    # output
    phase_1_output = pd.DataFrame({'host': host,'timestamps': timestamps })
    
    if sys.argv[6]:
        print 'Phase-1 blocked assessment is completed at ' + str(datetime.datetime.now()) + ' and the dimensions of the phase_1_output are ' + str(phase_1_output.shape[0])
    return phase_1_output


# Run phase-1 of Feature-4 using df as a solo input
phase_1_output = phase_1_blocked_assessment(df)



def phase_2_blocked_assessment(df, phase_1_output_df):
    
    # Lists for efficient comparison
    timestamps_array = phase_1_output_df['timestamps']
    host_array = phase_1_output_df['host']
    
    
    # Initialize a dataframe for the sought after cases, we Initialize manually on the first case and exclude it from the for loop, sort of bottom-up approach! T
    use_attempt_five_min = df[(df["host"] ==  host_array[0]) &
                           (df['timestamps'] > timestamps_array[0]) &
                           (df['timestamps'] <= timestamps_array[0] + pd.Timedelta('300 seconds'))]
    
    # initiate empty sets to faciliate search, we won't use these sets for anything other than for searching and making sure we don't report similar breaches over and over again, so, instead of dictionaries, we just use sets.
    host_set = set(use_attempt_five_min["host"])
    timestamps_set = set(use_attempt_five_min['timestamps'])
    
    
    # Time for action, we now can use information we obtained from phase-1 in order to catch breaches, all of them, failed or successful login, login attempt of watching a movie, whatever the breach is, it can be retrieved from the original df using what we know now.
    for n in range(1, phase_1_output_df.shape[0]):
        
        ## We don't want to report redundant cases or repeat cases
        if (phase_1_output_df['host'][n] in host_set) and (phase_1_output_df['timestamps'][n] in timestamps_set):
            continue
            
        ## Here we just append to the initialized dataframe and update our search sets
        else:
            use_attempt_five_min = use_attempt_five_min.append(df[(df["host"] ==  host_array[n]) & 
                                                              (df['timestamps'] > timestamps_array[n]) &
                                                              (df['timestamps'] <= timestamps_array[n] + pd.Timedelta('300 seconds'))])



            host_set = set(use_attempt_five_min["host"])
            timestamps_set = set(use_attempt_five_min['timestamps'])

    ## Return the dataframe and/or write the output directly
    if use_attempt_five_min.shape[0] > 0:
        with open(sys.argv[5], "w") as blockedOutput:
            for m in range(0, use_attempt_five_min.shape[0]):
                line = (str(use_attempt_five_min.iloc[m]['host']) + ' - - [' +
                    str(use_attempt_five_min.iloc[m]['datetime']) + ' ' +
                    str(use_attempt_five_min.iloc[m]['timezone']) + '] "' +
                    str(use_attempt_five_min.iloc[m]['total_resource']) + '" ' +
                    str(use_attempt_five_min.iloc[m]['http']) +  ' ' +
                    str(use_attempt_five_min.iloc[m]['byte']))
                blockedOutput.write(line + '\n')
    

    if sys.argv[6]:
        print 'blocked.txt was  written at ' + str(datetime.datetime.now()) + ' and the number of detected cases is ' + str(use_attempt_five_min.shape[0])
    #return use_attempt_five_min

# Run phase-2 of Feature-4 using df and the output of phase-1
phase_2_blocked_assessment(df, phase_1_output)
