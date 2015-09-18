
from bs4 import BeautifulSoup
import os
import pandas as pd
import sys

class Parser:

	def __init__(self):
		self.data = []

	def getEventPairs(self):

		for folder, subs, files in os.walk('data/xml'):
			
			for filename in files:
				
				try:
					print filename
					if ('.xml' in filename) and (filename[0] != '.'):
						f = open(os.path.join(folder, filename))
						soup = BeautifulSoup(f.read())
						events = soup.findAll('event')
						tokens = soup.findAll('token')
						
						for i in range(0,len(events)-1):

							event = events[i]

							for j in range(i+1, len(events)):

								next_event = events[j]

								event_token_id 		= event.find('token_anchor').attrs['id']
								next_event_token_id = next_event.find('token_anchor').attrs['id']

								event_token_tag 	 =	soup.find(lambda tag: tag.name == 'token' and
																		tag['id'] == event_token_id)

								next_event_token_tag = 	soup.find(lambda tag: tag.name == 'token' and
																		tag['id'] == next_event_token_id)



								event_sentence = event_token_tag['sentence']
								next_event_sentence = next_event_token_tag['sentence']

								if (int(next_event_sentence) - int(event_sentence)) > 1:
									
									break #Since we are only catering for events in the current sentence and the next one 

								else:
									
									event_one_token_id 	= event_token_tag.attrs['id']
									event_one_number 	= event_token_tag.attrs['number']
									event_one_sentence 	= event_sentence
									event_one_token 	= event_token_tag.text
									event_one_aspect 	= event.attrs['aspect']
									event_one_certainty = event.attrs['certainty']
									event_one_class 	= event.attrs['class']
									event_one_comment 	= event.attrs['comment']
									event_one_factuality= event.attrs['factuality']
									event_one_event_id 	= event.attrs['id']
									event_one_modality 	= event.attrs['modality']
									event_one_polarity 	= event.attrs['polarity']
									event_one_pos 		= event.attrs['pos']
									event_one_tense 	= event.attrs['tense']

									event_two_token_id 	= next_event_token_tag.attrs['id']
									event_two_number 	= next_event_token_tag.attrs['number']
									event_two_sentence 	= event_sentence
									event_two_token 	= next_event_token_tag.text
									event_two_aspect 	= next_event.attrs['aspect']
									event_two_certainty	= next_event.attrs['certainty']
									event_two_class 	= next_event.attrs['class']
									event_two_comment 	= next_event.attrs['comment']
									event_two_factuality= next_event.attrs['factuality']
									event_two_event_id 	= next_event.attrs['id']
									event_two_modality 	= next_event.attrs['modality']
									event_two_polarity 	= next_event.attrs['polarity']
									event_two_pos 		= next_event.attrs['pos']
									event_two_tense 	= next_event.attrs['tense']
									
									causal_relation_exists = len(soup.findAll(lambda tag: 
																tag.name == 'source' and 
																tag.findParent().name == 'clink' and 
																tag.findNextSibling().name == 'target' and

																((tag.attrs['id'] == event_one_event_id and 
																	tag.findNextSibling().attrs['id'] == event_two_event_id) 
																or 
																(tag.attrs['id'] == event_two_event_id and 
																	tag.findNextSibling().attrs['id'] == event_one_event_id))  )) > 0


									row = [	filename.split('.xml')[0],
											event_one_token_id, 
											event_one_number,
											event_one_sentence,
											event_one_token,
											event_one_aspect, 
											event_one_certainty,
											event_one_class,
											event_one_comment,
											event_one_factuality,
											event_one_event_id,
											event_one_modality,
											event_one_polarity,
											event_one_pos,
											event_one_tense,
											event_two_token_id, 
											event_two_number,
											event_two_sentence,
											event_two_token,
											event_two_aspect, 
											event_two_certainty,
											event_two_class,
											event_two_comment,
											event_two_factuality,
											event_two_event_id,
											event_two_modality,
											event_two_polarity,
											event_two_pos,
											event_two_tense,
											causal_relation_exists  ]


									self.data.append(row)
				except Exception as e:
					print '-----------------'
					print e
					print filename
					print sys.exc_info()[0]
					print '-----------------'
					continue

if __name__ == "__main__":
	parser = Parser()
	parser.getEventPairs()