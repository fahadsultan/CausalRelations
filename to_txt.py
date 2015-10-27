import os 

from bs4 import BeautifulSoup

count = pd.DataFrame(columns = ['filename', 'count'])
for folder, subs, files in os.walk('data/xml'):
	
	for filename in files:
		
		try:
			if ('.xml' in filename) and (filename[0] != '.'):
				f = open(os.path.join(folder, filename))
				soup = BeautifulSoup(f.read())
				tokens = soup.findAll('token')
				tokens_arr = [token.text for token in tokens]
				text = ' '.join(tokens_arr)
				f = open('data/text/'+filename, 'w')
				f.write(text)
				f.close()
		except Exception as e:
			print e
			continue