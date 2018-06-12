####################################################################################################################
# ===Conversion from DICOM to NIfTI Files & NIfTI File Reorganization=== #
# This section runs the dcm2niix conversion tool, then reorganizes converted NIfTI files into the file structure
# created previously in the script, following the BIDS format.
####################################################################################################################

import subprocess, os, shutil, json
from Tkinter import *

def notification(text):
	root = Tk()  # create TKinter window
	root.title("Conversion update")
	root.geometry('+1070+500')  # sets the location of the window - format (+horiz+vert)
	root.wm_attributes("-topmost", 1)  # makes sure that the window appears on top of all other windows
	label = Label(root)
	label.pack()
	label.config(text=str(text))
	root.after(5000, lambda: root.destroy())
	root.mainloop()


##########################################################
# ===Convert DICOMs to NIfTI Files=== #
##########################################################

def dcm2niix(show_notifications, multi_session, dicom_folder, nifti_folder, session, dcm2niix_folder):
	FNULL = open(os.devnull, 'w')  # used to suppress terminal command output
	if multi_session:
		print("Converting Session %s DICOMs to NIfTIs using dcm2niix" % session)
	else:
		print("Converting DICOMs to NIfTIs using dcm2niix" % session)
	subprocess.call(['%s -b y -ba y -z y -v n -o %s -f "%%p_%%s" %s' % (dcm2niix_folder, nifti_folder, dicom_folder)], shell=True, stdout=FNULL, stderr=subprocess.STDOUT)  # equivalent to typing command in Terminal, with output suppressed
	if show_notifications:
		notification("Your DICOMs have been converted to NIfTIs!")
	if multi_session:
		print("\nSession %s DICOMs converted to NIfTIs" % session)
	else:
		print("\nDICOMs converted to NIfTIs" % session)

##########################################################
# ===Relocate new NIfTI files to appropriate folders=== #
##########################################################

