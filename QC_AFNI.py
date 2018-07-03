#!/usr/bin/python

import os, glob, subprocess, shutil, sys
from datetime import datetime
from Tkinter import *
from tkFileDialog import askdirectory

# The purpose of this script is to execute a number of QC (quality control) functions.
# The output of these files will be placed in a "QC_AFNI" folder inside of the "subject_results" folder.

duration_string = ""
# Function for printing a string with the elapsed time
def time_duration(starttime, currenttime):
    global duration_string
    duration_string = ""
    totaltime = currenttime - starttime
    if "day" in str(totaltime):
        time_days = int(str(totaltime)[:1])
    else:
        time_days = 0
    time_minutes = (totaltime.seconds - (totaltime.seconds % 60)) / 60
    if time_minutes > 59:
        minutes_left = time_minutes % 60
        time_hours = (time_minutes - minutes_left) / 60
        time_minutes = minutes_left
    else:
        time_hours = 0
    time_seconds = totaltime.seconds % 60
    if time_days > 0:
        duration_string = duration_string + str(time_days) + " day"
    if time_days > 1:
        duration_string = duration_string + "s"
    if time_days > 0:
        duration_string = duration_string + ", "
    if time_days > 0 or time_hours > 0:
        duration_string = duration_string + str(time_hours) + " hour"
        if time_hours != 1:
            duration_string = duration_string + "s"
        duration_string = duration_string + ", "
    if time_days > 0 or time_hours > 0 or time_minutes > 0:
        duration_string = duration_string + str(time_minutes) + " minute"
        if time_minutes != 1:
            duration_string = duration_string + "s"
	if time_days > 0 or time_hours > 0:
		duration_string = duration_string + ", "
    if duration_string:
        duration_string = duration_string + " and "
    duration_string = duration_string + str(time_seconds) + " second"
    if time_seconds != 1:
        duration_string = duration_string + "s"


starttime = datetime.now()
print_starttime = starttime.strftime("%m-%d-%Y, %I:%M:%S %p")
print("Begin script execution: " + str(print_starttime))


####################
# Screen Size
####################

# This is used to determine the size of your main screen
screensize_test = Tk()
pointer = screensize_test.winfo_pointerxy()
screensize_test.geometry('+%s+%s' % (pointer[0], pointer[1]))
screensize_test.update()
screensize_test.attributes("-alpha", 00)
screensize_test.state('zoomed')
screenheight = screensize_test.winfo_height()
screenwidth = screensize_test.winfo_width()
screenx = screensize_test.winfo_rootx()
screeny = screensize_test.winfo_rooty()
screensize_test.after(1, lambda: screensize_test.destroy())
mainloop()


####################
# Select subject results directory
####################

subject_results = None

long_scripts_check = None

def entry_fields():
	global subject_results, long_scripts_check
	subject_results = e1.get()
	long_scripts_check = var1.get()
	master.destroy()

def sel1():
	global coord_system_selection
	coord_system_selection = str(var1.get())

def path_choose1():
    filepath1 = askdirectory()
    e1.delete(0, 'end')
    e1.insert(0, filepath1)

def exitscript():
	sys.exit()

master = Tk()
master.title("Input info")
master.geometry('+1070+500')
master.wm_attributes("-topmost", 1)

var1 = IntVar()

Label(master, text='Path to your subject results folder').grid(row=1, padx=20, columnspan=2)
e1 = Entry(master, width=50)
e1.grid(row=2, padx=20, columnspan=2)
button1 = Button(master, text="Browse", command=path_choose1).grid(row=3, column=0, columnspan=2)

Label(master, text='').grid(row=4)

backup_button = Checkbutton(master, text='Do not create review tables for GLMs with 50+ conditions\n(this can significantly speed up this script)', variable = var1).grid(row=5, column=0, columnspan=2)

Label(master, text='').grid(row=6)

Button(master, text='Begin QC processing', command=entry_fields).grid(row=7, sticky=S,
														 pady=4, columnspan=2)
Button(master, text='Cancel', command=exitscript).grid(row=8, sticky=S,
														 pady=4, columnspan=2)

