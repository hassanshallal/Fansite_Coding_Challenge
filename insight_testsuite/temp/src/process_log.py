# Import modules

import pandas as pd
import numpy as np
import datetime
from operator import itemgetter, attrgetter
import re
import sys

# Define command line arguments
input_file = sys.argv[1]
host_output = sys.argv[2]
resources_output = sys.argv[3]
hours_output = sys.argv[4]
blocked_output = sys.argv[5]


# Preprocessing

def read_clean_preprocess(file):
    
    print "Reading and preprocessing data started at" + " " + str(datetime.datetime.now())

    df = pd.read_table(file, header = None, error_bad_lines = False, warn_bad_lines = True)
    df.columns = ['line']
    df = df['line'].str[0:].str.split(' ', expand = True)
    df = df.ix[:,[0,1,2,3,4,5,6,7,8,9]]
    df = df.drop(1, axis=1)
    df = df.drop(2, axis=1)
    df[3] = df[3].str.replace('[', '')
    df[4] = df[4].str.replace(']', '')
    df[5] = df[5].str.replace('"', '')
    df[6] = df[6].str.replace('"', '')
    df[7] = df[7].str.replace('"', '')
    
    df.loc[df[9] ==  '-', 9] = '0'
    df.loc[df[9] ==  '', 9] = '0'
    
    df = df.fillna(0)
    
    df.columns = ['host', 'datetime', 'timezone', 'is_sent',  'resource', 'protocol', 'http', 'byte']
    df['timestamps'] = pd.Series(pd.to_datetime(df['datetime'], format='%d/%b/%Y:%H:%M:%S'), index=df.index)
    print 'Preprocessing the input was performed at ' + str(datetime.datetime.now())
    return df

df = read_clean_preprocess(input_file)



# Feature-1: hosts
def get_hosts(df):
    hosts = df['host'].value_counts()
    if len(hosts) > 10:
        hosts1 = hosts[0:10]
        hosts1.to_csv(sys.argv[2], header = None, index = True, sep=',', mode='w')
    else:
        hosts.to_csv(sys.argv[2], header = None, index = True, sep=',', mode='w')

    print 'hosts.txt was written at ' + str(datetime.datetime.now())


get_hosts(df)


# Feature-2: resources

def get_resources(df):
    
    # This is a dictionary based method that faciliatates fast generation of the output!
    resource_array = {}
    
    ##  These are arrays that are fast to access and get values
    resource = np.array(df['resource'])
    byte = np.array(df['byte'], dtype = 'int64')

    for n in range(0, len(resource)):
        if resource[n] not in resource_array:
            resource_array[resource[n]] = byte[n]

        else:
            resource_array[resource[n]] += byte[n]


    bandwidth_consumption = [(k, v) for k, v in resource_array.iteritems()]
    bandwidth_consumption.sort(key = itemgetter(1), reverse = True)
    
    with open(sys.argv[3], "w") as resources_output:
        if len(bandwidth_consumption) > 10:
            resources_output.write(''.join(str(t[0]) + '\n' for t in bandwidth_consumption[0:10]))
        else:
            resources_output.write(''.join(str(t[0]) + '\n' for t in bandwidth_consumption))


    print 'resources.txt was written at ' + str(datetime.datetime.now())
    # return bandwidth_consumption

get_resources(df)




# Feature-3: hours

def get_hours(df):
    '''
    First, we need to compute the number of clicks for every unique timestamp in the dataset.
    We can use efficient value_counts() method but it returns an unordered series which
    we convert into an easy to sort list of tuples.
    '''
    total_clicks_per_timestamp = df['timestamps'].value_counts(sort = False)
    total_clicks_per_timestamp = [(k, v) for k, v in total_clicks_per_timestamp.iteritems()]
    total_clicks_per_timestamp.sort(key = itemgetter(0))


    '''
    Second, we have to consider intervals of inactivity or no clicks. We create two lists:
    1) date_range_by_second which has an index for every single second in the total time interval of the dataset
    2) clicks_at_every_second which represents the activity or number of clicks per second. This
    list is all initialized to zero and then populated accordingly from total_clicks_per_timestamp
    We also need to pad clicks_at_every_second with an extra hour in order to facilitate the next
    phase of computing hourly cumulative clicks for the last second in our real dataset.
    '''

    date_range_by_second = pd.date_range(start = total_clicks_per_timestamp[0][0], end = total_clicks_per_timestamp[len(total_clicks_per_timestamp)-1][0], freq='S')
    clicks_at_every_second = [0] * len(date_range_by_second)
    clicks_at_every_second.extend([0] * (3599))

    for n in range(0, len(total_clicks_per_timestamp)):
        index_of_click_date = date_range_by_second.slice_locs(start = total_clicks_per_timestamp[n][0])[0]
        clicks_at_every_second[index_of_click_date] += total_clicks_per_timestamp[n][1]

    '''
    Third, we convert clicks_at_every_second into an np.array in order to facilitate cumulative sums
    We compute the cumulative clicks for the first second.
    Then we implement a fast algorithm for computing that value at every index of hourly_cumulative_clicks
    using this self-explanatory formula:
    hourly_cumulative_clicks[n] = hourly_cumulative_clicks[n-1] - 
                                  clicks_at_every_second[n-1] +
                                  clicks_at_every_second[n + 3599]
    Lastly and before we generate hours.txt output, we zip date_range_by_second and hourly_cumulative_clicks
    in order to facilitate sorting and locating the busiest 10 hours
    '''
    clicks_at_every_second = np.array(clicks_at_every_second)

    hourly_cumulative_clicks = [0] * len(date_range_by_second)
    hourly_cumulative_clicks[0] = np.sum(clicks_at_every_second[0:3599], axis=0)


    for n in range(1, len(hourly_cumulative_clicks)):
            hourly_cumulative_clicks[n] = hourly_cumulative_clicks[n-1] - clicks_at_every_second[n-1] + clicks_at_every_second[n+3599]


    hourly_cumulative_clicks = zip(date_range_by_second, hourly_cumulative_clicks)
    hourly_cumulative_clicks.sort(key = itemgetter(1), reverse = True)

    with open(sys.argv[4], "w") as hours_output:
        for n in range(0, 10):
            line = hourly_cumulative_clicks[n][0]
            line = line.strftime('%d/%b/%Y:%H:%M:%S')
            line = line + ' -0400,' + str(hourly_cumulative_clicks[n][1])
            hours_output.write(line + '\n')

    print 'hours.txt was written at ' + str(datetime.datetime.now())

