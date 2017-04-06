# Table of contents:
1. [Summary](README.md#Summary)
2. [Necessary libraries](README.md#Necessary-libraries)
3. [Reading and preprocessing input .txt file](README.md#Reading-and-preprocessing-input-.txt-file)
4. [Implementing Feature-1](README.md#Implementing-Feature-1)
5. [Implementing Feature-2](README.md#Implementing-Feature-2)
6. [Implementing Feature-3](README.md#Implementing-Feature-3)
7. [Implementing Feature-4](README.md#Implementing-Feature-4)


## Summary
This is my submission to the Insight coding challenge described in details here: https://github.com/InsightDataScience/fansite-analytics-challenge

The input log.txt can be dowanloaded from here: https://drive.google.com/file/d/0B7-XWjN4ezogbUh6bUl1cV82Tnc/view

## Necessary libraries

The current data pipeline was implemented in python and relied heavily on the following libraries:

#### pandas
#### numpy
#### datetime
#### operator
#### sys

## Reading and preprocessing input .txt file

The preprocessing step is pretty straightforward. Pandas dataframe allows us to get in control of the dataset and choose the 
best execution strategy. 

NB. The following lines were skipped by pandas read_table due to inconsistent number of fields:
306430, 306916, 306999, 307159, 1205663, 1956694, 2347209, 2447899, 2573753, 3014150, 3156351, 3518321, 3518597, 3596996

The log.txt input file recoded over 4.4 million lines and is about 447 MB on disk. Preprocessing this input file and outputting a dataframe ready for further analysis consumed around 90 seconds. This input spanned across a period of 27 and a hald days.

## Implementing Feature-1

The task at hand is to list the top 10 most active host/IP addresses that have accessed the site.
This is a pretty straightforward implementation utilizing pandas' value_counts() method which evaluates directly to the required feature-1 output.

The entire input was processed to produce feature-1 in less than 10 seconds. In other words,, feature-1 processed 27 and a half days in a few seconds. 

## Implementing Feature-2

The task here is to identify the 10 resources that consume the most bandwidth on the site
In order to compute the total bytes communicated through a given resource, summation of the bytes over all the incidents
of this resource was critical. In order to complete this computation in a reasonable time, numpy arrays were created from
the respective columns in the base dataframe and an empty dictionary was initialized. The keys in the dictionary represent
the resources and the values are the total byte per resource

The logic is to loop through all the cases for one time, check if the resource is a key in the dictionary or not, if it is 
not, we create a new key and initialize it with the respective byte value, if it is already a key in the dictionary, then we 
sum the byte of the new case to the value of same resource key. At the end, we transform the dictionary in to a list, sort 
it, and then write the output file.

The entire input of 27 and a half days was processed to produce feature-2 in about 10-15 seconds.


## Implementing Feature-3

This feature's task is to find the top 10 busiest 60-minute intervals.
The implementation of this feature can be explained in the next few points:

1) First, we need to compute the number of clicks for every unique timestamp in the dataset. We can the use efficient 
value_counts() method on the timestamp column in the dataframe. This method returns an unordered series which we convert into an easy to sort list of tuples.

2) Second, we have to consider intervals of inactivity or no clicks. For that purpose, we create two lists:

-- date_range_by_second which has an index for every single second in the total time interval of the dataset.

-- clicks_at_every_second which represents the activity or number of clicks per second. 

clicks_at_every_second list is all initialized to zero and then populated accordingly from total_clicks_per_timestamp we obtained from the first step above.

We also need to pad clicks_at_every_second with an extra hour in order to facilitate the next
phase of computing hourly cumulative clicks for the last second in our real dataset.

3) Third, we convert clicks_at_every_second into an np.array in order to facilitate cumulative sums over 3600 seconds.
We compute the cumulative clicks for the first second as a base case. Then we implement a fast algorithm for computing that 
value at every index of hourly_cumulative_clicks using this self-explanatory formula:

hourly_cumulative_clicks[n] = hourly_cumulative_clicks[n-1] - clicks_at_every_second[n-1] + clicks_at_every_second[n + 3599]

Lastly and before we generate hours.txt output, we zip date_range_by_second and hourly_cumulative_clicks in order to  facilitate sorting and locating the busiest 10 hours.

Feature-3 took around 4 seconds to process the entire input of more than 27 days.


## Implementing Feature-4

Feature-4 is expected to detect whether someone who failed to login from the same IP three consecutive time over 20 seconds  
was NOT blocked ofthe site for the next 5 minutes, in other words, feature-4 is supposed to record any security breach. 
Please refer to the website of the challenge for further information and more detailed expalnation of this feature.

In order to create feature-4, the implementation was divided into two phases:
Phase-1: we use phase_1_blocked_assessment function in order to locate and output any case in which the same host attemped to login and failed for three consecutive times in 20 seconds. 

Phase-2: using the output of phase-1, phase_2_blocked_assessment function will report any breach case in which a case detected in phase-1 was not blocked from using the site.

Feature-4 was the slowest among all the implemented features and it processed the input of more than 27 days in about 10 minutes.


In case you have any question, please contact me at 'hshallal@icloud.com'. '
