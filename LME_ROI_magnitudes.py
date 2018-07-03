import os
import subprocess
import csv
from Tkinter import *
import time
import fnmatch
from tkFileDialog import askdirectory

FNULL = open(os.devnull, 'w')  # used to suppress terminal command output

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
# Select Folders
####################

directory = None
masks_folder = None
folder_name = None

def entry_fields():
	global directoy, masks_folder, folder_name
	directoy = e1.get()
	masks_folder = e2.get()
	folder_name = e3.get()
	master.destroy()

def path_choose1():
    filepath1 = askdirectory()
    e1.delete(0, 'end')
    e1.insert(0, filepath1)

def path_choose2():
    filepath2 = askdirectory()
    e2.delete(0, 'end')
    e2.insert(0, filepath2)

def path_choose3():
	filepath3 = askdirectory()
	splits = filepath3.split("/")
	filepath3 = splits[-1]
	e3.delete(0, 'end')
	e3.insert(0, filepath3)

def exitscript():
	sys.exit()

master = Tk()
master.title("Input info")
master.geometry('+1070+500')
master.wm_attributes("-topmost", 1)



Label(master, text='Path to your subject results folder').grid(row=1, padx=20, columnspan=2)
e1 = Entry(master, width=50)
e1.grid(row=2, padx=20, columnspan=2)
button1 = Button(master, text="Browse", command=path_choose1).grid(row=3, column=0, columnspan=2)

Label(master, text='').grid(row=4)

Label(master, text='Path to directory containing AFNI mask file(s) for your ROIs').grid(row=5, padx=20, columnspan=2)
e2 = Entry(master, width=50)
e2.grid(row=6, padx=20, columnspan=2)
button4 = Button(master, text="Browse", command=path_choose2).grid(row=7, column=0, columnspan=2)

Label(master, text='').grid(row=8)

Label(master, text='GLM folder containing your LME data\n(You can either type in the folder name yourself,\nor use the "Browse" button to pick an example folder from one participant).').grid(row=9, padx=20, columnspan=2)
e3 = Entry(master, width=50)
e3.grid(row=10, padx=20, columnspan=2)
button4 = Button(master, text="Browse", command=path_choose3).grid(row=11, column=0, columnspan=2)

Label(master, text='').grid(row=12)

Button(master, text='Submit', command=entry_fields).grid(row=13, sticky=S,
														 pady=4, columnspan=2)
Button(master, text='Cancel', command=exitscript).grid(row=14, sticky=S,
														 pady=4, columnspan=2)

master.update_idletasks()
windowheight = master.winfo_height()
windowwidth = master.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
master.geometry("+%s+%s" % (positionRight, positionDown))
master.wm_attributes("-topmost", 0)
mainloop()


ROIs = []
ROI_files = os.listdir(masks_folder)
for ROI_file in ROI_files:
	if ".HEAD" in ROI_file:
		ROIs.append(ROI_file[:-10])  # remove "+tlrc.HEAD" from the file name

output_directory = os.path.join(directory, "LME_results")


####################
#Check ROI files
####################

root = Tk()  # create TKinter window
root.title("ROI file check")
root.geometry('+1070+500')  # sets the location of the window - format (+horiz+vert)
root.wm_attributes("-topmost", 1)  # makes sure that the window appears on top of all other windows
label5 = Label(root, text="The following are the files which will be used for ROIs:").grid(columnspan=3)
label6 = Label(root,text="").grid(columnspan=3)
for file in ROIs:
	label7 = Label(root, text=file, font='helvetica 14 bold').grid(column=1)
label8 = Label(root,text="").grid(columnspan=3)
label9 = Label(root,text="If these are correct, click 'Continue.' If not, click 'Quit' and change the files found in:").grid(columnspan=3)
label11 = Label(root,text=masks_folder).grid(columnspan=3)
button = Button(root, text='Continue', width=25, command=root.destroy).grid(columnspan=3)  # button closes window when pressed
button1 = Button(root, text='Quit',width=23, command=sys.exit).grid(columnspan=3) # button ends script when pressed

