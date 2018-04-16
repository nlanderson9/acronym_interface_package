####################################################################################################################
# ===Coding Behavioral Data=== #
# Codes participant responses, then creates a BIDS-format events file (.tsv)
####################################################################################################################

import os, csv, sys, glob


'''
Unsurprisingly, the coding of behavioral data is incredibly specific to each individual experiment. As it is
difficult to make any broad assumptions about how data will be coded, this script MUST be modified for your particular
experiment.

The purpose of the BIDS format is to ensure that these differences can be reduced to a common format. Therefore,
regardless of how your data looks to start, it MUST result in a standard BIDS event file format.

BIDS files have the following requirements:
1.  A single file must be created for each run, for each participant.
1a. It will share an identical name with the NIfTI file, and be stored in the same /func folder. For example,
    "sub-abcd001_task-encoding1_bold.nii.gz" should also have a file called "sub-abcd001_task-encoding1_events.tsv"
1b. If you have a session or experiment that is behavioral only (no fMRI data), you will create a task events file with
    its own name. This will be stored in the /beh folder (instead of /func).
2.  All event files must be in TSV format (tab-separated values).
3.  All items in the first two columns (and all subsequent columns) must be in seconds, not milliseconds:
    3a. The first column of this file must be "onset" and contain the start time for that event (from scan start, which
        would include dropped frames).
    3b. The second column must be "duration" and contain the duration of the event.
4.  You may add as many other columns as you'd like, which could include reaction time (in seconds), trial type,
    participant response, stimulus name, etc. All column names must be a single word ("reaction_time", not
    "reaction time") and must be all lower case.
5.  All missing values should be coded 'n/a'
    
Further information can be found in the BIDS Specification, section 8.5 "Task Events"
'''




