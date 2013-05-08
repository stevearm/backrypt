import os, subprocess

def list_files(dir):
	all_files = []
	for root, subFolders, files in os.walk(dir):
		common_base = root.replace(dir, '', 1)
		if (len(common_base) > 0 and (common_base[0] == '/' or common_base[0] == '\\')):
			common_base = common_base[1:]
		for file in files:
			if ('.backrypt' != file):
				all_files.append(os.path.join(common_base, file))
	return all_files

class Index():
	def __init__(self, filename):
		self.mod_time = 0
		self.path_to_md5 = {}
		self.md5_to_archive = {}
		
		if not os.path.isfile(filename):
			return
		
		self.mod_time = os.stat(filename).st_mtime
		
		file = open(filename, 'rb')
		try:
			line = file.readline()
			if (line != 'md5s\n'):
				raise Exception('Missing md5 tag from %s' % filename)
			while True:
				line = file.readline()
				if (line == 'backup history\n'):
					break;
				if (line == ''):
					raise Exception('Missing backup history tag from %s' % filename)
				path = line[:-34]
				md5 = line[-33:-1]
				self.path_to_md5[path] = md5
			
			while True:
				line = file.readline()
				if (line == ''):
					break
				md5 = line[:32]
				archive = line[33:-1]
				self.md5_to_archive[md5] = archive
		finally:
			file.close()

	def write(self, filename):
		file = open(filename, 'wb')
		try:
			file.write('md5s\n')
			tmp = []
			for key, value in self.path_to_md5.items():
				tmp.append('%s %s\n' % (key, value))
			tmp.sort()
			for line in tmp:
				file.write(line)
			
			file.write('backup history\n')
			tmp = []
			for key, value in self.md5_to_archive.items():
				tmp.append('%s %s\n' % (key, value))
			tmp.sort()
			for line in tmp:
				file.write(line)
		finally:
			file.close()

	def update_md5s(self, base_dir):
		old_md5s = self.path_to_md5
		self.path_to_md5 = {}
		for file in list_files(base_dir):
			true_path = os.path.join(base_dir, file)
			if (os.stat(true_path).st_mtime < self.mod_time and file in old_md5s):
				self.path_to_md5[file] = old_md5s[file]
			else:
				print('New or modified file: %s' % file)
				proc = subprocess.Popen(['md5deep',true_path],stdout=subprocess.PIPE)
				md5_result = proc.stdout.readline()
				if (len(md5_result) <= 32 or md5_result[32] != ' '):
					raise Exception("Crazy output while md5ing %s: %s" % (true_path, md5_result))
				self.path_to_md5[file] = md5_result[:32]