master.update_idletasks()
windowheight = master.winfo_height()
windowwidth = master.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
master.geometry("+%s+%s" % (positionRight, positionDown))
master.wm_attributes("-topmost", 0)

mainloop()

####################


QC_folder = os.path.join(subject_results, "QC_AFNI")
if not os.path.exists(QC_folder):
	os.makedirs(QC_folder
)  # create QC folder

FNULL = open(os.devnull, 'w')  # used to suppress terminal command output


########## moving files ##########

## move output.proc files ##

outputs_folder = QC_folder + "/proc_outputs"
if not os.path.exists(outputs_folder):
	os.makedirs(outputs_folder)  # create proc outputs folder

print("copying proc script output files.....")
parent = os.path.dirname(subject_results)
output_files_list1 = glob.glob(os.path.join(parent, "*output*"))
output_files_list2 = glob.glob(os.path.join(parent, "output*"))
output_files_list = output_files_list1 + output_files_list2
for output_file in output_files_list:
	subprocess.call("cp -n %s %s" % (output_file, outputs_folder), shell=True)  # copy all files beginning with "output" into QC folder

## move dfile_rall

Dfile_folder = QC_folder + "/dfiles"
if not os.path.exists(Dfile_folder):
	os.makedirs(Dfile_folder)  # create dfile folder

subject_folders = os.listdir(subject_results)  # list subject folders inside subject_results
subject_folders1 = [x for x in subject_folders if ("subj" in x)]  # only keep those containing "subj"
subject_folders1 = sorted(subject_folders1)
print("copying subject motion files.....")
for folder in subject_folders1:
	results_folder = os.listdir(os.path.join(subject_results, folder))  # find each subject's results folder
	results_folder = [x for x in results_folder if not (".DS_Store" in x)]
	dfile = os.path.join(subject_results, folder, results_folder[0], "*.dfile_rall.1D")
	subprocess.call("cp -n %s %s" % (dfile, Dfile_folder), shell=True)  # copy the overall movement file for each subject into the QC folder


########## gen_ss_review_table.py ##########

print("creating review files....")

all_GLM_folders = []

Review_table_folder = QC_folder + "/review_tables"
if not os.path.exists(Review_table_folder):
	os.makedirs(Review_table_folder)  # create review table folder