root.update_idletasks()
windowheight = root.winfo_height()
windowwidth = root.winfo_width()
positionRight = screenx + int(screenwidth / 2 - windowwidth / 2)
positionDown = screeny + int(screenheight / 2 - windowheight / 2)
root.geometry("+%s+%s" % (positionRight, positionDown))

root.mainloop()



list_all = os.listdir(directory)

subject_folders = []

for item in list_all:
	if os.path.exists(os.path.join(directory, item, (item[5:]+".results"), folder_name)):  # if this is a subject folder that has the LME GLM folder specified
		subject_folders.append(item)


print("\n**********\n\nFinding ROI averages\n\n**********\n")

for subject_folder in subject_folders:
	subject = subject_folder[5:]
	GLM_folder = os.path.join(directory, subject_folder, (subject_folder[5:]+".results"), folder_name)
	print("*****Participant %s" % subject)
	if not os.path.exists(GLM_folder + "/AllTrials_Betas_%s+tlrc.BRIK" % subject):
		subprocess.call("3dbucket -prefix %s/AllTrials_Betas_%s %s/stats.%s+tlrc'[1..$(2)]'" % (GLM_folder, subject, GLM_folder, subject), shell=True)
		
	#Figure out how many trials there are for this subject
	if os.path.exists(os.path.join(GLM_folder, "stats_info_temp.txt")):
		os.remove(os.path.join(GLM_folder, "stats_info_temp.txt"))  # if this file remains from running the script before
	subprocess.call(['cd %s && 3dinfo -verb stats.%s+tlrc > stats_info_temp.txt' % (GLM_folder, subject)], shell=True)
	text_file = open(os.path.join(GLM_folder, 'stats_info_temp.txt'))
	file_data = text_file.read()
	splits = file_data.split(" ")
	trials = fnmatch.filter(splits, "'*#*_Coef'")
	trial_number =len(trials)
		
	for ROI in ROIs:
		print("*ROI: %s" % ROI)

		for trial in range(0, (trial_number-1)):
			# average across voxels within ROI
			output_file = "%s.ave.%s.trial%s.txt" % (subject, ROI, trial)
			subprocess.call(
				"cd %s && 3dmaskave -mask %s+tlrc 'AllTrials_Betas_%s+tlrc[%s]' > %s" % (
				GLM_folder, ROI, subject, trial, output_file), shell=True,
				stdout=FNULL, stderr=subprocess.STDOUT)

			# relocate spherical ROI average to output folder
			os.rename(os.path.join(GLM_folder, output_file), os.path.join(output_directory, output_file))


print("\n**********\n\nGenerating CSV\n\n**********\n")

csv_output = output_directory + "/aaa_magnitude_list.csv"
data_dict_list = []

for subject_folder in subject_folders:
	subject = subject_folder[5:]
	GLM_folder = os.path.join(directory, subject_folder, (subject_folder[5:]+".results"), folder_name)
	print("*****Participant %s" % subject)
	if os.path.exists(GLM_folder + "/AllTrials_Betas_%s+tlrc.BRIK" % subject):
		text_file = open(os.path.join(GLM_folder, 'stats_info_temp.txt'))
		file_data = text_file.read()
		splits = file_data.split(" ")
		trials = fnmatch.filter(splits, "'*#*_Coef'")
		trial_number =len(trials)
		os.remove(os.path.join(GLM_folder, "stats_info_temp.txt"))
		
		for trial in range(0, (trial_number-1)):
			trial_dict = {}
			trial_dict['Participant'] = subject
			trial_dict['Trial'] = trial
			for ROI in ROIs:
				with open(output_directory + '/%s.ave.%s.trial%s.txt' % (subject, ROI, trial)) as magnitude_file:
					magnitude_data = magnitude_file.readline()
				splits = magnitude_data.split(" ")
				trial_dict[ROI] = splits[0]
			data_dict_list.append(trial_dict)


columnnames = ['Participant', 'Trial'] + ROIs
output_file_path = csv_output
output_dict_list = data_dict_list
write_file = open(output_file_path, 'w')  # write new file
csvwriter = csv.DictWriter(write_file, fieldnames=columnnames)
csvwriter.writerow(dict((fn, fn) for fn in columnnames))
for index, item in enumerate(output_dict_list):
	csvwriter.writerow(item)
write_file.close()