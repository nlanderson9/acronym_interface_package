#!/usr/bin/python
import os, sys, subprocess, gzip, string
# Written by N. Anderson 3/1/2018. Adapted from E. Gordon's Matlab script.


def main():

	FNULL = open(os.devnull, 'w')  # used to suppress terminal command output

	path = os.path.dirname(os.path.realpath(__file__)) # this script's directory path
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



	# paths to the left and right surfaces as well as the white and pial surfaces
	Lsurface = path + '/surface_files/Conte69.L.midthickness.32k_fs_LR.surf.gii'
	Lwhitesurface = path + '/surface_files/Conte69.L.white.32k_fs_LR.surf.gii'
	Lpialsurface = path + '/surface_files/Conte69.L.pial.32k_fs_LR.surf.gii'
	Rsurface = path + '/surface_files/Conte69.R.midthickness.32k_fs_LR.surf.gii'
	Rwhitesurface = path + '/surface_files/Conte69.R.white.32k_fs_LR.surf.gii'
	Rpialsurface = path + '/surface_files/Conte69.R.pial.32k_fs_LR.surf.gii'

	# where the 711-2B to MNI tranform is located on the server/computer
	# not implemented - only needed for FIDL -> GIfTI conversion
	#T4_7112B_to_MNI = path + '/surface_files/711-2B_to_MNI152lin_T1_t4'