for folder in subject_folders1:
	subj_number = folder[5:]

	results_folders = os.listdir(os.path.join(subject_results, folder))
	results_folders = [x for x in results_folders if not (".DS_Store" in x)]
	results_folder = os.path.join(subject_results, folder, results_folders[0])
	potential_folders = os.listdir(results_folder)
	GLM_folders = []
	for potential_folder in potential_folders:
 		check = glob.glob(os.path.join(results_folder, potential_folder, "stats*"))  # check to see if any of the folders has a stats file inside
		if check:
			GLM_folders.append(potential_folder)  # if it has a stats file inside, add it to "GLM_folders"
	GLM_folders = sorted(GLM_folders)
	GLM_folders_int = []
	for GLM_folder in GLM_folders:
		if not os.path.exists(os.path.join(Review_table_folder, "review_table_" + GLM_folder + ".xls")):
			GLM_folders_int.append(GLM_folder)  # don't do this GLM if the review table already exists
	GLM_folders = GLM_folders_int

	if long_scripts_check:
		for GLM_folder in GLM_folders:
			stats_file = os.path.join(results_folder, GLM_folder, "stats.%s+tlrc.HEAD" % subj_number)
			proc = subprocess.Popen("3dinfo -label %s" % (stats_file), shell=True, stdout=subprocess.PIPE)
			label_names = proc.stdout.read()
			name_list = label_names.split("|")
			stat_condition_list = [fn for fn in name_list if "Coef" in fn]
			if len(stat_condition_list) > 50:
				GLM_folders.remove(GLM_folder)  # if there are a large number of stimulus conditions, do not run this GLM

	for GLM_folder in GLM_folders:
		if GLM_folder not in all_GLM_folders:
			all_GLM_folders.append(GLM_folder)  # create a final list of all GLM folders used, regardless of participant

	if GLM_folders:
		time1 = datetime.now()
		time_duration(starttime, time1)
		print("***" + subj_number + "..." + duration_string + " elapsed")

	for GLM_folder in GLM_folders:
		print(GLM_folder + "....")
		subprocess.call('cd %s && rm out.ss_review.*' % (results_folder), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)  # delete old out.ss_review files
		subprocess.call('cd %s && rm @ss_review*' % (results_folder), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)  # delete old @ss_review commands
		review_files_folder = os.path.join(results_folder, GLM_folder, "review_files")
		if not os.path.exists(review_files_folder):
			os.makedirs(review_files_folder)
		else:
			shutil.rmtree(review_files_folder)
			os.makedirs(review_files_folder)
		results_GLM_folder = os.path.join(results_folder, GLM_folder)
		subprocess.call('cd %s && cp X.xmat.1D %s' % (results_GLM_folder, results_folder), shell=True)  # copy the X.xmat.1D file up to the main subject directory
		subprocess.call('cd %s && cp X.stim.xmat.1D %s' % (results_GLM_folder, results_folder), shell=True)   # copy the X.stim.xmat.1D file up to the main subject directory
		Xnocensor_file = os.path.join(GLM_folder, "X.nocensor.xmat.1D")
		stats_file = os.path.join(GLM_folder, "stats.%s+tlrc.HEAD" % subj_number)
		sumideal_file = os.path.join(GLM_folder, "sum_ideal.1D")
		tsnr_file = os.path.join(GLM_folder, "TSNR.%s+tlrc.HEAD" % subj_number)
		outgcor_file = os.path.join(GLM_folder, "out.gcor.1D")
		errts_file = os.path.join(GLM_folder, "errts.%s+tlrc.HEAD" % subj_number)
		subprocess.call('cd %s && gen_ss_review_scripts.py -mot_limit 0.3 -exit0 -out_limit 0.1 -uvar xmat_uncensored %s -uvar stats_dset %s -motion_dset %s.dfile_rall.1D -uvar sum_ideal %s -uvar tsnr_dset %s -uvar gcor_dset %s -xmat_regress X.xmat.1D -censor_dset motion_%s_censor.1D -errts_dset %s' % (results_folder, Xnocensor_file, stats_file, subj_number, sumideal_file, tsnr_file, outgcor_file, subj_number, errts_file), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)  # run AFNI's gen_ss_review_scripts.py
		subprocess.call('cd %s && ./@ss_review_basic > out.ss_review.%s.%s.txt' % (results_folder, subj_number, GLM_folder), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)  # execute @ss_review_basic to get text output
		
		mv_out_ss_review = os.path.join(results_folder, "out.ss_review.*")
		mv_ss_review_basic = os.path.join(results_folder, "@ss_review_basic")
		mv_ss_review_driver = os.path.join(results_folder, "@ss_review_driver")
		mv_ss_review_driver_commands = os.path.join(results_folder, "@ss_review_driver_commands")
		subprocess.call('mv %s %s' % (mv_out_ss_review, review_files_folder), shell=True)  # move output to dedicated folder
		subprocess.call('mv %s %s' % (mv_ss_review_basic, review_files_folder), shell=True)  # move output to dedicated folder
		subprocess.call('mv %s %s' % (mv_ss_review_driver, review_files_folder), shell=True)  # move output to dedicated folder
		subprocess.call('mv %s %s' % (mv_ss_review_driver_commands, review_files_folder), shell=True)  # move output to dedicated folder
		subprocess.call('cd %s && rm X*xmat.1D' % (results_folder), shell=True)  # delete copied X.xmat.1D and X.stim.xmat.1D files


print("creating review tables....")