def code_data(session, multi_session, number_of_sessions, folder, func_folder, raw_behavioral_folder, participant_number, participant_00X, id_prefix):
	# the "session" variable codes for an integer corresponding to which session number this is (always 1 if yours is a
	#               one-session experiment)
	# the "multi_session" variable is a boolean; it is "True" if you have multiple sessions, and "False" if you have one
	# the "func_folder" variable is a path to the func folder for this participant (and this session, if relevant)
	# the "raw_behavioral_folder" variable is a path the folder where all of your raw PsychoPy data is held (.csv, .log,
    #                             and .psydat files for all participants and runs).
	# the "participant number" variable codes for an integer for your participant number (e.g. 1, 25)
	# the "participant_number_00X" variable is a zero-padded string with your participant number (e.g. '001', '025')


	# This code does not have multiple runs of the same task. If this is the case for your experiment, you will need
	# to take into account the run number in your code (found in the file name of the BOLD run files)


	func_files = os.listdir(func_folder)  # list of all files in func folder
	func_files = [x for x in func_files if ".DS_Store" not in x]
	func_files = [x for x in func_files if "task-rest" not in x]  # remove all resting state files from list, which have no events to be coded
	func_files = [x for x in func_files if "sbref" not in x]  # remove all sbref files
	func_files = [x for x in func_files if "events" not in x]  # ignore any existing events files
	func_files = [x for x in func_files if ".json" not in x]  # keep only NIfTI files, remove json files

	func_tasks = []
	for file in func_files:
		splits = file.split("_")
		for item in splits:
			if "task-" in item:
				func_tasks.append(item[5:])  # add task name for each BOLD run to a list
	# There are now two lists:
	# func_files: all of the BOLD run NIfTI files with their full file names
	# func_tasks: all of the individual task names for each of those files


	raw_behavioral_files = os.listdir(raw_behavioral_folder)  # list of all files in the raw_behavioral folder (includes all participants, all sessions, all runs)
	task_file_dict = {}
	for file in raw_behavioral_files:
		for func_task in func_tasks:  # check each raw behavioral file against our list of tasks we want to code
			participant_task_count = 0
			if file.startswith(participant_00X) and func_task in file.lower() and '.csv' in file:
				# if this csv behavioral file starts with the participant number (zero-padded), and also contains the task name (when the file name is made all lower-case, to match the lower-case task name)
				task_file_dict[func_task] = file
				participant_task_count += 1
			if participant_task_count > 1:  # was there more than one .csv file for this participant for this task (i.e. the task was run more than once for this participant)
				print('For Participant sub-%s%s please ensure that there is only one %s csv file in the directory' % (
				id_prefix, participant_00X, func_task))
				sys.exit('Please add or delete unnecessary files from the folder %s' % raw_behavioral_folder)


	# There is now a dictionary (task_file_dict) with the structure {'TaskName': 'BehavioralFileName'} for all tasks

	for task in task_file_dict: # Loop through each run
		# Set up task/file names
		task_name = task
		behavioral_file_name = task_file_dict[task]
		func_file_name = None
		for file in func_files:
			if task_name in file:
				func_file_name = file


		##################################################################
		# Determine onset times for each trial of this task #

		logfile = behavioral_file_name[:-3] + 'log'
		tsvfile = 'converted_' + logfile[:-3] + 'tsv'
		csvfile = 'converted_' + logfile[:-3] + 'csv'

		# convert .log file to tab-delimited file
		with open(raw_behavioral_folder + "/" + tsvfile, 'w') as out:
			with open(raw_behavioral_folder + "/" + logfile, 'r') as f:
				for line in f:
					out.write(line)
		# convert .tsv to .csv
		in_txt = csv.reader(open(raw_behavioral_folder + "/" + tsvfile, "rb"), delimiter='\t')
		out_csv = csv.writer(open(raw_behavioral_folder + "/" + csvfile, 'wb'))
		out_csv.writerow(["Time", "EventType", "Event"])  # create file headers
		out_csv.writerows(in_txt)
		os.remove(raw_behavioral_folder + "/" + tsvfile)  # delete unnecessary .tsv file

		# Create list of dictionaries from new CSV file to manipulate in Python
		with open(raw_behavioral_folder + "/" + csvfile) as csvfile2:
			dict_list = [{k: v for k, v in row.items()} for row in
								csv.DictReader(csvfile2, skipinitialspace=True)]

		for item in dict_list:
			del item['EventType']  # delete unnecessary column

		for item in dict_list:
			if item['Event'] == 'Keypress: 5':  # finds the first line with "Keypress: 5" (i.e. first sync pulse)
				starttime = item['Time']  # this is the time the run started
				break

		# create a new spreadsheet only including the times for start and end of stimuli
		new_dict_list = []
		keepevents = ['encodingScene_1: autoDraw = True', 'retrievalScene_1A: autoDraw = True']  # autodraw refers to when the stimulus was displayed on the screen ("True") or removed from the screen ("False")
		new_dict_list[:] = [d for d in dict_list if d.get('Event') in keepevents]

		onsets_list = []
		for item in new_dict_list:
			onsets_list.append(float(item['Time']) - float(starttime))




		##################################################################
		# Create the event files#

		with open(raw_behavioral_folder + "/%s" % behavioral_file_name) as csvfile:
			behavioral_data_dict_list = [{k: v for k, v in row.items()} for row in
								csv.DictReader(csvfile, skipinitialspace=True)]
		# Import the csv file as a list of dictionaries (each dictionary in the list is a row, and each key/value pair in the dictionary is a column/value pair)


		output_dict_list = []  # This will contain the final data for the tsv file; the data for each row (trial) will be appended to this at the end of every loop
		if "encoding" in task_name:
			left_outdoor_list = [1, 2, 3 ,4 ,9, 10, 11, 12, 17, 18, 19, 20]  # participants for which "outdoor" is the left index finger
			outdoor = None
			if participant_number in left_outdoor_list:
				outdoor = 'left'  # OUTDOOR = LEFT (6), INDOOR = RIGHT (1)
			else:
				outdoor = 'right'  # INDOOR = LEFT (6), OUTDOOR = RIGHT (1)

			trial_count = 0
			for item in behavioral_data_dict_list:
				row_dict = {}  # This dictionary will hold the values for every column for this row (trial)

				if item['encodingTrialResponse.keys'] == "":  # if not an encoding trial (i.e. a null/jitter trial)
					del item
					continue  # end loop, skip to next item


				# REQUIRED COLUMNS
				row_dict['onset'] = onsets_list[trial_count]  # This will be determined later in the script
				row_dict['duration'] = '0.5'


				# Optional Columns
				row_dict['trial_type'] = 'encoding'
				row_dict['encoding_block'] = item['EncodingBlock']
				row_dict['retrieval_block'] = item['RetrievalBlock']
				row_dict['old_new'] = 'old'
				row_dict['indoor_outdoor'] = item['IndoorOutdoor'].lower()
				row_dict['filename'] = item['Filename'].lower()

				if outdoor == 'left':
					row_dict['buttonbox_side'] = 'outdoor | indoor'
				else:
					row_dict['buttonbox_side'] = 'indoor | outdoor'

				row_dict['fingers_side'] = 'n/a'

				if (outdoor == 'left' and item['IndoorOutdoor'] == 'Outdoor') or (outdoor == 'right' and item['IndoorOutdoor'] == 'Indoor'):
					row_dict['correct_key'] = '6'
				else:
					row_dict['correct_key'] = '1'

				row_dict['correct_response'] = item['IndoorOutdoor'].lower()

				if item['encodingTrialResponse.rt']:
					row_dict['participant_response_rt'] = item['encodingTrialResponse.rt']
				else:
					row_dict['participant_response_rt'] = 'n/a'

				if item['encodingTrialResponse.keys'] == 'None':
					row_dict['participant_response_key'] = 'n/a'
				else:
					row_dict['participant_response_key'] = item['encodingTrialResponse.keys']

				if (outdoor == 'left' and item['encodingTrialResponse.keys'] == '6') or (outdoor == 'right' and item['encodingTrialResponse.keys'] == '1'):
					row_dict['participant_response'] = 'outdoor'
				else:
					row_dict['participant_response'] = 'indoor'
				if row_dict['participant_response_key'] == 'n/a':
					row_dict['participant_response'] = 'n/a'

				if row_dict['participant_response_key'] == row_dict['correct_key']:
					row_dict['participant_response_scored'] = 'correct'
				else:
					row_dict['participant_response_scored'] = 'incorrect'

				row_dict['participant_response_judgment'] = 'n/a'
				row_dict['participant_response_conf'] = 'n/a'
				row_dict['participant_response_type'] = 'n/a'
				row_dict['participant_response_type_conf'] = 'n/a'

				#Mark these as '?' for now - they will be filled in later
				row_dict['participant_subsequent_judgment'] = '?'
				row_dict['participant_subsequent_conf'] = '?'
				row_dict['participant_subsequent_type'] = '?'
				row_dict['participant_subsequent_type_conf'] = '?'

				output_dict_list.append(row_dict)
				trial_count += 1



		elif "retrieval" in task_name:
			old = None
			if int((participant_number - 1) / 2) % 2 == 0:  # OLD = LEFT (S, D, F), NEW = RIGHT (J, K, L)
				old = 'left'
			else:
				old = 'right'

			index = None
			if int(participant_number - 1) % 2 == 0:  # OLD-LOW (8), OLD-MOD (7), OLD-HIGH (6), NEW-HIGH (1), NEW-MOD (2), NEW-LOW (3)
				index = 'high'
			else:
				index = 'low'

			trial_count = 0
			for item in behavioral_data_dict_list:
				row_dict = {}  # This dictionary will hold the values for every column for this row (trial)

				if item['retrievalTrialResponse.keys'] == "":  # if not an encoding trial (i.e. a null/jitter trial)
					del item
					continue  # end loop, skip to next item

				# REQUIRED COLUMNS
				row_dict['onset'] = onsets_list[trial_count]  # This will be determined later in the script
				row_dict['duration'] = '1.9'

				# Optional Columns
				row_dict['trial_type'] = 'retrieval'

				if item['EncodingBlock']:
					row_dict['encoding_block'] = item['EncodingBlock']
				else:
					row_dict['encoding_block'] = 'n/a'

				row_dict['retrieval_block'] = item['RetrievalBlock']

				if item['OldTrue'] == '1':
					row_dict['old_new'] = 'old'
				else:
					row_dict['old_new'] = 'new'

				row_dict['indoor_outdoor'] = item['IndoorOutdoor'].lower()
				row_dict['filename'] = item['Filename'].lower()

				if old == 'left':
					row_dict['buttonbox_side'] = 'old | new'
				else:
					row_dict['buttonbox_side'] = 'new | old'

				if index == 'high':
					row_dict['fingers_side'] = 'l m h | h m l'
				else:
					row_dict['fingers_side'] = 'h m l | l m h'

				if (row_dict['old_new'] == 'old' and old == 'left') or (row_dict['old_new'] == 'new' and old == 'right'):
					row_dict['correct_key'] = '6/7/8'
				else:
					row_dict['correct_key'] = '1/2/3'

				row_dict['correct_response'] = row_dict['old_new']

				if item['retrievalTrialResponse.rt']:
					row_dict['participant_response_rt'] = item['retrievalTrialResponse.rt']
				else:
					row_dict['participant_response_rt'] = 'n/a'

				if item['retrievalTrialResponse.keys'] == 'None':
					row_dict['participant_response_key'] = 'n/a'
				else:
					row_dict['participant_response_key'] = item['retrievalTrialResponse.keys']

				if row_dict['participant_response_key'] in row_dict['correct_key']:
					scored = 'correct'
				else:
					scored = 'incorrect'

				if (old == 'left' and row_dict['participant_response_key'] in ['6', '7', '8']) or (old == 'right' and row_dict['participant_response_key'] in ['1', '2', '3']):
					judgment = 'old'
				else:
					judgment = 'new'
				if row_dict['participant_response_key'] == 'n/a':
					judgment = 'n/a'

				if scored == 'correct':
					if row_dict['old_new'] == 'old':
						type = 'hit'  # correct and old item
					else:
						type = 'cr'  # correct and new item
				else:
					if row_dict['old_new'] == 'old':
						type = 'miss'  # incorrect and old item
					else:
						type = 'fa'  # incorrect and new item
				if row_dict['participant_response_key'] == 'n/a':
					type = 'n/a'

				if row_dict['participant_response_key'] in ['2', '7']:
					conf = 'mod'
				elif row_dict['participant_response_key'] in ['1', '6']:
					conf = index
				else:  # if response in ['3', '8']
					if index == 'high':
						conf = 'low'
					else:
						conf = 'high'
				if row_dict['participant_response_key'] == 'n/a':
					conf = 'n/a'

				if row_dict['participant_response_key'] == 'n/a':
					row_dict['participant_response'] = 'n/a'
				else:
					row_dict['participant_response'] = '%s-%s' % (judgment, conf)
				row_dict['participant_response_scored'] = scored
				row_dict['participant_response_judgment'] = judgment
				row_dict['participant_response_conf'] = conf
				row_dict['participant_response_type'] = type
				if row_dict['participant_response_key'] == 'n/a':
					row_dict['participant_response_type_conf'] = 'n/a'
				else:
					row_dict['participant_response_type_conf'] = '%s-%s' % (type, conf)

				row_dict['participant_subsequent_judgment'] = 'n/a'
				row_dict['participant_subsequent_conf'] = 'n/a'
				row_dict['participant_subsequent_type'] = 'n/a'
				row_dict['participant_subsequent_type_conf'] = 'n/a'

				if participant_00X == '007':  # this participant lost 44 trials at the end of Encoding 2, and they are being recoded as new items for Retrieval2A/B
					if any(row_dict['filename'] in x for x in
						   ['indoor_squash_court.jpg', 'indoor_hockey_rink.jpg .jpg', 'outdoor_deer_blind.jpg',
							'indoor_christmaspresents.jpg', 'outdoor_playground.jpg', 'indoor_ballroom.jpg',
							'indoor_airplane_cabin.jpg', 'outdoor_government_building.jpg', 'outdoor_track.jpg',
							'indoor_electronicstore.jpg'
							'indoor_fishingstore.jpg', 'outdoor_empty_wheelbarrow.jpg', 'indoor_drugstore.jpg',
							'outdoor_ferris_wheel.jpg', 'indoor_jail.jpeg', 'outdoor_rusting_sub.jpg',
							'indoor_bikestore.jpg', 'outdoor_dark_intersection.jpg', 'outdoor_smoke_stacks.jpg',
							'indoor_candy_store.jpg', 'indoor_gymnastics.jpg', 'outdoor_cityscape.jpg',
							'indoor_skydiving_tube.jpg', 'outdoor_cliff.jpg', 'outdoor_fancy_fence.jpg',
							'indoor_hardware_store.jpg', 'outdoor_dam.jpg', 'indoor_greekrestaurant.jpg',
							'indoor_officelunchroom.jpg', 'indoor_funeral_chapel.jpg', 'outdoor_botanical_garden.jpg',
							'outdoor_clock_tower.jpg', 'outdoor_butte.jpg', 'indoor_controlroom.jpg',
							'indoor_subway_station.jpg', 'outdoor_tornado.jpg', 'indoor_fabric_store.jpg',
							'indoor_toy_store.jpg', 'indoor_officesupplies.jpg', 'outdoor_old_arena.jpg',
							'outdoor_ww2_vehicles.jpg', 'outdoor_pine_forest.jpg', 'indoor_hair_salon.jpg',
							'outdoor_lava.jpg']):
						resp1 = None
						resp2 = None
						row_dict['encoding_block'] = 'n/a'
						row_dict['old_new'] = 'new'
						row_dict['correct_response'] = 'new'
						if 'new' in row_dict['participant_response']:
							row_dict['participant_response_scored'] = 'correct'
							row_dict['participant_response_judgment'] = 'new'
							resp1 = 'cr'
						elif 'old' in row_dict['participant_response']:
							row_dict['participant_response_scored'] = 'incorrect'
							row_dict['participant_response_judgment'] = 'old'
							resp1 = 'fa'
						else:
							row_dict['participant_response_scored'] = 'n/a'
							row_dict['participant_response_judgment'] = 'n/a'
							resp1 = 'n/a'
						if 'high' in row_dict['participant_response']:
							resp2 = 'high'
						elif 'mod' in row_dict['participant_response']:
							resp2 = 'mod'
						elif 'low' in row_dict['participant_response']:
							resp2 = 'low'
						else:
							resp2 = 'n/a'
						row_dict['participant_response_conf'] = resp2
						row_dict['participant_response_type'] = resp1
						if row_dict['participant_response_scored'] == 'n/a':
							row_dict['participant_response_type_conf'] = 'n/a'
						else:
							row_dict['participant_response_type_conf'] = '%s-%s' % (resp1, resp2)




				output_dict_list.append(row_dict)
				trial_count += 1

		columnnames = ['onset',
					   'duration',
					   'trial_type',
					   'encoding_block',
					   'retrieval_block',
					   'old_new',
					   'indoor_outdoor',
					   'filename',
					   'buttonbox_side',
					   'fingers_side',
					   'correct_key',
					   'correct_response',
					   'participant_response_rt',
					   'participant_response_key',
					   'participant_response',
					   'participant_response_scored',
					   'participant_response_judgment',
					   'participant_response_conf',
					   'participant_response_type',
					   'participant_response_type_conf',
					   'participant_subsequent_judgment',
					   'participant_subsequent_conf',
					   'participant_subsequent_type',
					   'participant_subsequent_type_conf']

		output_file_path = func_folder + "/" + func_file_name[:-11] + "events.tsv"
		write_file = open(output_file_path, 'wb')  # write new file
		csvwriter = csv.DictWriter(write_file, delimiter='\t', fieldnames=columnnames)
		csvwriter.writerow(dict((fn, fn) for fn in columnnames))
		for index, item in enumerate(output_dict_list):
			csvwriter.writerow(item)
		write_file.close()



	# Subsequent Memory
	if session == number_of_sessions:  # if this is the last session (or only session)
		events_files = []
		for session in range(1, number_of_sessions + 1):
			func_folder = folder + "/sub-%s%s/ses-0%s" % (id_prefix, participant_00X, session) + "/func"
			events_files = events_files + glob.glob(func_folder + "/*events.tsv")

		for file in events_files:
			if 'retrieval' in file:
				continue  # only do this for encoding files
			else:
				splits = file.split("_")
				for split in splits:
					if "task-" in split:
						task_name = split[5:]  # get the task name from the BIDS-structured filename
				retrieval_files = [x for x in events_files if 'task-retrieval%sa' % task_name[-1] in x] + [x for x in events_files if 'task-retrieval%sb' % task_name[-1] in x]


			with open(file) as encoding_file:
				encoding_dict_list = [{k: v for k, v in row.items()} for row in
									csv.DictReader(encoding_file, skipinitialspace=True, delimiter='\t')]
			with open(retrieval_files[0]) as retrieval_file1:
				retrieval_file1_dict_list = [{k: v for k, v in row.items()} for row in
									csv.DictReader(retrieval_file1, skipinitialspace=True, delimiter='\t')]
			with open(retrieval_files[1]) as retrieval_file2:
				retrieval_file2_dict_list = [{k: v for k, v in row.items()} for row in
									csv.DictReader(retrieval_file2, skipinitialspace=True, delimiter='\t')]
			retrieval_data = retrieval_file1_dict_list + retrieval_file2_dict_list

			for encoding_item in encoding_dict_list:
				for retrieval_item in retrieval_data:
					if encoding_item['filename'] == retrieval_item['filename']:
						encoding_item['participant_subsequent_judgment'] = retrieval_item['participant_response_judgment']
						encoding_item['participant_subsequent_conf'] = retrieval_item['participant_response_conf']
						encoding_item['participant_subsequent_type'] = retrieval_item['participant_response_type']
						encoding_item['participant_subsequent_type_conf'] = retrieval_item['participant_response_type_conf']
				if encoding_item['filename'] == 'outdoor_cebu_tops.jpg' and participant_00X == '014':  # due to experimenter error, this participant was not shown this item during retrieval, and so there were no subsequent responses
					encoding_item['participant_subsequent_judgment'] = 'n/a'
					encoding_item['participant_subsequent_conf'] = 'n/a'
					encoding_item['participant_subsequent_type'] = 'n/a'
					encoding_item['participant_subsequent_type_conf'] = 'n/a'


			columnnames = ['onset',
						   'duration',
						   'trial_type',
						   'encoding_block',
						   'retrieval_block',
						   'old_new',
						   'indoor_outdoor',
						   'filename',
						   'buttonbox_side',
						   'fingers_side',
						   'correct_key',
						   'correct_response',
						   'participant_response_rt',
						   'participant_response_key',
						   'participant_response',
						   'participant_response_scored',
						   'participant_response_judgment',
						   'participant_response_conf',
						   'participant_response_type',
						   'participant_response_type_conf',
						   'participant_subsequent_judgment',
						   'participant_subsequent_conf',
						   'participant_subsequent_type',
						   'participant_subsequent_type_conf']

			output_file_path = file
			output_dict_list = encoding_dict_list
			write_file = open(output_file_path, 'wb')  # write new file
			csvwriter = csv.DictWriter(write_file, delimiter='\t', fieldnames=columnnames)
			csvwriter.writerow(dict((fn, fn) for fn in columnnames))
			for index, item in enumerate(output_dict_list):
				csvwriter.writerow(item)
			write_file.close()


	print("Behavioral files written for sub-%s%s!" % (id_prefix, participant_00X))