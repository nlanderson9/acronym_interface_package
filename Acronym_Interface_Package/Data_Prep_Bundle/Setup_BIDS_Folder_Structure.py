####################################################################################################################
# ===Create Initial Folders=== #
# These creates the initial consistent file structure for this participant/session, according to BIDS format
####################################################################################################################


import os

def make_folders(top_folder):
	global folder_create_count

	##########
	# BIDS-specified folders (all required):
	anat_folder = top_folder + "/anat"  # anatomical data
	if not os.path.exists(anat_folder):
		os.makedirs(anat_folder)
		folder_create_count = + 1

	fieldmap_folder = top_folder + "/fmap"  # fieldmaps
	if not os.path.exists(fieldmap_folder):
		os.makedirs(fieldmap_folder)
		folder_create_count = + 1

	func_folder = top_folder + "/func"  # task scans, resting state scans, task event files
	if not os.path.exists(func_folder):
		os.makedirs(func_folder)  # BOLD data
		folder_create_count = + 1

	##########
	# Transient folders (created to organize data, will be deleted later by script):
	dicom_folder = top_folder + "/DICOM"  # DICOM files (downloaded from CNDA)
	if not os.path.exists(dicom_folder):
		os.makedirs(dicom_folder)
		folder_create_count = + 1
	nifti_folder = top_folder + "/NIfTI"  # NIfTI files (output from dmc2niix)
	if not os.path.exists(nifti_folder):
		os.makedirs(nifti_folder)
		folder_create_count = + 1



def create_folders(folder, id_prefix, participant_00X, multi_session, number_of_sessions, download_selections):

	folder_create_count = 0

	# create participant folder
	participant_folder = folder + "/sub-" + id_prefix + participant_00X  # /ERwD/sub-erwd001
	if not (os.path.exists(participant_folder)):  # if we haven't already created the participant folder
		os.makedirs(participant_folder)  # make the participant folder
		folder_create_count = + 1

	if multi_session:
		for session in range(1, number_of_sessions + 1):
			for item in download_selections:
				if (" " + str(session)) in item:
					session_sub_folder = participant_folder + "/ses-0%s" % session
					if not os.path.exists(session_sub_folder):
						os.makedirs(session_sub_folder)
					make_folders(session_sub_folder)

	else:
		make_folders(participant_folder)

	##########
	# Optional folder(s):
	AFNI_timing_files_folder = participant_folder + "/AFNI_timing_files"  # timing files
	if not os.path.exists(AFNI_timing_files_folder):
		os.makedirs(AFNI_timing_files_folder)
		folder_create_count = + 1


	if folder_create_count > 0:
		print("Necessary subfolders created")