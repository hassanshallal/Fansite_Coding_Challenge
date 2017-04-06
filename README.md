# Table of contents:
1. [Summary](README.md#Summary)
2. [Necessary libraries](README.md#Necessary-libraries)
3. [Reading and preprocessing input log.txt files](README.md#Reading-and-preprocessing-input-.txt-file)
4. [Implementing Feature-1](README.md#Implementing-Feature-1)
5. [Implementing Feature-2](README.md#Implementing-Feature-2)
6. [Implementing Feature-3](README.md#Implementing-Feature-3)
7. [Implementing Feature-4](README.md#Implementing-Feature-4)


## Summary
This is my submission to the Insight coding challenge described in details here: https://github.com/InsightDataScience/fansite-analytics-challenge

The input log.txt can be dowanloaded from here: https://drive.google.com/file/d/0B7-XWjN4ezogbUh6bUl1cV82Tnc/view

## Necessary libraries

The current data pipeline was implemented in python and relied heavily on the following libraries:

1) pandas
2) numpy
3) datetime
4) operator
5) sys

## Reading and preprocessing input log.txt file

The preprocessing step is pretty straightforward. Pandas dataframe allows us to get in control of the dataset and choose the  best execution strategy. 

Important note: The following lines were skipped by pandas read_table due to inconsistent number of fields:
306430, 306916, 306999, 307159, 1205663, 1956694, 2347209, 2447899, 2573753, 3014150, 3156351, 3518321, 3518597, 3596996

Some of the skipped lines may affect the final output of the analysis. A more robust reading pipeline is definitely an area for improvement of the current  approach.

The log.txt input file recoded over 4.4 million cases of interaction with NASA fans website and it is about 447 MB on disk. Preprocessing this input file and  outputting a dataframe ready for further analysis consumed around 90-120 seconds. It is noteworthy that this dataset spanned across a period of 27 and a half  days.

## Implementing Feature-1

The task at hand is to list the top 10 most active host/IP addresses that have accessed the site during the entire interval. This is a pretty straightforward implementation utilizing pandas' value_counts() method which evaluates directly to the required feature-1 output.

The entire input was processed to produce feature-1 in less than 10 seconds.

## Implementing Feature-2

The task here is to identify the 10 resources that consume the most bandwidth on the site. In order to compute the total bytes communicated through a given resource, summation of the bytes over all the incidents of this resource was critical. In order to complete this computation in a reasonable time, numpy arrays were created from the respective columns in the base dataframe and an empty dictionary was initialized. The keys in the dictionary represent the resources and the respective values are the total byte.

The logic is to loop through all the cases for one time, check if the resource is a key in the dictionary or not, if it is not a key, we create a new key and initialize it with the respective byte value, if it is already a key in the dictionary, then we  sum the byte of the new case to the value of the same resource key. At the end, we transform the dictionary in to a list, sort  it, and then write the output file.

The entire input of 27 and a half days was processed to produce feature-2 in about 10-15 seconds.


## Implementing Feature-3

This feature's task is to find the top 10 busiest 60-minute intervals. The implementation of this feature can be explained by the following points:

1) First, we needed to compute the number of clicks for every unique timestamp in the dataset. We applied the efficient value_counts() method on the timestamp column in the dataframe. This method returns an unordered series which we convert into an easy to sort list of tuples.

2) Second, we have to consider intervals of inactivity or no clicks. For that purpose, we initialize two all-zeroes lists:

        First-list: date_range_by_second which has an index for every single second in the total time interval of the dataset irrelevant to whether there was any activity during this second or not.

        Second-list: clicks_at_every_second which represents the activity or number of clicks per second. 

    All indices of the clicks_at_every_second list are initialized to zero and then populated accordingly from total_clicks_per_timestamp we obtained from the first step above. We also needed to pad clicks_at_every_second with an extra hour in order to facilitate the next phase of computing hourly cumulative clicks for the last second in our real dataset.

3) Third, we convert clicks_at_every_second into an np.array in order to facilitate cumulative sums over 3600 seconds. We computed the cumulative clicks for the first second as a base case. Then we implement a fast algorithm for computing that values at every index of the hourly_cumulative_clicks using this self explanatory formula:

##### hourly_cumulative_clicks[n] = hourly_cumulative_clicks[n-1] - clicks_at_every_second[n-1] + clicks_at_every_second[n + 3599]

Lastly and before we generate hours.txt output, we zip date_range_by_second and hourly_cumulative_clicks in order to facilitate sorting and locating the busiest        10 hours.

Feature-3 consumed around 40 seconds to process the entire input of more than 27 days.


## Implementing Feature-4

Feature-4 is expected to detect whether someone who failed to login from the same IP three consecutive time over 20 seconds was NOT blocked of the site for the  next 5 minutes, in other words, feature-4 is supposed to catch security breaches. Please refer to the website of the challenge for further information and more detailed expalnation of this feature. You can also explore the illustration in the images folder.

Feature-4 was implemented in two phases:

    **Phase-1**: phase_1_blocked_assessment function locates and outputs any case in which the same host attemped to login and failed for three consecutive times in an interval of 20 seconds. 

    **Phase-2**: using the output of phase-1, phase_2_blocked_assessment function reports any breach in which a case that was detected in phase-1 was not blocked  by the site in the next five minutes.

Feature-4 was the slowest among all the implemented features and it processed the input of more than 27 days in less than 10 minutes.


## System information:

import platform

platform.uname()

('Darwin',
'MacBook-Air',
'16.4.0',
'Darwin Kernel Version 16.4.0: Thu Dec 22 22:53:21 PST 2016; root:xnu-3789.41.3~3/RELEASE_X86_64',
'x86_64',
'i386')

In case you have any question, please contact me at hshallal@icloud.com. 