get_hours(df)


# Feature-4

def process_dict_into_sorted_lists(input_dict, sorting_index):
    
    output_list = [(k, v) for k, v in input_dict.iteritems()]
    output_list.sort(key = itemgetter(sorting_index))
    indices, output_array = map(list,zip(*output_list))
    return output_array


def phase_1_blocked_assessment(df):
    ## used to be called collect_three_cons_failed_attempts_same_host_within_twenty_sec


    failed_login_df = df[(df['resource'] ==  '/login') & (df['http'] != 200)][['host', 'timestamps']]
    df.sort_values(['host', 'timestamps'], inplace = True, ascending = True)  
    
    ## We need to work with arrays cause it is much faster than working with dataframes
    host_array = np.array(failed_login_df['host'], dtype = str)
    timestamps_array = np.array(failed_login_df['timestamps'], dtype = 'datetime64[ns]')
    timestamps_tsl_array = np.array(failed_login_df['timestamps'] + pd.Timedelta('20 seconds'), dtype = 'datetime64[ns]')
    
    ## We need empty dictionaries to retrieve the most important information
    three_consecutive_failures_host = {}
    third_consecutive_failures_timestamps = {}
    
    for n in range(0, failed_login_df.shape[0]-3):
        if (host_array[n] == host_array[n+1] and
            host_array[n+1] == host_array[n+2] and
            timestamps_array[n+2] < timestamps_tsl_array[n]):
            
            three_consecutive_failures_host[n+2] = host_array[n+2]
            third_consecutive_failures_timestamps[n+2] = timestamps_array[n+2]
    

    ## Now, we process the dictionaries in order to have a neat output
    host = process_dict_into_sorted_lists(three_consecutive_failures_host, 0)
    timestamps = process_dict_into_sorted_lists(third_consecutive_failures_timestamps, 0)
            
    phase_1_output = pd.DataFrame({'host': host,'timestamps': timestamps })
    
    print 'Phase-1 assessment of feature-4 (blocked.txt) is completed at ' + str(datetime.datetime.now()) + ' and the number of cases with three comsecutive failures within 20 seconds is' + str(phase_1_output.shape[0])
    return phase_1_output

phase_1_output = phase_1_blocked_assessment(df)


def phase_2_blocked_assessment(df, phase_1_output_df):
    
    ## Lists for efficient comparison
    timestamps_array = phase_1_output_df['timestamps']
    host_array = phase_1_output_df['host']
    
    ## Initialize a dataframe for the sought after cases, we Initialize manually on the first case and exclude it from the for loop, sort of bottom-up approach!
    use_attempt_five_min = df[(df["host"] ==  host_array[0]) & 
                           (df['timestamps'] > timestamps_array[0]) &
                           (df['timestamps'] <= timestamps_array[0] + pd.Timedelta('300 seconds'))]
    
    ## initiate sets to faciliate search
    host_set = set(use_attempt_five_min["host"])
    timestamps_set = set(use_attempt_five_min['timestamps'])
    
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
                        str(use_attempt_five_min.iloc[m]['is_sent']) + ' ' + 
                        str(use_attempt_five_min.iloc[m]['resource']) +  ' ' + 
                        str(use_attempt_five_min.iloc[m]['protocol']) + '" ' + 
                        str(use_attempt_five_min.iloc[m]['http']) +  ' ' +  
                        str(use_attempt_five_min.iloc[m]['byte']))               
                blockedOutput.write(line + '\n')
    print 'blocked.txt was  written at ' + str(datetime.datetime.now()) + ' and the number of detected cases is ' + str(use_attempt_five_min.shape[0])
    #return use_attempt_five_min

phase_2_blocked_assessment(df, phase_1_output)
