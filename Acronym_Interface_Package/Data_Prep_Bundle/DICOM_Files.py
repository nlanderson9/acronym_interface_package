####################################################################################################################
# ===File download and Backup Upload=== #
# Downloads DICOM file(s) from the CNDA and backs them up to Icarus
####################################################################################################################


from Tkinter import *
import os, datetime, subprocess, sys, zipfile, shutil, dicom


def notification(text):
	root = Tk()  # create TKinter window
	root.title("Download/Backup update")
	root.geometry('+1070+500')  # sets the location of the window - format (+horiz+vert)
	root.wm_attributes("-topmost", 1)  # makes sure that the window appears on top of all other windows
	label = Label(root)
	label.pack()
	label.config(text=str(text))
	root.after(5000, lambda: root.destroy())
	root.mainloop()


##########################################################
# ===Download DICOMs from CNDA=== #
##########################################################

def CNDA_download(show_notifications, multi_session, session, dicom_folder, id_prefix, participant_00X, vcnumber, CNDA_Auto, CNDA_login, CNDA_password, project_name, day, month, year):
	if not os.path.exists(dicom_folder + "/%s.zip" % vcnumber):
		CNDA_starttime = datetime.datetime.now() # start time of CNDA download
		# change directory to target directory and use "curl" to download the specified CNDA file into a .zip
		if multi_session:
			print('\nDownloading DICOM files for %s (Participant sub-%s%s, Session %s) from CNDA to local machine' % (vcnumber, id_prefix, participant_00X, session))
		else:
			print('\nDownloading DICOM files for %s (Participant sub-%s%s) from CNDA to local machine' % (vcnumber, id_prefix, participant_00X))
		print('Start time: %s\n' % CNDA_starttime.strftime("%m-%d-%Y, %I:%M:%S %p"))
		if CNDA_Auto:
			subprocess.call(['cd %s && curl -k -u %s:%s "https://cnda.wustl.edu/REST/projects/%s/experiments/%s/DIR/SCANS?format=zip&recursive=true" > %s.zip' % (
				dicom_folder, CNDA_login, CNDA_password, project_name, vcnumber, vcnumber)], shell=True)
		else:
			subprocess.call(['cd %s && curl -k -u %s:%s "https://cnda.wustl.edu/REST/projects/%s/experiments/%s_%s%s_%s/DIR/SCANS?format=zip&recursive=true" > %s.zip' % (
				dicom_folder, CNDA_login, CNDA_password, project_name, vcnumber, month, day, year, vcnumber)], shell=True)
		if CNDA_starttime > datetime.datetime.now()-datetime.timedelta(seconds=60): # if the CNDA download took less than 60 seconds, something probably went wrong
			if show_notifications:
				notification('\nYour download failed\n')
			sys.exit("XXXXXXXXXX\nCNDA download failed!\nXXXXXXXXXX")
		if show_notifications:
			notification('\nYour download is finished!\n')
		if multi_session:
			print('\n%s.zip downloaded - DICOM files for sub-%s%s, Session %s' % (vcnumber, id_prefix, participant_00X, session))
		else:
			print('\n%s.zip downloaded - DICOM files for sub-%s%s' % (vcnumber, id_prefix, participant_00X))
	else:
		print ("%s.zip file already in folder" % vcnumber)

	# extract the files from the .zip
	zip_ref = zipfile.ZipFile('%s/%s.zip' % (dicom_folder, vcnumber), 'r')
	zip_ref.extractall(dicom_folder)
	zip_ref.close()


# All CNDA DICOM files are downloaded in the following file structure:
# e.g. abcd/sub-abcd001/DICOM/vc99999/SCANS/1/DICOM/ - where "1" refers to the given scan's folder of DICOMs


##########################################################
# ===Back up DICOMs to Icarus=== #
##########################################################

def DICOM_backup(show_notifications, multi_session, session, Icarus_password, dicom_folder, id_prefix, participant_00X, vcnumber, Icarus_login, Icarus_folder):
	backupfail = False
	Icarus_starttime = datetime.datetime.now()
	if multi_session:
		print('\nBacking up %s.zip archive from local machine to Icarus (containing DICOM files for Participant sub-%s%s, Session %s)' % (vcnumber, id_prefix, participant_00X, session))
	else:
		print('\nBacking up %s.zip archive from local machine to Icarus (containing DICOM files for Participant sub-%s%s, Session %s)' % (
			vcnumber, id_prefix, participant_00X, session))
	print('Start time: %s\n' % Icarus_starttime.strftime("%m-%d-%Y, %I:%M:%S %p"))
	subprocess.call(["/usr/local/bin/sshpass -p '%s' scp %s/%s.zip %s@icarus.neuroimage.wustl.edu:%s" % (
		Icarus_password, dicom_folder, vcnumber, Icarus_login, Icarus_folder)], shell=True)
	if Icarus_starttime > datetime.datetime.now()-datetime.timedelta(seconds=60):  # if the Icarus backup took less than 60 seconds, something probably went wrong
		print("XXX  Warning - Icarus backup failed\n%s.zip not deleted, try backup again  XXX" % (vcnumber))
		backupfail = True
		if show_notifications:
			notification("\nYour Icarus backup failed\n")
	else:
		if show_notifications:
			notification("\nYour Icarus backup is finished!\n")
		if multi_session:
			print('\n%s.zip backed up to Icarus - DICOM files for sub-%s%s, Session %s (located at %s/%s.zip)' % (vcnumber, id_prefix, participant_00X, session, Icarus_folder, vcnumber))
		else:
			print('\n%s.zip backed up to Icarus - DICOM files for sub-%s%s (located at %s/%s.zip)' % (vcnumber, id_prefix, participant_00X, Icarus_folder, vcnumber))

	# delete unnecessary .zip file
	if backupfail:
		pass  # don't delete the zip file yet if it didn't successfully backup to Icarus
	else:
		os.remove('%s/%s.zip' % (dicom_folder, vcnumber))