def reorganize_NIfTI(multi_session, session, id_prefix, dicom_folder, nifti_folder, anat_folder, func_folder, fieldmap_folder, participant_00X, task_code):
	# Delete the DICOM folder, which is no longer needed now that all files have been converted to NIfTIs
	if os.path.exists(dicom_folder):
		shutil.rmtree(dicom_folder)

	ses = ''
	if multi_session:
		ses = "_ses-0" + str(session)  # if this is a multi-session experiment, all filenames must include the session

	# Move selected NIfTI & JSON files to other folders to conform with BIDS specification
	files2 = os.listdir(nifti_folder)
	for f in files2:
		# Anatomical files
		if "T1" in f or "T2" in f:
			shutil.move(nifti_folder + "/%s" % f, anat_folder + "/%s" % f)
		# Fieldmap files
		elif "spinecho" in f.lower() or "fieldmap" in f.lower():
			shutil.move(nifti_folder + "/%s" % f, fieldmap_folder + "/%s" % f)
		# Resting state files
		elif "rsfc" in f.lower() or 'rest' in f.lower():
			shutil.move(nifti_folder + "/%s" % f, func_folder + "/%s" % f)
		# Task files
		# Files will be moved that contain the "task code" in the name of the scan
		elif task_code.lower() in f.lower():
			shutil.move(nifti_folder + "/%s" % f, func_folder + "/%s" % f)


	# Delete extraneous T1 files, and rename them according to BIDS
	anat_files = os.listdir(anat_folder)
	if any("T1" in x for x in anat_files):  # If there are any T1 files in the anat folder
		T1_files = []
		for file in anat_files:
			if "T1" in file and ".nii" in file:
				T1_files.append(file[:-7])  # remove file type suffix
		T1_dict = {}
		for item in T1_files:
			T1_dict[item] = int(item.split("_")[-1])
		keep = max(T1_dict, key=lambda key: T1_dict[key])
		for file in anat_files:
			if not keep in file and "T1" in file:
				os.remove(anat_folder + '/%s' % file) # delete the un-normalized T1 files (nii & JSON)
		anat_files_new = os.listdir(anat_folder)
		for file in anat_files_new:
			if "T1" in file and ".nii" in file:
				os.rename(anat_folder + "/%s" % file, anat_folder + "/sub-%s%s%s_T1w.nii.gz" % (id_prefix, participant_00X, ses))
			if "T1" in file and ".json" in file:
				os.rename(anat_folder + "/%s" % file, anat_folder + "/sub-%s%s%s_T1w.json" % (id_prefix, participant_00X, ses))


	# Delete extraneous T2 files, and rename them according to BIDS
	if any("T2" in x for x in anat_files):  # If there are any T2 files in the anat folder
		T2_files = []
		for file in anat_files:
			if "T2" in file and ".nii" in file:
				T2_files.append(file[:-7])  # remove file type suffix
		T2_dict = {}
		for item in T2_files:
			T2_dict[item] = int(item.split("_")[-1])
		keep = max(T2_dict, key=lambda key: T2_dict[key])
		for file in anat_files:
			if not keep in file and "T2" in file:
				os.remove(anat_folder + '/%s' % file) # delete the un-normalized T2 files (nii & JSON)
		anat_files_new = os.listdir(anat_folder)
		for file in anat_files_new:
			if "T2" in file and ".nii" in file:
				os.rename(anat_folder + "/%s" % file, anat_folder + "/sub-%s%s%s_T2w.nii.gz" % (id_prefix, participant_00X, ses))
			if "T2" in file and ".json" in file:
				os.rename(anat_folder + "/%s" % file, anat_folder + "/sub-%s%s%s_T2w.json" % (id_prefix, participant_00X, ses))


	# Rename task BOLD runs and SBRef (single-band reference files generated by multi-band scans)
	# NOTE: This assumes that all info in the name of the scan, besides the "task code" present in all BOLD task scans,
	# refers to the task being performed. If you did not name your scans this way, you will have to modify the code
	# below to adjust for this.
	# If you choose to manually rename your scans after-the-fact, you will also need to adjust the .json files for
	# fieldmaps you've collected, which have an "IntendedFor:" section that will have added these scan names
	# automatically.
	func_files = os.listdir(func_folder)
	task_files = []
	rsfc_files = []
	for file in func_files:
		if "rsfc" in file.lower() or "rest" in file.lower():
			rsfc_files.append(file)
		else:
			task_files.append(file)
	if task_files:  # if there are any BOLD task files in the func folder
		file_names = []
		for file in task_files:
			if ".nii" in file:
				file_name_split = file.split("_")
				file_name = file.replace(("_" + file_name_split[-1]), "")
				if not file_name in file_names:
					file_names.append(file_name)
		for file in file_names:
			candidates = []
			for original_file in task_files:
				if file in original_file and ".nii" in original_file:
					candidates.append(original_file[:-7])
			candidate_dict = {}
			for item in candidates:
				candidate_dict[item] = int(item.split("_")[-1])
			BOLD_run = max(candidate_dict, key=lambda key: candidate_dict[key])
			SBRef = min(candidate_dict, key=lambda key: candidate_dict[key])

			file = file.lower()
			file_name = file.replace(task_code.lower(), "")
			if file_name[0] == any(x for x in ["_", "-", "."]):  # if there is now a stray '_' or '-' or '.' at the start of the filename
				file_name = file_name[1:]
			if "__" in file_name:  # these three clean things up if the task_code is in the middle of the filename
				file_name = file_name.replace("__", "_")
			if "--" in file_name:
				file_name = file_name.replace("--", "-")
			if ".." in file_name:
				file_name = file_name.replace("..", ".")

			file_name = ''.join(ch for ch in file_name if ch.isalnum())  # BIDS format only allows alphanumeric characters in your task label
			for original_file in task_files:
				if BOLD_run in original_file:
					if ".nii" in original_file:
						os.rename(func_folder + "/%s" % original_file, func_folder + "/sub-%s%s%s_task-%s_bold.nii.gz" % (id_prefix, participant_00X, ses, file_name))
					if ".json" in original_file:
						os.rename(func_folder + "/%s" % original_file, func_folder + "/sub-%s%s%s_task-%s_bold.json" % (id_prefix, participant_00X, ses, file_name))
				if SBRef in original_file:
					if ".nii" in original_file:
						os.rename(func_folder + "/%s" % original_file, func_folder + "/sub-%s%s%s_task-%s_sbref.nii.gz" % (id_prefix, participant_00X, ses, file_name))
					if ".json" in original_file:
						os.rename(func_folder + "/%s" % original_file, func_folder + "/sub-%s%s%s_task-%s_sbref.json" % (id_prefix, participant_00X, ses, file_name))

	if rsfc_files:  # if there are any resting state files in the func folder
		rest_runs = []
		for file in rsfc_files:
			if ".nii" in file:
				rest_runs.append(file[:-7])
		rest_dict = {}
		for item in rest_runs:
			rest_dict[item] = int(item.split("_")[-1])
		rest_bold_dict = {}
		for item in rest_dict:
			if (rest_dict[item] - 1) in rest_dict.values():  # if there is a run in the list that has an index one less than this run
				rest_bold_dict[item] = rest_dict[item]
		rest_bold_sorted_list = []
		for key, value in sorted(rest_bold_dict.iteritems(), key=lambda (k, v): (v, k)):
			rest_bold_sorted_list.append(key)
		run = 1
		for file in rest_bold_sorted_list:
			if len(rest_bold_sorted_list) == 1:  # if there's only one rsfc run
				os.rename(func_folder + "/%s.nii.gz" % file, func_folder + "/sub-%s%s%s_task-rest_bold.nii.gz" % (id_prefix, participant_00X, ses))
				os.rename(func_folder + "/%s.json" % file, func_folder + "/sub-%s%s%s_task-rest_bold.json" % (id_prefix, participant_00X, ses))
				file_split = file.split("_")
				file_sbref = file.replace(file_split[-1], str(int(file_split[-1]) - 1))  # decrement file index by 1 for SBRef file
				os.rename(func_folder + "/%s.nii.gz" % file_sbref, func_folder + "/sub-%s%s%s_task-rest_sbref.nii.gz" % (id_prefix, participant_00X,ses))
				os.rename(func_folder + "/%s.json" % file_sbref, func_folder + "/sub-%s%s%s_task-rest_sbref.json" % (id_prefix, participant_00X, ses))
			else:  # if there are multiple rsfc runs, include a run number
				os.rename(func_folder + "/%s.nii.gz" % file, func_folder + "/sub-%s%s%s_task-rest_run-0%s_bold.nii.gz" % (id_prefix, participant_00X, ses, run))
				os.rename(func_folder + "/%s.json" % file, func_folder + "/sub-%s%s%s_task-rest_run-0%s_bold.json" % (id_prefix, participant_00X, ses, run))
				file_split = file.split("_")
				file_sbref = file.replace(file_split[-1], str(int(file_split[-1])-1))  # decrement file index by 1 for SBRef file
				os.rename(func_folder + "/%s.nii.gz" % file_sbref, func_folder + "/sub-%s%s%s_task-rest_run-0%s_sbref.nii.gz" % (id_prefix, participant_00X, ses, run))
				os.rename(func_folder + "/%s.json" % file_sbref, func_folder + "/sub-%s%s%s_task-rest_run-0%s_sbref.json" % (id_prefix, participant_00X, ses, run))
				run += 1

	renamed_func_files_all = os.listdir(func_folder)
	renamed_func_jsons = []
	for file in renamed_func_files_all:
		if ".json" in file:
				renamed_func_jsons.append(file)
	for file in renamed_func_jsons:
		splits = file.split("_")
		for item in splits:
			if "task-" in item:
				task_name = item[5:]
		with open(func_folder + "/%s" % file, 'r') as f:
			data = json.load(f)
			data['TaskName'] = task_name  # BIDS requires the TaskName to be added to the corresponding .json file

		os.remove(func_folder + "/%s" % file)
		with open(func_folder + "/%s" % file, 'w') as f:
			json.dump(data, f, indent=4)

	# Rename fieldmaps according to BIDS
	fieldmap_files1 = os.listdir(fieldmap_folder)
	fieldmap_files = []
	for item in fieldmap_files1:
		if 'spinecho' in item.lower() or 'fieldmap' in item.lower():
			fieldmap_files.append(item)
	if fieldmap_files:
		if len(fieldmap_files) == 4:  # If there is only a single pair of AP/PA fieldmap files (with their .json files)
			for file in fieldmap_files:
				if ".nii" in file:
					scan_data = json.load(open(fieldmap_folder + '/%s.json' % file[:-7])) # Import the data from the corresponding .json file
					direction = str(scan_data['PhaseEncodingDirection']) # get the phase encoding direction for this fieldmap
					os.rename(fieldmap_folder + "/%s" % file, fieldmap_folder + "/sub-%s%s%s_dir-%s_epi.nii.gz" % (id_prefix, participant_00X, ses, direction))
					os.rename(fieldmap_folder + "/%s.json" % file[:-7], fieldmap_folder + "/sub-%s%s%s_dir-%s_epi.json" % (id_prefix, participant_00X, ses, direction))

		else:
			for file in fieldmap_files:
				if ".nii" in file:
					scan_data = json.load(open(fieldmap_folder + '/%s.json' % file[:-7])) # Import the data from the corresponding .json file
					direction = str(scan_data['PhaseEncodingDirection']) # get the phase encoding direction for this fieldmap
					if direction == 'j':
						direction = "PA"  # 'j' corresponds to the Posterior -> Anterior fieldmap direction
					elif direction == 'j-':
						direction = "AP"  # 'j-' corresponds to the Anterior -> Posterior fieldmap direction
					os.rename(fieldmap_folder + "/%s" % file, fieldmap_folder + "/sub-%s%s%s_dir-%s_epi.nii.gz" % (id_prefix, participant_00X, ses, direction))
					os.rename(fieldmap_folder + "/%s.json" % file[:-7], fieldmap_folder + "/sub-%s%s%s_dir-%s_epi.json" % (id_prefix, participant_00X, ses, direction))

	renamed_func_files = []
	for file in renamed_func_files_all:
		if "bold" in file:
			if ".nii" in file:
				if multi_session:
					splits = func_folder.split("/")
					session_folder = splits[-2]
					prefix = session_folder + "/func/"
				else:
					prefix = "func/"
				renamed_func_files.append(prefix + file)  # this is a list of all BOLD runs (task + resting state) to add to the json files for the fieldmaps (below)



	renamed_fieldmap_files = os.listdir(fieldmap_folder)
	if any("epi" in x for x in renamed_fieldmap_files):
		for file in renamed_fieldmap_files:
			if ".json" in file:
				with open(fieldmap_folder + "/%s" % file, 'r') as f:
					data = json.load(f)
					data['IntendedFor'] = renamed_func_files  # Add all the BOLD runs (task + resting state) which correspond to this fieldmap to its .json

				os.remove(fieldmap_folder + "/%s" % file)
				with open(fieldmap_folder + "/%s" % file, 'w') as f:
					json.dump(data, f, indent=4)


	if len(fieldmap_files) > 4:  # If there is more than a single pair of AP/PA fieldmap files (with their .json files)
		print("XXXXXXXXXX\nCareful! You have acquired multiple pairs of fieldmap files. You will need to modify the 'IntendedFor' section of their corresponding .json files to specify which BOLD runs they are for.\nXXXXXXXXXX")


	print("Session %s NIfTI files relocated in subfolders\n" % session)

	shutil.rmtree(nifti_folder)  # now that all relevant NIfTI files have been relocated and renamed, delete the folder with any remaining (unnecessary) NIfTI files

	# If there are any empty folder now (for example, no anat file from this session), delete the empty folder
	if not os.listdir(anat_folder):
		os.rmdir(anat_folder)
	if not os.listdir(func_folder):
		os.rmdir(func_folder)
	if not os.listdir(fieldmap_folder):
		os.rmdir(fieldmap_folder)