count = {}
for folder, subs, files in os.walk('data/xml'):
	
	for filename in files:
		
		try:
			if ('.xml' in filename) and (filename[0] != '.'):
				f = open(os.path.join(folder, filename))
				soup = BeautifulSoup(f.read())
				clink_count = len(soup.findAll('clink'))
				print clink_count
				count[filename] = clink_count
		except Exception as e:
			print e
			continue