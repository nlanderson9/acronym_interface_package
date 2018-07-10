#!/usr/bin/python

import os
import glob
import subprocess
import csv
import numpy
from datetime import datetime
from operator import add
from scipy import stats
from Tkinter import *
import time
from tkFileDialog import askdirectory


# The purpose of this script is to extract averaged ROI magnitudes and timecourses in AFNI
# ROIs can be defined by either a coordinate (around which a sphere is drawn) or by a pre-defined mask in AFNI

# All coordinates should be saved in .txt files, in this format:
# ROIname.txt (eg. "precuneus.txt" or "apriori_midcingulate.txt") with no spaces
# The file should contain 3 numbers in LPI or RAI order (based on your dataset), separated by spaces or commas (e.g. "-5 42.5 21" without quotes)

# All mask files should be pairs of AFNI .HEAD/.BRIK files, comprising a masked region


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


####################
# Import Presets
####################


path = os.path.dirname(os.path.realpath(__file__))  # this script's directory path

presets_control_file = os.path.join(path, "presets_control_file.txt")

with open(presets_control_file) as control_file:
	presets_init = control_file.read().splitlines()
presets = {}
for item in presets_init:
	splits = item.split(":")
	presets[splits[0]] = splits[1]

input_subject_results_path = presets['subject_results_path']
input_masks_path = presets['masks_path']
input_coord_system = presets['coord_system']
input_sphere_radius = presets['sphere_radius']


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
# Select analyses
####################

analysis_choices = ['Sphere from coordinate (magnitude)',
					'Sphere from coordinate (timecourse)',
					'Pre-defined mask (magnitude)',
					'Pre-defined mask (timecourse)']

buttons_list = analysis_choices
buttons = {}
for item in buttons_list:
	buttons[item] = 0
buttons_outcome = {}


root = Tk()  # create TKinter window
root.update_idletasks()
root.title("Analysis Selection")
root.geometry('+1070+500')  # sets the location of the window - format (+horiz+vert)
root.wm_attributes("-topmost", 1)  # makes sure that the window appears on top of all other windows

def end():
	for item in buttons:
		buttons_outcome[item] = buttons[item].get()
	root.destroy()


Label(root, text="Choose the analyses to execute:").grid(row=1)
Label(root, text="").grid(row=2)
row = 3
for button in buttons_list:
	buttons[button] = IntVar()
	user_button = Checkbutton(root, text=button, variable=buttons[button])
	user_button.grid(row=row, column=0, sticky="w", padx=20, pady=5)
	row += 1
endbutton = Button(root, text="Submit", width=25, command=end).grid(row=row, column=0, padx=20)
button1 = Button(root, text='Quit',width=25, command=sys.exit).grid(row=(row+1), column=0, pady=5)

root.update_idletasks()
windowheight = root.winfo_height()
windowwidth = root.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
root.geometry("+%s+%s" % (positionRight, positionDown))

root.mainloop()

use_buttons = []
for item in buttons_outcome:
	if buttons_outcome[item] == 1:
		use_buttons.append(item)

analyses = use_buttons
if not analyses:  # if no options were selected:
	sys.exit("You must choose at least one option to proceed.")


####################
# Confirm paths and coord system
####################

subject_results = None
masks_path = None
coord_system = None
sphere_radius = None

coord_system_selection = None

def entry_fields():
	global subject_results, masks_path, sphere_radius
	subject_results = e1.get()
	masks_path = e2.get()
	if analysis_choices[0] in analyses or analysis_choices[1] in analyses:
		sphere_radius = e3.get()
	master.destroy()

def sel1():
	global coord_system_selection
	coord_system_selection = str(var1.get())

def path_choose1():
    filepath1 = askdirectory()
    e1.delete(0, 'end')
    e1.insert(0, filepath1)

def path_choose2():
    filepath2 = askdirectory()
    e2.delete(0, 'end')
    e2.insert(0, filepath2)

def exitscript():
	sys.exit()

master = Tk()
master.title("Input info")
master.geometry('+1070+500')
master.wm_attributes("-topmost", 1)
master.wm_attributes("-topmost", 0)

var1 = IntVar()
if input_coord_system == "LPI":
	var1.set(1)
	coord_system_selection = str(var1.get())
elif input_coord_system == "RAI":
	var1.set(2)
	coord_system_selection = str(var1.get())

Label(master, text='Path to your subject results folder').grid(row=1, padx=20, columnspan=2)
e1 = Entry(master, width=50)
e1.insert(0, input_subject_results_path)
e1.grid(row=2, padx=20, columnspan=2)
button1 = Button(master, text="Browse", command=path_choose1).grid(row=3, column=0, columnspan=2)

Label(master, text='').grid(row=4)

Label(master, text='Path to directory containing AFNI mask file(s) and/or text file(s) with ROI coordinates').grid(row=5, padx=20, columnspan=2)
e2 = Entry(master, width=50)
e2.insert(0, input_masks_path)
e2.grid(row=6, padx=20, columnspan=2)
button4 = Button(master, text="Browse", command=path_choose2).grid(row=7, column=0, columnspan=2)

if analysis_choices[0] in analyses or analysis_choices[1] in analyses:
	Label(master, text='').grid(row=8)

	Label(master, text='').grid(row=12)

	Label(master, text='Coordinate system:  ').grid(row=13, column=0, rowspan=2, sticky=E)
	Radiobutton(master, text="LPI (SPM order)", variable=var1, value=1, command=sel1).grid(row=13, column=1, sticky=W)
	Radiobutton(master, text="RAI (DICOM order)", variable=var1, value=2, command=sel1).grid(row=14, column=1, sticky=W)

	Label(master, text='').grid(row=15)

	Label(master, text='Sphere radius (mm):  ').grid(row=16, column=0, sticky=E)
	e3 = Entry(master, width=3)
	e3.insert(0, input_sphere_radius)
	e3.grid(row=16, column=1, sticky=W)

Label(master, text='').grid(row=17)

Button(master, text='Submit', command=entry_fields).grid(row=18, sticky=S,
														 pady=4, columnspan=2)
Button(master, text='Cancel', command=exitscript).grid(row=19, sticky=S,
														 pady=4, columnspan=2)

master.update_idletasks()
windowheight = master.winfo_height()
windowwidth = master.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
master.geometry("+%s+%s" % (positionRight, positionDown))