for GLM_folder in all_GLM_folders:
	all_out_ss_review = os.path.join("subject_results", "*", "*", GLM_folder, "review_files", "out.ss_review.*")
	subprocess.call("cd %s && gen_ss_review_table.py -tablefile review_table.xls -overwrite -infiles %s" % (parent, all_out_ss_review), shell=True)  # run gen_ss_review_table.py
	review_table = os.path.join(parent, "review_table.xls")
	review_table_move = os.path.join(Review_table_folder, "review_table_%s.xls" % GLM_folder)
	subprocess.call("mv %s %s " % (review_table, review_table_move) , shell=True)  # move the result to the QC folder


########## create snapshots ##########
# loops through AFNI command @snapshot_volreg, then organizes resulting jpgs

print("creating alignment snapshots....")

snapshot_folder = QC_folder + "/snapshots"
if not os.path.exists(snapshot_folder):
	os.makedirs(snapshot_folder)

for folder in subject_folders1:
	subj_number = folder[5:]
	results_folder = os.path.join(subject_results, "subj." + subj_number, subj_number + ".results")
	result_files = os.listdir(results_folder)
	result_files1 = [x for x in result_files if ("pb" in x)]  # find all processing-block files 
	result_files1 = [x for x in result_files1 if ("volreg" in x)]  # find all processing-block files from the "volreg" block
	result_files1 = [x for x in result_files1 if ("HEAD" in x)]  # only keep the HEAD files, to avoid doubles (with the BRIK files)
	result_files1 = sorted(result_files1)
	number_of_runs = len(result_files1)

	warped_anat_path = os.path.join(results_folder, "anat_mprage_unif_ns_shft+tlrc.HEAD")  # this is the anatomical file immediately after being warped to the template
	proc = subprocess.Popen("3dinfo -history %s" % (warped_anat_path), shell=True, stdout=subprocess.PIPE)  # search the file's history to find what template was used
	history = proc.stdout.read()
	splits = history.split(" ")
	count = 0
	template = None
	for item in splits:
		if item == "-base":
			template = splits[count +1]  # the item after "-base" in the command is the file name of the anatomical template
		count += 1

	if template.endswith(".HEAD"):
		template = template[:-5]

	#copy the necessary template file to the current directory, if not already copied
	if not os.path.exists(os.path.join(results_folder, template + ".HEAD")):
		subprocess.call("cp ~/abin/%s* %s" % (template, results_folder), shell=True)
	
	anat = "anat_final.%s+tlrc" % subj_number
	
	run_0_list = []
	for run in range(number_of_runs):
		if run < 9:
			run_0 = "0" + str(run+1)
			run_0_list.append(run_0)
		else:
			run_0 = str(run+1)
			run_0_list.append(run_0)

	run_0_list = sorted(run_0_list)

	epi_files = dict(zip(run_0_list, result_files1))

	time1 = datetime.now()
	time_duration(starttime, time1)

	do_snapshots = False
	if not os.path.exists(os.path.join(snapshot_folder, subj_number + "_anat-template.jpg")):
		do_snapshots = True
	for run in run_0_list:
		jpg_name = "%s_run%s-anat" % (subj_number, run)
		if not os.path.exists(os.path.join(snapshot_folder, jpg_name + ".jpg")):
			do_snapshots = True

	if do_snapshots:
		print("creating snapshots for " + subj_number + "..." + duration_string + " elapsed")

	jpg_name = "%s_anat-template" % subj_number
	if not os.path.exists(os.path.join(snapshot_folder, jpg_name + ".jpg")):
		subprocess.call("cd %s && @snapshot_volreg %s %s %s" % (results_folder, template, anat, jpg_name), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
		print("output file:  %s.jpg" % jpg_name)
		anat_jpg_path = os.path.join(results_folder, "*_anat-template.jpg")
		subprocess.call("mv %s %s" % (anat_jpg_path, snapshot_folder), shell=True, stdout=FNULL, stderr=subprocess.STDOUT) # move snapshot to correct folder in QC folder

	for run in run_0_list:
		run_file_name = epi_files[run][:-5]  # remove .HEAD from file name
		jpg_name = "%s_run%s-anat" % (subj_number, run)
		if not os.path.exists(os.path.join(snapshot_folder, jpg_name + ".jpg")):
			subprocess.call("cd %s && @snapshot_volreg %s %s %s" % (results_folder, anat, run_file_name, jpg_name), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
			print("output file:  %s.jpg" % jpg_name)
			epi_jpg_paths = os.path.join(results_folder, "*_run*-anat.jpg")
			subprocess.call("mv %s %s" % (epi_jpg_paths, snapshot_folder), shell=True, stdout=FNULL, stderr=subprocess.STDOUT) # move snapshots to correct folder in QC folder
	
	subprocess.call("rm %s*" % os.path.join(results_folder, template), shell=True)

	
	
	

########## create radial correlations ##########
# loops through the results of @radial_correlate and summarizes them in a text file
if not os.path.exists(os.path.join(QC_folder, "radial_correlate_summary.txt")):
	print("creating radial_correlate summary.....")
	final_output = QC_folder + "/radial_correlate_summary.txt"
	final_output_write = open(final_output, "w")

	for folder in subject_folders1:
		subj_number = folder[5:]
		results_folder = os.path.join(subject_results, "subj." + subj_number, subj_number + ".results")
		output_files = glob.glob(os.path.join(results_folder, "output.radial_correlate*")) # finds output files from @radial_correlate
		output_file = output_files[0] # grabs first (hopefully only!) result
		textfile = open(output_file, 'r')
		text = textfile.read()	
		start_index = text.find("============================================================") # all relevant info is contained within blocks of "===="
		end_index = text.find("============================================================", (start_index + 1))	
		final_output_write.write(text[start_index:(end_index+61)])
		final_output_write.write("\n") # create a new line so the file is ready to write the next participant on the next loop
		textfile.close()
	final_output_write.close()


########## create motion and outlier plots ##########

Mot_out_folder = QC_folder + "/motion_outlier_plots"
if not os.path.exists(Mot_out_folder):
	os.makedirs(Mot_out_folder)  # create motion & outlier plot folder

for folder in subject_folders1:
	subj_number = folder[5:]
	results_folder = os.path.join(subject_results, "subj." + subj_number, subj_number + ".results")
	outcount_file = os.path.join(results_folder, "outcount_rall.1D")
	motion_files = glob.glob(os.path.join(results_folder, "motion_*_enorm.1D"))
	motion_file = motion_files[0]
	censor_files = glob.glob(os.path.join(results_folder, "motion_*_censor.1D"))
	censor_file = censor_files[0]
	if not os.path.exists(os.path.join(Mot_out_folder, subj_number + "_outliers.jpg")) or not os.path.exists(os.path.join(Mot_out_folder, subj_number + "_motion.jpg")):
		print("creating motion and outlier plots for %s....." % subj_number)
	if not os.path.exists(os.path.join(Mot_out_folder, subj_number + "_outliers.jpg")):
		subprocess.call('cd %s && 1dplot -one -plabel %s_outliers -censor_RGB green -censor %s -jpg %s_outliers %s "1D: 2319@0.1"' % (results_folder, subj_number, censor_file, subj_number, outcount_file), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)  # use AFNI's 1dplot to create outlier plot
		outliers = os.path.join(results_folder, "*outliers.jpg")
		subprocess.call("mv %s %s" % (outliers, Mot_out_folder), shell=True)  # move plots to dedicated folder in QC folder
	if not os.path.exists(os.path.join(Mot_out_folder, subj_number + "_motion.jpg")):
		subprocess.call('cd %s && 1dplot -one -plabel %s_motion -censor_RGB green -censor %s -jpg %s_motion %s "1D: 2319@0.3"' % (results_folder, subj_number, censor_file, subj_number, motion_file), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)  # use AFNI's 1dplot to create motion plot
		motion = os.path.join(results_folder, "*motion.jpg")
		subprocess.call("mv %s %s" % (motion, Mot_out_folder), shell=True)  # move plots to dedicated folder in QC folder



endtime = datetime.now()
print_endtime = endtime.strftime("%m-%d-%Y, %I:%M:%S %p")
print("End script execution: " + str(print_endtime))

time_duration(starttime, endtime)
print("Total script duration: " + duration_string)