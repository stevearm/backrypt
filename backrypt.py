import sys, os, random, struct, hashlib, subprocess, datetime, shutil, tarfile, aestool
from index import Index

if len(sys.argv) < 5:
	print("Usage: python backrypt.py password dir_to_backup temp_dir archive_dest_dir")
	sys.exit(1)

password = sys.argv[1]
source_dir = sys.argv[2]
temp_dir = sys.argv[3]
dest_dir = sys.argv[4]

local_cache_file = os.path.join(source_dir, '.backrypt')

index = Index(local_cache_file)

# Scan any files modified since last run
index.update_md5s(source_dir)

# Prepare the directory
if os.path.isdir(temp_dir):
	shutil.rmtree(temp_dir)
os.makedirs(temp_dir)
staging_dir = os.path.join(temp_dir, 'staging')
os.makedirs(staging_dir)

# Filenames
now_string = datetime.datetime.today().strftime('%Y%m%d_%H%M')
tar_name = '%s.tar.bz2' % now_string
archive_name = '%s.enc' % tar_name

# Copy needed files
file_count = 0
for file, md5 in index.path_to_md5.items():
	if md5 not in index.md5_to_archive:
		file_count = file_count + 1
		
		# Record that this hash is in this archive
		index.md5_to_archive[md5] = archive_name
		
		# Copy the file
		dir = os.path.join(staging_dir, md5[0:2], md5[2:4])
		if not os.path.isdir(dir):
			os.makedirs(dir)
		shutil.copyfile(os.path.join(source_dir, file), os.path.join(dir, md5))
index.write(os.path.join(staging_dir, '%s.backrypt' % now_string))

if file_count == 0:
	shutil.rmtree(temp_dir)
	print('No new or modified files to backup since last backup')
	sys.exit(0)

# Tar up staging_dir to os.path.join(temp_dir, tgz_name)
tar_path = os.path.join(temp_dir, tar_name)
tar = tarfile.open(tar_path, 'w:bz2')
tar.add(staging_dir, arcname='staging')
tar.close()

# Encrypt tgz to os.path.join(temp_dir, archive_name)
archive_path = os.path.join(temp_dir, archive_name)
key = aestool.get_key(password)
aestool.encrypt_file(key, tar_path, archive_path)

# Copy the archive
shutil.copyfile(archive_path, os.path.join(dest_dir, archive_name))

# Write back out the index
index.write(local_cache_file)

# Cleanup
shutil.rmtree(temp_dir)