mainloop()


if analysis_choices[0] in analyses or analysis_choices[1] in analyses:
	if coord_system_selection == "1":
		coord_system = "LPI"
	elif coord_system_selection == "2":
		coord_system = "RAI"

if analysis_choices[0] in analyses or analysis_choices[1] in analyses:
	try:
		sphere_radius = int(sphere_radius)
	except:
		sys.exit("Please make sure you provide an integer for your sphere radius.")


####################################################################################################
##### Updating Presets Control List #####

if not analysis_choices[0] in analyses and not analysis_choices[1] in analyses:
	coord_system = input_coord_system
	sphere_radius = input_sphere_radius
if not analysis_choices[2] in analyses and not analysis_choices[3] in analyses:
	masks_path = input_masks_path

new_control_list = ['subject_results_path:' + subject_results,
					'masks_path:' + masks_path,
					'coord_system:' + coord_system,
					'sphere_radius:' + str(sphere_radius)]

with open(presets_control_file, 'w') as control_file:
	control_file.writelines('\n'.join(new_control_list))


####################

FNULL = open(os.devnull, 'w')   # used to suppress terminal command output
subject_folders = os.listdir(subject_results)  # list subject folders inside subject_results
subject_folders1 = [x for x in subject_folders if ("subj" in x)]  # only keep those containing "subj"
subject_folders1 = [x for x in subject_folders1 if not (".DS_Store" in x)]
subject_folders1 = sorted(subject_folders1)  # order the folders alphabetically

##########
# Choose which participants are included
##########

button_list = []
for item in subject_folders1:
	button_list.append(item[5:])

buttons = {}
for item in button_list:
	buttons[item] = 0
buttons_outcome = {}


def end():
	for item in buttons:
		buttons_outcome[item] = buttons[item].get()
	master.destroy()

def selectall():  # button function that selects all checkboxes
	for item in buttons:
		buttons[item].set(1)

def unselectall():  # button function that unselects all checkboxes
	for item in buttons:
		buttons[item].set(0)

def exitscript():
	sys.exit()


master = Tk()
master.title("Participant Selection")
master.geometry('+1070+500')  # sets the location of the window - format (+horiz+vert)
master.wm_attributes("-topmost", 1)  # makes sure that the window appears on top of all other windows
label = Label(master, padx=20)
label.grid(row=1)
label.config(text=str('Select the participants you would like to include:'))

selectbutton = Button(master, text='Select all', command=selectall).grid(row=2)
unselectbutton = Button(master, text='Unselect all', command=unselectall).grid(row=3)

label0 = Label(master, padx=10).grid(row=4)

for item in buttons:
	buttons[item] = IntVar()
	buttons[item].set(1)
	user_button = Checkbutton(master, text=item, variable=buttons[item])
	user_button.grid(row=(5 + subject_folders1.index("subj." + item)))

row_loop = 5 + len(buttons)
label1 = Label(master, padx=10).grid(row=row_loop)
row_loop += 1
btn = Button(master, text="OK", command=end).grid(row=row_loop)
row_loop += 1
btn1 = Button(master, text="Cancel", command=exitscript).grid(row=row_loop)

master.update_idletasks()
windowheight = master.winfo_height()
windowwidth = master.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
master.geometry("+%s+%s" % (positionRight, positionDown))

mainloop()

subject_folders1 = []
for item in buttons_outcome:
	if buttons_outcome[item] == 1:
		subject_folders1.append("subj." + item)

subject_folders1 = sorted(subject_folders1)  # order the folders alphabetically


####################

if analysis_choices[0] in analyses or analysis_choices[1] in analyses:
	coord_path_list = glob.glob(os.path.join(masks_path, "*.txt"))
	coord_list = {}
	for coord_file in coord_path_list:
		splits = coord_file.split("/")
		if " " in splits[-1]:
			sys.exit("Please make sure that no text files with coordinates have spaces in their filename.")
		coord_list[splits[-1]] = coord_file  # resulting dict format: {'region.txt': 'path/to/filelocation/region.txt'}
		
	files_and_coordinates = {}
	for item in coord_list:
		coordinate_values = open(coord_list[item], 'r')
		coordinate_values = coordinate_values.readline()
		if "," in coordinate_values:
			if not " " in coordinate_values:  # values are 'a,b,c'
				coordinate_values = coordinate_values.replace(",", ", ")
		else:  # values are 'a b c'
			coordinate_values = coordinate_values.replace(" ", ", ")
		if not "(" in coordinate_values:  # values are a,b,c and not (a,b,c)
			coordinate_values = "(" + coordinate_values + ")"
		files_and_coordinates[item] = coordinate_values  # resulting dict format: {'region.txt': '(x_coord, y_coord, z_coord)'}
		
		
if analysis_choices[2] in analyses or analysis_choices[3] in analyses:
	masks_path_list = glob.glob(os.path.join(masks_path, "*+tlrc.HEAD"))
	mask_list = {}
	for mask_file in masks_path_list:
		splits = mask_file.split("/")
		if " " in splits[-1]:
			sys.exit("Please make sure that no AFNI mask files have spaces in their filename.")
		mask_list[splits[-1]] = mask_file  # resulting dict format: {'region.HEAD': 'path/to/filelocation/region.HEAD'}

	check_files = []
	for item in mask_list:
		check_files.append(item[:-5])


####################
#Check ROI files
####################

root = Tk()  # create TKinter window
root.title("ROI file check")
root.geometry('+1070+500')  # sets the location of the window - format (+horiz+vert)
root.wm_attributes("-topmost", 1)  # makes sure that the window appears on top of all other windows
if analysis_choices[0] in analyses or analysis_choices[1] in analyses:
	label = Label(root, text="The following are the files which will be used for spherical ROIs:").grid(columnspan=3)
	label1 = Label(root,text="").grid(columnspan=3)
	for file in files_and_coordinates:
		label2 = Label(root, text=file, font='helvetica 14 bold').grid(column=1)
		label3 = Label(root, text=files_and_coordinates[file], font='helvetica 14 bold').grid(column=1)
	label4 = Label(root,text="").grid(columnspan=3)
if analysis_choices[2] in analyses or analysis_choices[3] in analyses:	
	label5 = Label(root, text="The following are the files which will be used for pre-determined ROIs:").grid(columnspan=3)
	label6 = Label(root,text="").grid(columnspan=3)
	for file in check_files:
		label7 = Label(root, text=file, font='helvetica 14 bold').grid(column=1)
	label8 = Label(root,text="").grid(columnspan=3)
