####################################################################################################################
# ===Create AFNI Timing Files=== #
# Pulls data from PsychoPy .log files, along with coded behavioral data, to create timing (onset) files formatted for AFNI
####################################################################################################################

import os, csv, sys, glob

'''
Unsurprisingly, the creation of timing files is fairly specific to each individual experiment. As it is
difficult to make any broad assumptions about how data will be coded, this script MUST be modified for your particular
experiment.

Importantly, these are timing files for AFNI. Therefore, they do not follow BIDS format (as they follow AFNI's
requirements, and BIDS has no standard format for timing files). However, this script does assume that the input data is
in BIDS format, and uses BIDS events files to quickly create AFNI-formatted timing files.

The following are formatting notes for AFNI timing files:
1. They are simple text files. AFNI can read these as .txt files, or its own .1D files.
2. All trial times for a single run should appear on a single line, separated by spaces.
3. There must be a row for every BOLD file you include in your script. If your analysis means you aren't interested in
   the information in a particular run, you can instead place an asterisk (*) on that line instead of times.
4. You must create a timing file for each type of data you are interested in. Together, each of these timing files MUST
   account for every event that occurs during the BOLD runs (e.g. when looking at retrieval data, you cannot just look
   at Hits and Misses. You must also code for CRs and FAs; however, you could create a timing file for "not Hits/Misses"
   to simply account for all other events that aren't Hits/Misses, if you aren't interested in them.
4. If you are interested in the data for a given BOLD run, but no events of the type being used in a timing file exist
   (for example, I'm making a "misses" timing file and I care about Encoding Run 2, but during Run 2 this participant
   had no misses), put a "-1" on that run's line. This tells AFNI that the run isn't to be ignored (like using an
   asterisk *), but that there are no valid times for that event type.
5. If you wish to include a trial-level covariate (the most common being RT), include it as a "married" value with an
   asterisk (i.e. timevalue*RTvalue)
6. If wish to include RT as a covariate, on trials with no participant response you should set the RT equal to your TR.
   
   
Example files (3 BOLD runs):
############################
############################

Hits.txt
5.7 16.7 22.2
3.6 11.8
6.4 12.2 18.7 29.6

Same as above, but with RT:

Hits.txt
5.7*0.325 16.7*0.232 22.2*0.336
3.6*0.227 11.8*0.292
6.4*0.312 12.2*0.288 18.7*0.301 29.6*0.262

Same as the first, but (for whatever reason) you aren't interested in Run 2:

Hits.txt
5.7 16.7 22.2
*
6.4 12.2 18.7 29.6

Same as the first, but if the participant didn't have any hits in Run 1:

Hits.txt
-1
3.6 11.8
6.4 12.2 18.7 29.6

'''


# This is used to tell the script the order of the task runs, so they can be put in order in the timing files
# These are the task names used in the BIDS naming system for bold and events files.
task_order = ['encoding1', 'retrieval1a', 'retrieval1b', 'encoding2', 'retrieval2a', 'retrieval2b', 'encoding3', 'retrieval3a', 'retrieval3b']

# In the case of trials that do not have an RT (i.e. trials with no participant response), you can simply replace the
# RT with the full length of the TR.
tr = '1.1'


