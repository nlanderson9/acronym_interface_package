#!/usr/bin/python
import os, sys, operator, subprocess, string
import scipy.stats as st
# Written by N. Anderson 3/1/2018

# This script is meant to be used on the output of 3dttest++ when used with the -Clustsim option. This script will:

# 1. Perform the equivalent of the AFNI GUI "Clusterize" function (using 3dclust)
# 2. Save it to a mask
# 3. Create a new dataset with voxel values from the t-test, within the voxels defined by the clusterize mask
# 4. Use the map_vol_to_surface.py script to convert the result to a Workbench-formatted file.

# The script can either be used to convert individual files, or to batch convert all applicable files in the current directory.




def main():

	FNULL = open(os.devnull, 'w')  # used to suppress terminal command output

	path = os.path.dirname(os.path.realpath(__file__))  # this script's directory path
	thisdir = os.getcwd()

	all_normal_characters = string.ascii_letters + string.digits + "/_-"
	def is_special(character):
		return character not in all_normal_characters
	special_characters = [character for character in path if is_special(character)]

	if special_characters:
		character_string = ''
		unique_characters = []
		for character in special_characters:
			if character not in unique_characters:
				unique_characters.append(character)
				if character == ' ':
					character_string = character_string + "' ' (space), "
				else:
					character_string = character_string + "'%s', " % character
		character_string = character_string[:-2]

		sys.exit("XXXXX\nPlease remove any spaces and special characters from your directory path.\nCurrent path: %s\nInvalid characters: %s\nXXXXX" % (path, character_string))

	commands = []
	if len(sys.argv) < 2:
		print("\n#########################\nThis script does the following:\n1. Taking an AFNI t-test file as input, extract the -Clustsim info from the header of the file\n   and use this to generate a mask of all voxels that survive thresholding and cluster correction\n   (this is the equivalent of using the 'Savemsk' option in the 'Clusterize' interface in the\n   AFNI GUI)\n2. Create a new t-test AFNI file that only contains voxels present in the generated mask\n3. Us map_vol_to_surface.py to convert the resulting file into a surface file (GIfTI) to be used\n   in Caret/Workbench\n"
		      "#########################\n\n"
		      "Command argument options:\n\n\n"
			  "**Required: (unless you set loop=true; see below)\n\n"
		      "   filename	= AFNI file in current directory\n\n\n"
		      "**Required: at least one\n\n"
			  "   p		= The desired p-value to threshold your map (e.g. 0.05, 0.001)\n\n"
		      "   z		= The desired z-value to threshold your map (e.g. 1.96, 3.291)\n"
		      "		  Note: the actual z-value used might be adjusted to match a round p-value.\n\n"
			  "**Required:\n\n"
		      "   alpha	= The desired alpha-value to threshold your map (e.g. 0.05, 0.01). Default is '0.05'.\n\n"
			  "   NN		= The NN level - valid options are '1', '2', or '3'. Default is '3'.\n"
		      "		  (Type 'NN=more' as an argument to see an explanation of the different NN levels.)\n\n"
			  "   bisided	= Determines approach to pos/neg values - valid options are 'true' or 'false'. Default is 'true'.\n"
		      "		  (Type 'bisided=more' as an argument to see an explanation of how AFNI handles this parameter.)\n\n"
			  "*Optional:\n\n"
			  "   loop		= loop through all applicable files in the current directory - valid options are 'true' or 'false'. Default is 'false'.\n"
		      "		  Note: if loop=true, a filename does not need to be provided (and if provided, it will be ignored)\n\n"
			  "   suffix	= a unique suffix to be added to the end of your output file(s).\n\n"
			  "   keepnifti 	= when converting volume to surface, determines if the intermediate NIfTI file is kept or deleted - valid options are 'true' or 'false'.\n"
			  "		  Default is 'false'.\n\n"
			  "   keepafni     = when performing cluster correction, determines if the intermediate AFNI file is kept (the original data, with voxels outside surviving clusters removed).\n"
			  "		  Valid options are 'true' or 'false'. Default is 'false'.\n\n\n"
			  "All arguments must be provided in the form arg=value (e.g. NN=1 or bisided=false). Filename may be included without 'filename='. Any order is permitted.\n")
		sys.exit()
	if len(sys.argv) > 1:
		commands = sys.argv

	filename = None
	p = None
	z = None
	alpha = '0.05'
	NN = '3'
	bisided = True
	loop = False
	suffix = ''
	keepnifti = False
	keepafni = False

	for command in commands:
		if "p=" in command and "loop" not in command:
			p = command[2:]
		if "z=" in command:
			z = command[2:]
		if "alpha=" in command:
			alpha = command[6:]
		if "NN=" in command:
			NN = command[3:]
			if "more" in command:
				print("\n# The NN level refers to AFNI's clustering method, and determines\n"
					  "# whether voxels are considered part of a cluster:\n\n"
					  "# 1: faces must touch\n"
					  "# 2: faces or edges touch\n"
					  "# 3: faces or edges or corners touch\n\n"
					  "# The most conservative choice is 1, with the least conservative\n"
					  "# being 3. However, as has been stated elsewhere, 'a box is not\n"
					  "# a recognized unit of cortical organization.'\n")
				sys.exit()
		if "bisided=" in command:
			bisided_string = command[8:]
			if bisided_string == 'true':
				bisided = True
			elif bisided_string == 'false':
				bisided = False
			else:
				bisided = bisided_string
			if "more" in command:
				print("\n# 'Bisided' refers to how AFNI treats positive and negative voxels: \n\n"
					  "# true: positively and negatively thresholded voxels get clustered separately\n"
					  "# false: positively and negatively thresholded voxels get clustered together\n\n"
					  "# Choosing 'true' means, for example, that a cluster of negatively-thresholded\n"
					  "# will have to survive clustering thresholds, even if there are a sufficient\n"
					  "# number of positively-thresholded voxels nearby. Choosing 'false' would allow\n"
					  "# a small number of negatively-thresholded voxels to survive, as long as it was\n"
					  "# contiguous with a large enough group of positively-thresholded voxels.\n"
					  "# Therefore, 'true' is a more conservative choice.\n")
		if "loop=" in command:
			loop_string = command[5:]
			if loop_string == 'true':
				loop = True
			elif loop_string == 'false':
				loop = False
			else:
				loop = loop_string
		if "suffix=" in command:
			suffix = command[7:]
		if "keepnifti=" in command:
			keepnifti_string = command[10:]
			if keepnifti_string == 'true':
				keepnifti = True
			elif keepnifti_string == 'false':
				keepnifti = False
			else:
				keepnifti = keepnifti_string
		if "keepafni=" in command:
			keepafni_string = command[9:]
			if keepnifti_string == 'true':
				keepafni = True
			elif keepafni_string == 'false':
				keepafni = False
			else:
				keepafni = keepafni_string
		if any(x in command for x in ['.HEAD', '.BRIK']) or os.path.exists(
				thisdir + "/" + command + ".HEAD") or os.path.exists(thisdir + "/" + command[9:] + ".HEAD"):
			if command.startswith('filename='):
				filename = command[9:]
			else:
				filename = command


	if p and z:
		sys.exit("You cannot specify both a p-value and a z-value. Please select only one.")

	if p:
		try:
			float(p)
		except ValueError:  # if the value provided for p is not a decimal
			sys.exit("Please provide a valid option for the argument 'p'")

	if z:
		try:
			float(z)
		except ValueError:  # if the value provided for p is not a decimal
			sys.exit("Please provide a valid option for the argument 'z'")

	if not p and not z:
		sys.exit("You must provide at least one threshold value using either 'p' or 'z'")

	if alpha:
		try:
			float(alpha)
		except ValueError:  # if the value provided for p is not a decimal
			sys.exit("Please provide a valid option for the argument 'alpha'")
	else:
		sys.exit("Please provide a valid option for the argument 'alpha'")

	if not any(x == NN for x in ['1', '2', '3']):
		sys.exit("Please provide a valid option for the argument 'NN'")
	if not any(x == bisided for x in [True, False]):
		sys.exit("Please provide a valid option for the argument 'bisided'")
	if loop:
		if not any(x == loop for x in [True, False]):
			sys.exit("Please provide a valid option for the argument 'loop'")
	if not any(x == keepnifti for x in [True, False]):
		sys.exit("Please provide a valid option for the argument 'keepnifti'")
	if not any(x == keepafni for x in [True, False]):
		sys.exit("Please provide a valid option for the argument 'keepafni'")
	if len(commands) > 0:
		if not loop:
			if filename:
				if not(os.path.exists(thisdir + "/" + filename) or os.path.exists(thisdir + "/" + filename + ".HEAD")):
					sys.exit("Please provide a valid AFNI file name, or set loop=true")
			if not filename:
				sys.exit("Please provide a valid AFNI file name, or set loop=true")

	if loop and filename:
		decision = raw_input("XXX\nWarning - you've supplied a filename and set loop=true. Your filename will be ignored, and all files in this directory will be converted.\nDo you wish to continue? (y/n)  ")
		if decision == 'n':
			sys.exit()


	if z:
		p_options = [0.1, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.007, 0.005, 0.003, 0.002,
					 0.0015, 0.001, 0.0007, 0.0005, 0.0003, 0.0002, 0.00015, 0.0001, 7e-05, 5e-05, 3e-05, 2e-05,
					 1.5e-05, 1e-05]
		p_start = (1 - st.norm.cdf(float(z))) * 2
		p_fits = {}
		for item in p_options:
			diff = abs(p_start - item)
			p_fits[item] = diff

		result = min(p_fits.iteritems(), key=operator.itemgetter(1))[0]
		p = str(result)

	if filename:
		if (".HEAD" in filename or ".BRIK" in filename) and (".BRIK.gz" not in filename):
			filename = filename[:-5]
		if ".BRIK.gz" in filename:
			filename = filename[:-8]
	if p.startswith("."):
		p = '0' + p
	if alpha.startswith("."):
		alpha = '0' + alpha
	if suffix:
		if not suffix.startswith("_") and not suffix.startswith(".") and not suffix.startswith("-"):
			suffix = "_" + suffix


	if loop:
		files = os.listdir(thisdir)
		files = [filenamex[:-5] for filenamex in files if ".HEAD" in filenamex]
	else:
		files = [filename]  # Will only run loop once if this script is being used for a single file




	for filename in files:
		if os.path.exists(thisdir + "/Clust_mask+tlrc.HEAD") or os.path.exists(thisdir + "/Clust_mask+tlrc.BRIK.gz"):
			sys.exit("There are Cluster masks remaining from previous use of this script (Clust_mask+tlrc) - please delete these before continuing.")

		if os.path.exists(thisdir + "/%s_Clust%s+tlrc.HEAD" % (filename[:-5],suffix)) or os.path.exists(thisdir + "/%s_Clust%s+tlrc.BRIK.gz" % (filename[:-5],suffix)):
			sys.exit("There are intermediate AFNI files remaining from previous use of this script (%s_Clust%s+tlrc) - please delete these before continuing." % (filename[:-5],suffix))
		if os.path.exists(thisdir + "/%s_Clust%s.nii" % (filename[:-5],suffix)):
			sys.exit("There are intermediate NIfTI files remaining from previous use of this script (%s_Clust%s.nii) - please delete these before continuing." % (filename[:-5],suffix))
		if os.path.exists(thisdir + "/%s_Clust%s_L.func.gii" % (filename[:-5],suffix)) or os.path.exists(thisdir + "/%s_Clust%s_R.func.gii" % (filename[:-5],suffix)):
			sys.exit("The output GIfTI surface files already exist (%s_Clust%s_L/R.func.gii) - please delete these before continuing." % (filename[:-5],suffix))

		thresh = st.norm.ppf(1 - float(p) / 2)
		thresh = round(thresh, 3)
		if z:
			print("***\nDesired z-value: %s\nActual z-value used: %s\np-value used: %s\n***" % (z, thresh, p))


		# Access AFNI file header, to obtain minimum number of voxels per cluster to meet p-value/alpha settings
		# These are the results of -Clustsim calculation from the original t-test

		file_header =  thisdir + '/%s.HEAD' % filename

		with open(file_header) as header:
			data = header.readlines()

		if NN == '1':
			NN_level = "NN1"
		elif NN == '2':
			NN_level = "NN2"
		elif NN == '3':
			NN_level = "NN3"

		if bisided:
			sided = "bisided"
		else:
			sided = "1sided"

		name = "AFNI_CLUSTSIM_%s_%s" % (NN_level, sided)

		pthresholds = None
		athresholds = None
		numbers = []

		start = False
		numbers_start = False
		for line in data:
			if ("name = %s" % name) in line:
				start = True
			if start and "pthr=" in line:
				pthresholds = line
			if start and "athr=" in line:
				athresholds = line
			if start and "mask_count=" in line:
				numbers_start = True
				pass
			if numbers_start and ("</3dClustSim_%s>~" % NN_level) in line:
				break
			if numbers_start and "mask_count" not in line:
				numbers.append(line)

		if not numbers:
			sys.exit("Make sure that you have run your t-test with the -Clustsim option, and that the results were added to the your file's header.")


		pthresholds = pthresholds[8:-2].split(",")
		pthresholds_float = [float(x) for x in pthresholds]
		athresholds = athresholds[8:-2].split(",")

		numbers_lists = []

		for item in numbers:
			numbers_lists.append(item[1:-1].split(" "))

		if not float(p) in pthresholds_float:
			sys.exit(
				"You p-value is not included in AFNI's list of simulated p-values to determine minimum cluster sizes. Please choose one of the following thresholds:\n%s" % pthresholds)
		else:
			index = pthresholds_float.index(float(p))

		if not alpha in athresholds:
			sys.exit(
				"Your alpha-value is not included in AFNI's list of simulated alpha-values to determine minimum cluster sizes. Please choose one of the following thresholds:\n%s" % athresholds)

		cluster_sizes = dict(zip(athresholds, numbers_lists[index]))

		if keepnifti:
			keepnifti_input = 'true'
		else:
			keepnifti_input = 'false'

		voxel_number = cluster_sizes[alpha]
		print("\nperforming cluster correction for %s...." % filename)


		subprocess.call("3dclust -1Dformat -nosum -1dindex 0 -1tindex 1 -2thresh -%s %s -dxyz=1 -savemask Clust_mask -%s %s %s" % (thresh, thresh, NN_level, voxel_number, filename), shell=True)#, stdout=FNULL, stderr=subprocess.STDOUT)  # create the mask; equivalent to Clusterize function in AFNI GUI
		subprocess.call("3dcalc -a Clust_mask+tlrc -b %s'[0]' -expr 'step(a)*b' -prefix %s_Clust%s" % (filename, filename[:-5], suffix), shell=True)#, stdout=FNULL, stderr=subprocess.STDOUT)  # create a new dataset, comprised of the data from the input dataset but only within regions specified by the mask
		subprocess.call("python %s/map_vol_to_surface.py %s_Clust%s+tlrc keepnifti=%s" % (path, filename[:-5], suffix, keepnifti_input), shell=True)  # use map_vol_to_surface.py to convert to Workbench format

		# Delete Cluster masks
		if os.path.exists(thisdir + "/Clust_mask+tlrc.HEAD"):
			os.remove(thisdir + "/Clust_mask+tlrc.HEAD")
		if os.path.exists(thisdir + "/Clust_mask+tlrc.BRIK.gz"):
			os.remove(thisdir + "/Clust_mask+tlrc.BRIK.gz")

		# Delete intermediate AFNI files
		if not keepafni:
			if os.path.exists(thisdir + "/%s_Clust%s+tlrc.HEAD" % (filename[:-5], suffix)):
				os.remove(thisdir + "/%s_Clust%s+tlrc.HEAD" % (filename[:-5], suffix))
			if os.path.exists(thisdir + "/%s_Clust%s+tlrc.BRIK.gz" % (filename[:-5], suffix)):
				os.remove(thisdir + "/%s_Clust%s+tlrc.BRIK.gz" % (filename[:-5], suffix))



if __name__ == "__main__":
	main()