label9 = Label(root,text="If these are correct, click 'Continue.' If not, click 'Quit' and change the files found in:").grid(columnspan=3)
label11 = Label(root,text=masks_path).grid(columnspan=3)
button = Button(root, text='Continue', width=25, command=root.destroy).grid(columnspan=3)  # button closes window when pressed
button1 = Button(root, text='Quit',width=23, command=sys.exit).grid(columnspan=3) # button ends script when pressed

root.update_idletasks()
windowheight = root.winfo_height()
windowwidth = root.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
root.geometry("+%s+%s" % (positionRight, positionDown))

root.mainloop()


####################
#Get names of all possible GLM folders
####################

possible_GLM_folders = []

GLM_GAM_folders = []
GLM_TENT_folders = []

for folder in subject_folders1:
	subj_number = folder[5:]

	results_folders = os.listdir(os.path.join(subject_results, folder))
	results_folders = [x for x in results_folders if (".DS_Store" not in x)]
	results_folder = os.path.join(subject_results, folder, results_folders[0]) #results folder inside subject folder
	GLM_folders = glob.glob(os.path.join(results_folder, "*"))
	GLM_folders1 = []
	for folder in GLM_folders:
		splits = folder.split("/")
		GLM_folders1.append(splits[-1])
	if analysis_choices[0] in analyses or analysis_choices[2] in analyses:
		for potential_folder in GLM_folders1:
 			check = glob.glob(os.path.join(results_folder, potential_folder, "stats*"))  # for GAM GLMs
 			check1 = glob.glob(os.path.join(results_folder, potential_folder, "iresp*"))  # for TENT GLMs
			if check and not check1:  # if the folder has a stats file, but no iresp files
				if not potential_folder in GLM_GAM_folders:
					GLM_GAM_folders.append(potential_folder)		
	if analysis_choices[1] in analyses or analysis_choices[3] in analyses:
		for potential_folder in GLM_folders1:
 			check = glob.glob(os.path.join(results_folder, potential_folder, "iresp*"))  # for TENT GLMs
			if check:  # if the folder has any iresp files
				if not potential_folder in GLM_TENT_folders:
					GLM_TENT_folders.append(potential_folder)
			

GLM_GAM_folders = sorted(GLM_GAM_folders)
GLM_TENT_folders = sorted(GLM_TENT_folders)	

buttons_list_GAM = GLM_GAM_folders
buttons_list_TENT = GLM_TENT_folders

buttons_GAM = {}
buttons_TENT = {}
for item in buttons_list_GAM:
	buttons_GAM[item] = 0
for item in buttons_list_TENT:
	buttons_TENT[item] = 0
buttons_outcome_GAM = {}
buttons_outcome_TENT = {}

root = Tk()  # create TKinter window
root.title("GLM Selection")
root.geometry('+1070+500')  # sets the location of the window - format (+horiz+vert)
root.wm_attributes("-topmost", 1)  # makes sure that the window appears on top of all other windows


def end():
	if analysis_choices[0] in analyses or analysis_choices[2] in analyses:
		for item in buttons_GAM:
				buttons_outcome_GAM[item] = buttons_GAM[item].get()
	if analysis_choices[1] in analyses or analysis_choices[3] in analyses:
		for item in buttons_TENT:
				buttons_outcome_TENT[item] = buttons_TENT[item].get()
	root.destroy()

def selectall():
	if analysis_choices[0] in analyses or analysis_choices[2] in analyses:
		for item in buttons_GAM:
			buttons_GAM[item].set(1)
	if analysis_choices[1] in analyses or analysis_choices[3] in analyses:
		for item in buttons_TENT:
			buttons_TENT[item].set(1)

def selectall_GAM():
	for item in buttons_GAM:
		buttons_GAM[item].set(1)

def selectall_TENT():
	for item in buttons_TENT:
		buttons_TENT[item].set(1)

def unselectall():
	if analysis_choices[0] in analyses or analysis_choices[2] in analyses:
		for item in buttons_GAM:
			buttons_GAM[item].set(0)
	if analysis_choices[1] in analyses or analysis_choices[3] in analyses:
		for item in buttons_TENT:
			buttons_TENT[item].set(0)


if (analysis_choices[0] in analyses or analysis_choices[2] in analyses) and (analysis_choices[1] in analyses or analysis_choices[3] in analyses):
	label = Label(root, text="Please select the GLMs to use").grid(row=1, columnspan=2, padx=20, pady=5)
	button1 = Button(root, text="Select All", command = selectall).grid(row=2, columnspan=2)
	button2 = Button(root, text="Unselect All", command = unselectall).grid(row=3, columnspan=2)
	button3 = Button(root, text="Select All GAM", command = selectall_GAM).grid(row=4, column=0, padx=20)
	button4 = Button(root, text="Select All TENT", command = selectall_TENT).grid(row=4, column=1, padx=20)
	start_row = 5
else:
	label = Label(root, text="Please select the GLMs to use").grid(row=1, padx=20, pady=5)
	button1 = Button(root, text="Select All", command = selectall).grid(row=2)
	button2 = Button(root, text="Unselect All", command = unselectall).grid(row=3)
	start_row = 4

row = start_row
tent_row = start_row
if analysis_choices[0] in analyses or analysis_choices[2] in analyses:
	if analysis_choices[1] in analyses or analysis_choices[3] in analyses:
		columnspan = 2
		for button in buttons_list_GAM:
			buttons_GAM[button] = IntVar()
			user_button = Checkbutton(root, text=button, variable=buttons_GAM[button], padx=20)
			user_button.grid(row=row, column=0, sticky="w")
			row += 1
		for button in buttons_list_TENT:
			buttons_TENT[button] = IntVar()
			user_button = Checkbutton(root, text=button, variable=buttons_TENT[button], padx=20)
			user_button.grid(row=tent_row, column=1, sticky="w")
			tent_row += 1
	else: # if only GAM
		columnspan = 1
		for button in buttons_list_GAM:
			buttons_GAM[button] = IntVar()
			user_button = Checkbutton(root, text=button, variable=buttons_GAM[button], padx=20)
			user_button.grid(row=row, column=0, sticky="w")
			row += 1