def create_AFNI_timing_files(number_of_sessions, multi_session, participant_00X, id_prefix, folder, onsets_folder):
	if multi_session:
		events_files = []
		for session in range(1, number_of_sessions + 1):
			func_folder = folder + "/sub-%s%s/ses-0%s" % (id_prefix, participant_00X, session) + "/func"
			events_files = events_files + glob.glob(func_folder + "/*events.tsv")
	else:
		func_folder = folder + "/sub-%s%s" % (id_prefix, participant_00X) + "/func"
		events_files = glob.glob(func_folder + "/*events.tsv")
	# events_files now contains the filepaths for every events file for this participant

	#deletes all existing files in the onsets folder, so the script doesn't add times to existing files
	old_onset_files = os.listdir(onsets_folder)
	for f in old_onset_files:
		os.remove(onsets_folder + "/" + f)

	events_files_ordered = []
	for task in task_order:
		for file in events_files:
			if task in file:
				events_files_ordered.append(file)
	events_files = events_files_ordered
	# events_files is now ordered, in the order given by task_order (above)

	for file in events_files:
		splits = file.split("_")
		for split in splits:
			if "task-" in split:
				task_name = split[5:]  # get the task name from the BIDS-structured filename

		with open(file) as csvfile: # open the events tsv file
			events_dict_list = [{k: v for k, v in row.items()} for row in
								csv.DictReader(csvfile, skipinitialspace=True, delimiter = '\t')]


		# This script basically loops through each task, and adds a row to the timing files for that task. So it looks
		# like this:
		# Task 1: Create all timing files, write the first line of times (or a *, if this task isn't applicable)
		# Task 2: Open all timing files, append a new line, write the second line of times (or *)
		# Task 3: Open all timing files, append a new line, write the third line of times (or *)
		# etc...


		type_level = ["all", "encoding", "retrieval"]
		duration_level = ["allruns","short1", "short2", "bothshort", "long"]
		event_level = ["allevents", "hit", "miss", "cr", "fa"]
		conf_level = ["all", "high", "mod", "low", "modlow"]
		rt_level = ['rt', 'nort']

		for loop_rt_level in rt_level:
			for loop_type_level in type_level:
				for loop_duration_level in duration_level:
					for loop_event_level in event_level:
						if loop_type_level == 'encoding' and (loop_event_level == 'cr' or loop_event_level == 'fa'):
							continue  # we don't need to write a file for CRs or FAs if we're looking at encoding (those are impossible)
						for loop_conf_level in conf_level:
							if conf_level == 'all':
								output_file = onsets_folder + "/sub-%s%s_%s_%s_%s_%s.txt" % (id_prefix, participant_00X, loop_type_level, loop_duration_level, loop_event_level, loop_rt_level)  #create the filename for our AFNI timing file
							else:
								output_file = onsets_folder + "/sub-%s%s_%s_%s_%s_%sconf_%s.txt" % (id_prefix, participant_00X, loop_type_level, loop_duration_level, loop_event_level, loop_conf_level, loop_rt_level)
							if os.path.exists(output_file):
								textfile = open(output_file, 'a')  # add to the existing file
							else:
								textfile = open(output_file, 'w')  # for the first row, create new file
							if loop_type_level not in task_name and loop_type_level != 'all':
								textfile.write("*")
								textfile.write("\n")
								continue
							if loop_duration_level == 'short1' and '1' not in task_name:
								textfile.write("*")
								textfile.write("\n")
								continue
							if loop_duration_level == 'short2' and '3' not in task_name:
								textfile.write("*")
								textfile.write("\n")
								continue
							if loop_duration_level == 'bothshort' and not any(x in task_name for x in ['1', '3']):
								textfile.write("*")
								textfile.write("\n")
								continue
							if loop_duration_level == 'long' and '2' not in task_name:
								textfile.write("*")
								textfile.write("\n")
								continue
							event_counter = 0
							for item in events_dict_list:
								onset = item['onset']
								rt = item['participant_response_rt']
								response_type = item['participant_response_type']
								response_conf = item['participant_response_conf']
								response_type_conf = item['participant_response_type_conf']
								subsequent_type = item['participant_subsequent_type']
								subsequent_conf = item['participant_subsequent_conf']
								subsequent_type_conf = item['participant_subsequent_type_conf']

								if item['filename'] == 'outdoor_cebu_tops.jpg' and participant_00X == '014':  # due to experimenter error, this participant was not shown this item during retrieval, and will be omitted from analyses
									continue

								if loop_event_level == 'allevents':  # all trials
									textfile.write(str(round(float(onset), 4)))
									event_counter += 1
									if loop_rt_level == 'rt':  # if we want to include RT as a covariate
										if rt != 'n/a':  # if we have an RT for this trial (i.e. the participant responded)
											textfile.write('*' + str(round(float(rt), 4)) + ' ')
										else:  # if there is no RT (i.e. no response from the participant)
											textfile.write('*' + tr + ' ')  # AFNI just lets you put the TR, to assume no RT during the length of the trial
									else:  # if we don't want to include RT as a covariate
										textfile.write(' ')
								else:  # selected trials
									if loop_conf_level == 'all':  # not separated by confidence
										if loop_event_level == response_type or loop_event_level == subsequent_type:
											textfile.write(str(round(float(onset), 4)))
											event_counter += 1
											event_counter += 1
											if loop_rt_level == 'rt':
												if rt != 'n/a':
													textfile.write('*' + str(round(float(rt), 4)) + ' ')
												else:
													textfile.write('*' + tr + ' ')
											else:
												textfile.write(' ')
									elif loop_conf_level == 'modlow':  # special case added manually
										if (loop_event_level in response_type_conf and any(x in response_type_conf for x in ['mod', 'low'])) or (loop_event_level in subsequent_type_conf and any(x in subsequent_type_conf for x in ['mod', 'low'])):
											textfile.write(str(round(float(onset), 4)))
											event_counter += 1
											if loop_rt_level == 'rt':
												if rt != 'n/a':
													textfile.write('*' + str(round(float(rt), 4)) + ' ')
												else:
													textfile.write('*' + tr + ' ')
											else:
												textfile.write(' ')
									else:  # separated by confidence
										if ('%s-%s' % (loop_event_level, loop_conf_level) == response_type_conf) or ('%s-%s' % (loop_event_level, loop_conf_level) == subsequent_type_conf):
											textfile.write(str(round(float(onset), 4)))
											event_counter += 1
											if loop_rt_level == 'rt':
												if rt != 'n/a':
													textfile.write('*' + str(round(float(rt), 4)) + ' ')
												else:
													textfile.write('*' + tr + ' ')
											else:
												textfile.write(' ')
							if event_counter == 0:  # if this was a relevant run, but there were no events of this type
								textfile.write('-1')
								if loop_rt_level == 'rt':
									textfile.write('*' + tr)
							textfile.write('\n')
							textfile.close()

	print("AFNI timing files generated for sub-%s%s!" % (id_prefix, participant_00X))