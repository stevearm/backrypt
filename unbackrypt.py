import sys, os, random, struct, hashlib, subprocess, datetime, shutil, tarfile, aestool
from index import Index

if len(sys.argv) < 5:
	print("Usage: python backrypt.py password archive_file temp_dir dest_dir")
	sys.exit(1)

password = sys.argv[1]
archive_file = sys.argv[2]
temp_dir = sys.argv[3]
dest_dir = sys.argv[4]

# Prepare the directory
if os.path.isdir(temp_dir):
	shutil.rmtree(temp_dir)
os.makedirs(temp_dir)
staging_dir = os.path.join(temp_dir, 'staging')

def decrypt_and_extract(file):
	if not os.path.isfile(file):
		print("Archive file not found: %s" % file)
		sys.exit(1)
	if file[-4:] != '.enc':
		print("Archive file must be encoded: %s" % file)
		sys.exit(1)
	name = os.path.basename(file)
	tar_path = os.path.join(temp_dir, name[:-4])
	aestool.decrypt_file(aestool.get_key(password), file, tar_path)
	tar = tarfile.open(tar_path, 'r')
	tar.extractall(temp_dir)
	tar.close()
	print("Decrypting and unpacking: %s" % file)

# Decrypt and expand main file
decrypt_and_extract(archive_file)

# Load index
(archive_dir, archive_name) = os.path.split(archive_file)
index = Index(os.path.join(staging_dir, '%s.backrypt' % archive_name[:13]))

# Extract any other needed archives
other_archives = []
for file, md5 in index.path_to_md5.items():
	other_archive = index.md5_to_archive[md5]
	if other_archive != archive_name and other_archive not in other_archives:
		decrypt_and_extract(os.path.join(archive_dir, other_archive))
		other_archives.append(other_archive)


# Copy out and rename files
if not os.path.isdir(dest_dir):
	os.makedirs(dest_dir)
for file, md5 in index.path_to_md5.items():
	file_destination = os.path.join(dest_dir, file)
	file_destination_dir = os.path.dirname(file_destination)
	if not os.path.isdir(file_destination_dir):
		os.makedirs(file_destination_dir)
	md5_path = dir = os.path.join(staging_dir, md5[0:2], md5[2:4], md5)
	shutil.copyfile(md5_path, file_destination)
	print("Copied out %s" % file)

# Cleanup
try:
	shutil.rmtree(temp_dir)
except:
	print("Error deleting temp dir %s" % temp_dir)