else: # if only TENT
	columnspan = 1
	for button in buttons_list_TENT:
		buttons_TENT[button] = IntVar()
		user_button = Checkbutton(root, text=button, variable=buttons_TENT[button], padx=20)
		user_button.grid(row=max(row,tent_row), column=0, sticky="w")
		row += 1
	

endbutton = Button(root, text="Submit", command=end).grid(row=row, column=0, columnspan=columnspan)
quitbutton = Button(root, text="Cancel", command=sys.exit).grid(row=row + 1, column=0, columnspan=columnspan, pady=5)

root.update_idletasks()
windowheight = root.winfo_height()
windowwidth = root.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
root.geometry("+%s+%s" % (positionRight, positionDown))

root.mainloop()



use_GAM = []
for item in buttons_outcome_GAM:
	if buttons_outcome_GAM[item] == 1:
		use_GAM.append(item)
use_GAM = sorted(use_GAM)

	
		
use_TENT = []
for item in buttons_outcome_TENT:
	if buttons_outcome_TENT[item] == 1:
		use_TENT.append(item)
use_TENT = sorted(use_TENT)

use_GLM_folders = use_GAM + use_TENT



possible_GAM_conditions_list = {}
possible_TENT_conditions_list = {}
	
for GLM_folder in use_GAM:
	possible_conditions = []
	for folder in subject_folders1:  # find a subject who has this GLM, to extract info about it
		subj_number = folder[5:]
		results_folders = os.listdir(os.path.join(subject_results, folder))
		results_folders = [x for x in results_folders if (".DS_Store" not in x)]
		results_folder = os.path.join(subject_results, folder, results_folders[0])
		if os.path.exists(os.path.join(results_folder, GLM_folder)):
			GLM_folder_path = os.path.join(results_folder, GLM_folder)
			break
	GLM_conditions = []		
	stats_files = glob.glob(os.path.join(GLM_folder_path, "stats*.HEAD"))
	stat_splits = stats_files[0].split("/")
	stats_file = stat_splits[-1]
	stats_path = os.path.join(GLM_folder_path, stats_file)
	proc = subprocess.Popen("3dinfo -label %s" % (stats_path), shell=True, stdout=subprocess.PIPE)
	label_names = proc.stdout.read()
	name_list = label_names.split("|")
	stat_condition_list = [fn for fn in name_list if "#0_Coef" in fn]
	for condition in stat_condition_list:
		possible_conditions.append(condition[:-7])
	possible_GAM_conditions_list[GLM_folder] = possible_conditions

for GLM_folder in use_TENT:
	possible_conditions = []
	for folder in subject_folders1:  # find a subject who has this GLM, to extract info about it
		subj_number = folder[5:]
		results_folders = os.listdir(os.path.join(subject_results, folder))
		results_folders = [x for x in results_folders if (".DS_Store" not in x)]
		results_folder = os.path.join(subject_results, folder, results_folders[0])
		if os.path.exists(os.path.join(results_folder, GLM_folder)):
			GLM_folder_path = os.path.join(results_folder, GLM_folder)
			break
	GLM_conditions = []		
	iresp_files = glob.glob(os.path.join(GLM_folder_path, "iresp*.HEAD"))
	iresp_files1 = []
	for iresp_file in iresp_files:
		splits = iresp_file.split("/")
		iresp_files1.append(splits[-1])
	for iresp_file in iresp_files1:	
		iresp = iresp_file[:-10]  # remove the '+tlrc.HEAD' from iresp file
		iresp_split = iresp[6:].split(".")  # remove "iresp" from filename, split at '.' (lose participant number)
		condition = iresp_split[0]  # keeps only the user-specified condition name
		possible_conditions.append(condition)
	possible_TENT_conditions_list[GLM_folder] = possible_conditions




def long_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0])-i+1):
                if j > len(substr) and is_substr(data[0][i:i+j], data) and len(data[0][i:i+j]) > 2:
                    substr = data[0][i:i+j]
    return substr

def is_substr(find, data):
    if len(data) < 1 and len(find) < 1:
        return False
    for i in range(len(data)):
        if find not in data[i]:
            return False
    return True

for item in possible_GAM_conditions_list:
	for i in range(0,5):
		long_substring = long_substr(possible_GAM_conditions_list[item])
		possible_GAM_conditions_list[item] = [x.replace(long_substring, '') for x in possible_GAM_conditions_list[item]]
		possible_GAM_conditions_list[item] = sorted(possible_GAM_conditions_list[item])

for item in possible_TENT_conditions_list:
	for i in range(0,5):
		long_substring = long_substr(possible_TENT_conditions_list[item])
		possible_TENT_conditions_list[item] = [x.replace(long_substring, '') for x in possible_TENT_conditions_list[item]]
		possible_TENT_conditions_list[item] = sorted(possible_TENT_conditions_list[item])


root = Tk()

buttons_GAM = {}
buttons_TENT = {}	

for GLM in possible_GAM_conditions_list:
	new_GLM_dict = {}
	for response in possible_GAM_conditions_list[GLM]:
		new_GLM_dict[response] = IntVar()
	buttons_GAM[GLM] = new_GLM_dict

for GLM in possible_TENT_conditions_list:
	new_GLM_dict = {}
	for response in possible_TENT_conditions_list[GLM]:
		new_GLM_dict[response] = IntVar()
	buttons_TENT[GLM] = new_GLM_dict


shortened_GAM_responses = []
for GLM in buttons_GAM:
	for response in buttons_GAM[GLM]:
		if response not in shortened_GAM_responses:
			shortened_GAM_responses.append(response)
shortened_GAM_responses = sorted(shortened_GAM_responses)
	
shortened_TENT_responses = []
for GLM in buttons_TENT:
	for response in buttons_TENT[GLM]:
		if response not in shortened_TENT_responses:
			shortened_TENT_responses.append(response)
shortened_TENT_responses = sorted(shortened_TENT_responses)	
	

buttons_GAM_outcome = {}
buttons_TENT_outcome = {}

root.title("Condition Selection")
root.geometry('+1070+500')  # sets the location of the window - format (+horiz+vert)
root.wm_attributes("-topmost", 1)  # makes sure that the window appears on top of all other windows


