import os, sys
from bs4 import BeautifulSoup

for folder, subs, files in os.walk('data/xml'):
	
	for filename in files:
		
		# try:
			
		if ('.xml' in filename) and (filename[0] != '.'):
			
			in_file = open(os.path.join(folder, filename))
			soup = BeautifulSoup(in_file.read())
			token_tags = soup.findAll('token')
			tokens = [tag.text for tag in token_tags]
			text = ' '.join(tokens)
			out_file = open(os.path.join('data/out', filename.replace('.xml', '.txt')), 'w')
			out_file.write(text)
			out_file.close()
			in_file.close()
		# except Exception as e:
		# 	print 'Exception '+filename+" "
		# 	print sys.exc_info()[0]
		# 	continue