# 	path to the folder containing 'wb_command'
	workbenchdir = path + '/bin_macosx64'

	commands = []
	if len(sys.argv) < 2:
		print("\n#########################\nThis script will convert a neuroimaging volume file (AFNI HEAD/BRIK, FIDL 4dfp.img, or NIfTI)\ninto a GIfTI surface file, which is used in Caret/Workbench.\n"
		      "#########################\n\n"
		      "Command argument options:\n\n\n"
			  "**Required: \n\n"
			  "   filename	= NIfTI, AFNI, or 4dfp file, must be in current directory\n\n\n"
			  "*Optional:\n\n"
			  "   hem		= hemisphere - valid options are 'L', 'R', or 'both'. Default is 'both'.\n\n"
			  "   mappingtype 	= method used to map volume to surface - valid options are 'enclosing', 'trilinear', or 'ribbon-constrained'. Default is 'ribbon-constrained'.\n"
			  "		  (Type 'mappingtype=more' as an argument to see a description from the wb_command help text.)\n\n"
			  "   space	= valid options are 'MNI' or '711-2B'. Default is 'MNI'.\n\n\n"
			  "*Optional: only when converting AFNI .HEAD/.BRIK files:\n\n"
			  "   subbrick		= subbrick of AFNI file that you want to convert. If your file has no subbricks, you do not need to include this argument. Default is '0'.\n\n"
			  "   keepnifti 	= determines if the intermediate NIfTI file is kept or deleted - valid options are 'true' or 'false'. Default is 'false'.\n\n\n"
			  "Optional arguments must be provided in the form arg=value (e.g. hem=both or space=MNI). Filename may be included without 'filename='. Any order is permitted.\n\n\n"
			  "NOTE: This program does not yet support the conversion of 4dfp filetypes.\n"
			  "NOTE: This program does not yet support the use of 'enclosing' or 'trilinear' mappingtype values.\n")
		sys.exit()
	if len(sys.argv) > 1:
		commands = sys.argv


	hem = 'both'
	mappingtype = 'ribbon-constrained'
	space = 'MNI'
	filename = None
	subbrick = 0
	keepnifti = False

	for command in commands:
		if "hem=" in command:
			hem = command[4:]
		if "mappingtype=" in command:
			mappingtype = command[12:]
			if "more" in command:
				print("\n# Mapping type descriptions (from the wb_command help text):\n\n"
					  "# Enclosing voxel uses the value from the voxel the vertex lies\n"
					  "# inside, while trilinear does a 3D linear interpolation based on\n"
					  "# the voxels immediately on each side of the  vertex's position.\n"
					  "# The ribbon mapping method constructs a polyhedron from the\n"
					  "# vertex's neighbors on each surface, and estimates the amount of\n"
					  "# this polyhedron's volume that falls inside any nearby voxels, to\n"
					  "# use as the weights for sampling.  The volume ROI is useful to\n"
					  "# exclude partial volume effects of voxels the surfaces pass\n"
					  "# through, and will cause the mapping to ignore voxels that don't\n"
					  "# have a positive value in the mask.  The subdivision number\n"
					  "# specifies how it approximates the amount of the volume the\n"
					  "# polyhedron intersects, by splitting each voxel into NxNxN pieces,\n"
					  "# and checking whether the center of each piece is inside the\n"
					  "# polyhedron.  If you have very large voxels, consider increasing\n"
					  "# this if you get zeros in your output.\n")
				sys.exit()
		if "space=" in command:
			space = command[6:]
		if "subbrick" in command:
			subbrick = int(command[8:])
		if "keepnifti=" in command:
			keepnifti_string = command[10:]
			if keepnifti_string == 'true':
				keepnifti = True
			elif keepnifti_string == 'false':
				keepnifti = False
			else:
				keepnifti = keepnifti_string
		if any(x in command for x in ['4dfp.img', '.nii','.HEAD','.BRIK']) or os.path.exists(thisdir + "/" + command + ".HEAD") or os.path.exists(thisdir + "/" + command[9:] + ".HEAD"):
			if command.startswith('filename='):
				filename = command[9:]
			else:
				filename = command

	if not any(x == hem for x in ['L', 'R', 'both']):
		sys.exit("Please provide a valid option for the argument 'hem'")
	if not any(x == mappingtype for x in ['enclosing', 'trilinear', 'ribbon-constrained']):
		sys.exit("Please provide a valid option for the argument 'mappingtype'")
	if not any(x == space for x in ['MNI', '711-2B']):
		sys.exit("Please provide a valid option for the argument 'space'")
	if subbrick:
		try:
			int(subbrick)
		except ValueError:  # if the value provided for the subbrick is not an integer
			sys.exit("Please provide a valid option for the argument 'subbrick'")
	if not any(x == keepnifti for x in [True, False]):
		sys.exit("Please provide a valid option for the argument 'keepnifti'")
	if len(commands) > 0:
		if not filename or not os.path.exists(thisdir + "/" + filename):
			if not os.path.exists(thisdir + "/" + filename + ".HEAD"):
				sys.exit("Please provide a valid file name (.nii, .HEAD/.BRIK, or .4dfp.img)")

	print("converting volume to surface....")
	
	mappingtype_orig = mappingtype
	volume = thisdir + "/" + filename
	deletenifti = False

	# check if volume is a 4dfp and convert to nifti if needed
	if ".4dfp.img" in volume:
		subprocess.call('nifti_4dfp -n %s %s.nii' % (volume, volume[:-9]), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
		volume = volume[:-9] + ".nii"
		deletenifti = True
	elif ".nii.gz" in volume:
		unzipped = gzip.open(volume,'rb')
		volume = unzipped.read()
		unzipped.close()
		deletenifti = True
	elif ".HEAD" in volume or ".BRIK" in volume or os.path.exists(volume + ".HEAD") or os.path.exists(volume + ".BRIK"):
		if ".HEAD" in volume or (".BRIK" in volume and not ".BRIK.gz" in volume):
			volume = volume[:-5]
		if ".BRIK.gz" in volume:
			volume = volume[:-8]
		subprocess.call("3dAFNItoNIFTI %s'[%s]'" % (volume, subbrick), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
		volume = volume[:-5] + ".nii"
		if not keepnifti:
			deletenifti = True
	
	
	
	# Transform to MNI if desired
	# not implemented - only needed for FIDL -> GIfTI conversion
# 	if space == '711-2B':
# 		subprocess.call('nifti_4dfp -4 %s Temp.4dfp.img' % volume, shell=True)
# 		subprocess.call('t4img_4dfp %s Temp.4dfp.img Temp_MNI.4dfp.img' % T4_7112B_to_MNI, shell=True)
# 		subprocess.call('nifti_4dfp -n Temp_MNI.4dfp.img %s_MNI.nii' % volume[:-9], shell=True)
# 		subprocess.call('rm %s/Temp*' % thisdir, shell=True)
# 		deletenifti = True
# 		volume = volume[:-9] + "_MNI.nii"

	# Map to surface
	if hem == 'both' or hem == 'L':
		if mappingtype_orig == 'ribbon-constrained':
			mappingtype = 'ribbon-constrained ' + Lwhitesurface + " " + Lpialsurface + " -voxel-subdiv 5"
		subprocess.call('%s/wb_command -volume-to-surface-mapping %s %s %s_L.func.gii -%s' % (workbenchdir, volume, Lsurface, volume[:-4], mappingtype), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
		print("output: %s_L.func.gii" % volume[:-4])
	if hem == 'both' or hem == 'R':
		if mappingtype_orig == 'ribbon-constrained':
			mappingtype = 'ribbon-constrained ' + Rwhitesurface + " " + Rpialsurface + " -voxel-subdiv 5"
		subprocess.call('%s/wb_command -volume-to-surface-mapping %s %s %s_R.func.gii -%s' % (workbenchdir, volume, Rsurface, volume[:-4], mappingtype), shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
		print("output: %s_R.func.gii" % volume[:-4])


	# Clean up temporary files
	if deletenifti:
		os.remove(volume)



if __name__ == "__main__":
	main()