def end():
	for item in buttons_GAM:
		outcomes = {}
		for response in buttons_GAM[item]:
			outcomes[response] = buttons_GAM[item][response].get()
		buttons_GAM_outcome[item] = outcomes
	for item in buttons_TENT:
		outcomes = {}
		for response in buttons_TENT[item]:
			outcomes[response] = buttons_TENT[item][response].get()
		buttons_TENT_outcome[item] = outcomes
	root.destroy()

def selectall():
	for item in buttons_GAM:
		for response in buttons_GAM[item]:
			buttons_GAM[item][response].set(1)
	for item in buttons_TENT:
		for response in buttons_TENT[item]:
			buttons_TENT[item][response].set(1)

def unselectall():
	for item in buttons_GAM:
		for response in buttons_GAM[item]:
			buttons_GAM[item][response].set(0)
	for item in buttons_TENT:
		for response in buttons_TENT[item]:
			buttons_TENT[item][response].set(0)

def GAM_button(key):
	for item in buttons_GAM:
		if item == key:
			all_checked = []
			for response in buttons_GAM[item]:
				if buttons_GAM[item][response].get() == 0:
					buttons_GAM[item][response].set(1)
				else:
					all_checked.append("checked")
			if len(all_checked) == len(buttons_GAM[item]):
				for response in buttons_GAM[item]:
					buttons_GAM[item][response].set(0)
				
def GAM_short_button(key):
	quick_list = [x for x in shortened_GAM_responses if x != key]
	for item in buttons_GAM:
		for response in buttons_GAM[item]:
			if key in response:
				unique = True
				for other_option in quick_list:
					if (other_option not in response) or (other_option in key):
						continue
					else:
						unique = False
				if unique:
					buttons_GAM[item][response].set(1)


def TENT_button(key):
	for item in buttons_TENT:
		if item == key:
			for response in buttons_TENT[item]:
				buttons_TENT[item][response].set(1)

def TENT_short_button(key):
	quick_list = [x for x in shortened_TENT_responses if x != key]
	for item in buttons_TENT:
		for response in buttons_TENT[item]:
			if key in response:
				unique = True
				for other_option in quick_list:
					if (other_option not in response) or (other_option in key):
						continue
					else:
						unique = False
				if unique:
					buttons_TENT[item][response].set(1)
				

TENT_condition_column = 0
columnspan = 1
if analysis_choices[0] in analyses or analysis_choices[2] in analyses:
	if analysis_choices[1] in analyses or analysis_choices[3] in analyses:
		columnspan = 2
		TENT_condition_column = 1



GAMrow_shorts = 5
GAMrow_condition_start = 6 + len(shortened_GAM_responses)
TENTrow_shorts = 5
TENTrow_condition_start = 6	+ len(shortened_TENT_responses)
GAMrow_condition_start = max(GAMrow_condition_start, TENTrow_condition_start)
TENTrow_condition_start = max(GAMrow_condition_start, TENTrow_condition_start)
GAMrow = GAMrow_condition_start
TENTrow = TENTrow_condition_start

GAMcount = 0
GAMcolumn = 0
for key in use_GAM:
	if GAMrow > 30:
		GAMrow = GAMrow_condition_start
		GAMcolumn = 1
	if GAMrow > 30 and GAMcolumn == 1:
		GAMrow = GAMrow_condition_start
		GAMcolumn = 2
	if GAMrow > 30 and GAMcolumn == 2:
		GAMrow = GAMrow_condition_start
		GAMcolumn = 3
	for item in buttons_GAM:
		if item == key:
			button = Button(root, text=key,command=lambda GAMcount=GAMcount: GAM_button(use_GAM[GAMcount])).grid(row=GAMrow,column=GAMcolumn)
			GAMrow += 1
			for response in buttons_GAM[item]:
				user_button = Checkbutton(root, text=response, variable = buttons_GAM[item][response]).grid(row=GAMrow, column=GAMcolumn)
				GAMrow += 1
	GAMcount += 1


GAMcount_short = 0
for key in shortened_GAM_responses:
	button = Button(root, text=key, command=lambda GAMcount_short=GAMcount_short: GAM_short_button(shortened_GAM_responses[GAMcount_short])).grid(row=GAMrow_shorts,column=0, columnspan = max(1,GAMcolumn+1))
	GAMrow_shorts += 1
	GAMcount_short += 1

label_int = Label(root, text="").grid(row=(GAMrow_condition_start -1), column= 0) 

	
TENTcount = 0
TENT_condition_column_original = TENT_condition_column
if GAMcolumn > 0:
	TENT_condition_column_original = GAMcolumn + 1
TENTcolumn = TENT_condition_column_original
for key in use_TENT:
	if TENTrow > 30 and TENTcolumn == TENT_condition_column_original:
		TENTrow = TENTrow_condition_start
		TENTcolumn = TENT_condition_column_original + 1
	if TENTrow > 30 and TENTcolumn == (TENT_condition_column_original + 1):
		TENTrow = TENTrow_condition_start
		TENTcolumn = TENT_condition_column_original + 2
	if TENTrow > 30 and TENTcolumn == (TENT_condition_column_original + 2):
		TENTrow = TENTrow_condition_start
		TENTcolumn = TENT_condition_column_original + 3
	for item in buttons_TENT:
		if item == key:
			button = Button(root, text=key,command=lambda TENTcount=TENTcount: TENT_button(use_TENT[TENTcount])).grid(row=TENTrow,column=TENTcolumn)
			TENTrow += 1
			for response in buttons_TENT[item]:
				user_button = Checkbutton(root, text=response, variable = buttons_TENT[item][response]).grid(row=TENTrow, column=TENTcolumn)
				TENTrow += 1
	TENTcount += 1


TENTcount_short = 0
for key in shortened_TENT_responses:
	button = Button(root, text=key, command=lambda TENTcount_short=TENTcount_short: TENT_short_button(shortened_TENT_responses[TENTcount_short])).grid(row=TENTrow_shorts,column=TENT_condition_column_original, columnspan = max(1,TENTcolumn-GAMcolumn))
	TENTrow_shorts += 1
	TENTcount_short += 1

label_int = Label(root, text="").grid(row=(TENTrow_condition_start -1), column= 0) 


header = Label(root, text="Please select the conditions to use. Clicking a GLM's name will select all of its conditions.\nIf all conditions in a GLM are selected, clicking the GLM's name will unselect all associated conditions.").grid(row=1, columnspan=(GAMcolumn+TENTcolumn+1))
button1 = Button(root, text="Select All", command = selectall).grid(row=3, columnspan=(GAMcolumn+TENTcolumn+1))
button2 = Button(root, text="Unselect All", command = unselectall).grid(row=4, columnspan=(GAMcolumn+TENTcolumn+1))
endbutton = Button(root, text="Begin ROI extraction", command=end).grid(row=40, column=0, columnspan=(GAMcolumn+TENTcolumn+1))
quitbutton = Button(root, text="Cancel", command=sys.exit).grid(row=41, column=0, columnspan=(GAMcolumn+TENTcolumn+1))

root.update_idletasks()
windowheight = root.winfo_height()
windowwidth = root.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
root.geometry("+%s+%s" % (positionRight, positionDown))

root.mainloop()



final_GAM_list = {}
for item in buttons_GAM_outcome:
	checked_options = []
	for response in buttons_GAM_outcome[item]:
		if buttons_GAM_outcome[item][response] == 1:
			checked_options.append(response)
	final_GAM_list[item] = checked_options

final_TENT_list = {}
for item in buttons_TENT_outcome:
	checked_options = []
	for response in buttons_TENT_outcome[item]:
		if buttons_TENT_outcome[item][response] == 1:
			checked_options.append(response)
	final_TENT_list[item] = checked_options


starttime = datetime.now()
print_starttime = starttime.strftime("%m-%d-%Y, %I:%M:%S %p")
print("Begin script execution: " + str(print_starttime))

########################################################################
# CALCULATE
########################################################################
for method in analyses:

	all_GLM_condition_pairs = {}

	if "sphere" in method:
		method_ROI = "spherical"
		ROI_list = coord_list

	if "mask" in method:
		method_ROI = "predefined_mask"
		ROI_list = mask_list

	if "magnitude" in method:
		method_type = "magnitudes"
		final_list = final_GAM_list
		shortened_responses = shortened_GAM_responses
		file_type = "stats"

	if "timecourse" in method:
		method_type = "timecourses"
		final_list = final_TENT_list
		shortened_responses = shortened_TENT_responses
		file_type = "iresp"


	print("\n\n#########################")
	print("Processing %s ROI(s) - %s" % (method_ROI, method_type))
	print("#########################")


	###iterate through each subject
	for folder in subject_folders1:
		subj_number = folder[5:]

		time1 = datetime.now()
		time_duration(starttime, time1)
		print("***" + subj_number + "..." + duration_string + " elapsed")

		results_folders = os.listdir(os.path.join(subject_results, folder))
		results_folders = [x for x in results_folders if (".DS_Store" not in x)]
		results_folder = os.path.join(subject_results, folder, results_folders[0]) #results folder inside subject folder
			
			
		###iterate through each GLM	
		for GLM_folder in final_list:
			print(GLM_folder + "....")
			GLM_folder_path = os.path.join(results_folder, GLM_folder)
			if not os.path.exists(GLM_folder_path):
				break
			average_folder = os.path.join(GLM_folder_path, "%s_ROI_averages_%s" % (method_ROI, method_type))
			if not os.path.exists(average_folder):
				os.makedirs(average_folder)



			GLM_conditions = []		
		
			# import spherical ROI coordinate text files
			if method_ROI == "spherical":				
				for spherical_ROI_coord in coord_list:
					# If the coordinates have not been provided in the format required by AFNI, fix the text file
					coord_file = open(coord_list[spherical_ROI_coord], 'r')
					file_data = coord_file.readline()
					coord_file.close()
					if "," in file_data:
						if not " " in file_data:  # values are 'a,b,c'
							file_data = file_data.replace(",", " ")
						else:  # values are 'a, b, c'
							file_data = file_data.replace(", ", " ")
						new_coord_file = open(coord_list[spherical_ROI_coord], 'w')
						new_coord_file.writelines(file_data)
						new_coord_file.close()

					spherical_coord_path = os.path.join(GLM_folder_path, spherical_ROI_coord)
					temp_spherical_coord_path = os.path.join(GLM_folder_path, "temp_" + spherical_ROI_coord)
					if os.path.exists(spherical_coord_path):
						subprocess.call("rm %s" % (spherical_coord_path), shell=True)
					subprocess.call("cp %s %s" % (coord_list[spherical_ROI_coord], GLM_folder_path), shell=True)
					subprocess.call("mv %s %s" % (spherical_coord_path, temp_spherical_coord_path), shell=True)

			#import predefined ROI mask AFNI files
			elif method_ROI == "predefined_mask":
				temp_mask_paths = os.path.join(GLM_folder_path, "temp_*")
				subprocess.call("rm %s" % temp_mask_paths, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)  # if there are any lingering masks from previous analyses, delete them
				for Predef_ROI_mask in mask_list:
					mask_path = os.path.join(GLM_folder_path, Predef_ROI_mask)
					temp_head_mask_path = os.path.join(GLM_folder_path, "temp_" + Predef_ROI_mask)
					brik_mask_path = os.path.join(GLM_folder_path, Predef_ROI_mask[:-5] + ".BRIK.gz")
					temp_brik_mask_path = os.path.join(GLM_folder_path, "temp_" + Predef_ROI_mask[:-5] + ".BRIK.gz")

					subprocess.call("cp %s* %s" % (mask_list[Predef_ROI_mask][:-5], GLM_folder_path), shell=True)
					subprocess.call("mv %s %s" % (mask_path, temp_head_mask_path), shell=True)
					subprocess.call("mv %s %s" % (brik_mask_path, temp_brik_mask_path), shell=True)
			



			analysis_files = glob.glob(os.path.join(GLM_folder_path, "%s*.HEAD" % file_type))

			if method_type == "magnitudes":
				proc = subprocess.Popen("3dinfo -label %s" % (analysis_files[0]), shell=True, stdout=subprocess.PIPE)
				label_names = proc.stdout.read()
				name_list = label_names.split("|")
				condition_list = [fn for fn in name_list if "#0_Coef" in fn]
				iterate = condition_list
			elif method_type == "timecourses":
				iterate = analysis_files


			# this section prevents repeated filenames from being included wrong (i.e. you want 'hit', but that is contained in 'hit-cr_GLT')
			use_list = []
			for option in iterate:  # for each condition in the stats file (magnitude), or each iresp file in this folder (timecourse)
				for condition in final_list[GLM_folder]:  # for each condition selected in the pop-up window
					if condition in option:
						unique = True
						quick_list = [x for x in shortened_responses if x != condition]  
						for other_option in quick_list:  # for each shortened_response option that isn't this one
							if (other_option not in option) or (other_option in condition):
								continue
							else:
								unique = False
						if unique:
							use_list.append(option)


			##########
			# Make sure the geometry of the file matches the coordinate system provided
			##########
			def check_geometry(input_file):
				input_filepath = os.path.join(GLM_folder_path, input_file)
				check = subprocess.Popen("3dinfo -orient %s" % (input_filepath), shell=True, stdout=subprocess.PIPE)
				orient_check = check.stdout.read()
				if not coord_system in orient_check:

					master = Tk()
					master.title("Coordinate System Mismatch")
					master.geometry('+1070+500')
					master.wm_attributes("-topmost", 1)

					Label(master, text='Error for file:\n%s\n\n'
									'The coordinate system you provided (%s) does not match your file (%s).\n'
									'This could result in the wrong ROI being used.\n\n'
									'Do you wish to continue anyway?' % ((input_filepath),
																			coord_system,
																			orient_check[:3])).grid(row=1, padx=20)
					Label(master, text='').grid(row=2)

					Button(master, text='Continue', command=master.destroy).grid(row=3, sticky=S,
																			pady=4)
					Button(master, text='Exit', command=sys.exit).grid(row=4, sticky=S,
																		pady=4)

					master.update_idletasks()
					windowheight = master.winfo_height()
					windowwidth = master.winfo_width()
					positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
					positionDown = screeny + int(screenheight / 2 - windowheight / 2)
					master.geometry("+%s+%s" % (positionRight, positionDown))

					mainloop()


			if method_type == "timecourses":
				iresp_files = []
				for iresp_file in use_list:
					splits = iresp_file.split("/")
					iresp_files.append(splits[-1])
					if method_ROI == "spherical":
						check_geometry(splits[-1])
				use_list = iresp_files
			elif method_type == "magnitudes":
				splits = analysis_files[0].split("/")
				stats_file = splits[-1]
				if method_ROI == "spherical":
					check_geometry(stats_file)


			###iterate through each condition/event type for this GLM		
			for condition in use_list:
				if method_type == "magnitudes":
					condition_name = condition[:-7]
					use_file = stats_file[:-5]
				elif method_type == "timecourses":
					condition = condition[:-5]   # remove the .HEAD from iresp file
					split = condition[6:].split(".")  # remove "iresp" from filename, split at "."
					condition_name = split[0]  # keeps only the user-specified condition name
					use_file = condition
				if method_ROI == "spherical":
					for spherical_ROI_coord in coord_list:
						spherical_ROI_name = spherical_ROI_coord[:-4] # remove ".txt" at the end of the file name
						print(spherical_ROI_name)

						# create spherical ROIs
						# print("cd %s && 3dUndump -prefix temp_%s_mask_%s -master %s -srad %s -xyz temp_%s" % (GLM_folder_path, spherical_ROI_name, condition_name, use_file, sphere_radius, spherical_ROI_coord))
						subprocess.call("cd %s && 3dUndump -prefix temp_%s_mask_%s -master %s -srad %s -xyz temp_%s" % (GLM_folder_path, spherical_ROI_name, condition_name, use_file, sphere_radius, spherical_ROI_coord), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
						# average across voxels within spherical ROIs
						if method_type == "magnitudes":
							# print("cd %s && 3dmaskave -mask temp_%s_mask_%s+tlrc '%s[%s]' > %s.ave.%s.%s.txt" % (GLM_folder_path, spherical_ROI_name, condition_name, use_file, condition, spherical_ROI_name, subj_number, condition_name))
							subprocess.call("cd %s && 3dmaskave -mask temp_%s_mask_%s+tlrc '%s[%s]' > %s.ave.%s.%s.txt" % (GLM_folder_path, spherical_ROI_name, condition_name, use_file, condition, spherical_ROI_name, subj_number, condition_name), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
						elif method_type == "timecourses":
							# print("cd %s && 3dmaskave -mask temp_%s_mask_%s+tlrc %s > %s.ave.%s.txt" % (GLM_folder_path, spherical_ROI_name, condition_name, use_file, spherical_ROI_name, condition_name))
							subprocess.call("cd %s && 3dmaskave -mask temp_%s_mask_%s+tlrc %s > %s.ave.%s.%s.txt" % (GLM_folder_path, spherical_ROI_name, condition_name, use_file, spherical_ROI_name, subj_number, condition_name), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
				elif method_ROI == "predefined_mask":
					for Predef_ROI_mask in mask_list:
						Predef_ROI_name = Predef_ROI_mask[:-5] # remove ".HEAD" at the end of the file name
						print(Predef_ROI_name[:-5])
						
						# average across voxels within predefined ROI
						if method_type == "magnitudes":
							# print("cd %s && 3dmaskave -mask temp_%s '%s[%s]' > %s.ave.%s.%s.txt" % (GLM_folder_path, Predef_ROI_name, stats_file[:-5], condition, Predef_ROI_name, subj_number, condition_name))
							subprocess.call("cd %s && 3dmaskave -mask temp_%s '%s[%s]' > %s.ave.%s.%s.txt" % (GLM_folder_path, Predef_ROI_name, stats_file[:-5], condition, Predef_ROI_name, subj_number, condition_name), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
						elif method_type == "timecourses":
							# print("cd %s && 3dmaskave -mask temp_%s %s > %s.ave.%s.txt" % (GLM_folder_path, Predef_ROI_name, use_file, Predef_ROI_name, condition_name))
							subprocess.call("cd %s && 3dmaskave -mask temp_%s %s > %s.ave.%s.%s.txt" % (GLM_folder_path, Predef_ROI_name, use_file, Predef_ROI_name, subj_number, condition_name), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
				# relocate output ROI averages
				average_file = os.path.join(GLM_folder_path, "*ave*txt")
				subprocess.call("mv %s %s" % (average_file, average_folder), shell=True)

				GLM_conditions.append(condition_name)

			# delete temp masks and temp coordinate files
			temp_files = os.path.join(GLM_folder_path, "temp_*")
			subprocess.call("rm %s" % temp_files, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

				

			all_GLM_condition_pairs[GLM_folder] = sorted(GLM_conditions)
			
	output_averages_folder = os.path.join(subject_results, "Average_%s_ROI_%s" % (method_ROI, method_type))
	if not os.path.exists(output_averages_folder):
		os.makedirs(output_averages_folder)

	avg_count = 0
	master_list = {}
	for folder in all_GLM_condition_pairs:
		for condition in all_GLM_condition_pairs[folder]:
			print("\n" + folder + " : " + condition)
			for ROI in ROI_list:
				if method_ROI == "spherical":
					ROI_name = ROI[:-4]
				elif method_ROI == "predefined_mask":
					ROI_name = ROI[:-10]
				ROI_conditions = glob.glob(os.path.join(subject_results, "*", "*", folder, "%s_ROI_averages_%s" % (method_ROI, method_type), "%s*%s.txt" % (ROI_name, condition)))

				ROI_conditions = sorted(ROI_conditions)

				count = 0

				for subject in ROI_conditions:
					subject_number = subject.split(os.path.join(subject_results, "subj."))
					subject_number = subject_number[1].split("/")
					subject_number = subject_number[0]

					count = count + 1

					with open(subject, 'r') as in_file:
						lines1=[]
						for line in in_file:
							newlines = line.split(" ")
							lines1.append(newlines[0])
						if method_type == "magnitudes":
							act_data = float(lines1[0])
						elif method_type == "timecourses":
							act_data = []
							for item in lines1:
								act_data.append(float(item))
						key_name = ROI_name + "_" + condition
						if key_name in master_list:
							if method_type == "magnitudes":
								master_list[key_name] = master_list[key_name] + act_data
							elif method_type == "timecourses":
								master_list[key_name] = map(add, master_list[key_name], act_data)
							master_list[key_name + "_count"] = master_list[key_name + "_count"] + 1
							master_list[key_name + "_sem"].append(act_data)
						else:
							master_list[key_name] = act_data
							master_list[key_name + "_count"] = 1
							master_list[key_name + "_sem"] = [act_data]
				avg_count = avg_count + 1

	if method_type == "timecourses":
		timepoint_number = None
		for item in master_list:
			if "count" not in item and "sem" not in item:
				timepoint_number = len(master_list[item])
				break


	master_file_path = os.path.join(output_averages_folder, "master_%s_ROI_%s_file.csv" % (method_ROI, method_type))
	if os.path.exists(master_file_path):
		existing_outputs = glob.glob(os.path.join(output_averages_folder, "master_%s_ROI_%s_file*" % (method_ROI, method_type)))
		master_file_path = os.path.join(output_averages_folder, "master_%s_ROI_%s_file_%s.csv" % (method_ROI, method_type, len(existing_outputs)))

	if method_type == "timecourses":
		for item in master_list:
			if "count" not in item and "sem" not in item:
				master_list[item][:] = [x / master_list[item + "_count"] for x in master_list[item]]

		for item in master_list:
			sem_calc = []
			if "sem" in item:
				for j in range(0, timepoint_number):
					sem_list = []
					for participant in master_list[item]:
						sem_list.append(participant[j])
					sem = stats.sem(sem_list, ddof=1, axis=None)
					sem_calc.append(sem)
				master_list[item] = sem_calc
				
		final_list = {}	



	for item in master_list:
		if "count" not in item and "sem" not in item:
			if method_type == "magnitudes":
				master_list[item] = master_list[item] / master_list[item + "_count"]
				master_list[item  + "_sem"] = stats.sem(master_list[item + "_sem"], axis=None, ddof=1)
			elif method_type == "timecourses":
				final_list[item] = [item, master_list[item + "_count"]]
				for k in range(0, timepoint_number):
					final_list[item].append(master_list[item][k])
					final_list[item].append(master_list[item + "_sem"][k])

	ordered_list = []
	for item in master_list:
		if "count" not in item and "sem" not in item:
			ordered_list.append(item)
	ordered_list = sorted(ordered_list)

	if method_type == "magnitudes":
		headers = ["activation", "subj_count", "average", "sem"]
	elif method_type == "timecourses":
		headers = ['timepoint']
		for item in ordered_list:
				if "count" not in item and "sem" not in item:
					headers.append(item + "_subj_count")
					headers.append(item + "_average")
					headers.append(item + "_sem")
			
	with open(master_file_path, 'w') as master_file:
		writer = csv.writer(master_file)
		writer.writerow(headers)




	if method_type == "timecourses":
		intermediate_list = {}
		for i in range(0, timepoint_number):
			for item in ordered_list:
					intermediate_list[item + "_subj_count_" + str(i+1)] = master_list[item + "_count"]
					intermediate_list[item + "_average_" + str(i+1)] = master_list[item][i]
					intermediate_list[item + "_sem_" + str(i+1)] = master_list[item + "_sem"][i]

		master_list = intermediate_list

	
	if method_type == "magnitudes":
		for item in ordered_list:
				with open(master_file_path, 'a') as master_file:
					writer = csv.writer(master_file)
					writer.writerow([item, master_list[item + "_count"], master_list[item], master_list[item + "_sem"]])
	elif method_type == "timecourses":
		for i in range(1, timepoint_number + 1):
			with open(master_file_path, 'a') as master_file:
				writer = csv.writer(master_file)
				write_list = [str(i)]
				for item in ordered_list:
					write_list.append(master_list[item+ "_subj_count_" + str(i)])
					write_list.append(master_list[item+ "_average_" + str(i)])
					write_list.append(master_list[item+ "_sem_" + str(i)])
				writer.writerow(write_list)




	print("\n" + str(avg_count) + " averages calculated")

	# Delete remaining intermediate files
	avg_folder_files = os.listdir(output_averages_folder)
	for avg_file in avg_folder_files:
		if not avg_file.startswith("master_"):
			rm_file = os.path.join(subject_results, ("Average_" + method_ROI + "_ROI_" + method_type), avg_file)
			subprocess.call("rm %s" % (rm_file), shell=True)
	rm_folder = os.path.join(subject_results, "*", "*", "*", "*_ROI_averages_*")
	subprocess.call("rm -R %s" % (rm_folder), shell=True)

endtime = datetime.now()
print_endtime = endtime.strftime("%m-%d-%Y, %I:%M:%S %p")
print("End script execution: " + str(print_endtime))

time_duration(starttime, endtime)
print("Total script duration: " + duration_string)