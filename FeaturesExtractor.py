
from bs4 import BeautifulSoup
import os
import pandas as pd
import sys
import traceback
from sklearn.feature_extraction.text import CountVectorizer

class FeaturesExtractor:

    def __init__(self):

        self.FEATURE_NAMES = ['e1_token_id', 'e1_number','e1_sentence','e1_token','e1_aspect', 'e1_class','e1_event_id','e1_modality','e1_polarity','e1_pos','e1_tense','e2_token_id', 'e2_number','e2_sentence','e2_token','e2_aspect', 'e2_class','e2_event_id','e2_modality','e2_polarity','e2_pos','e2_tense','dep_path', 'same_pos_tag','sentence_distance','event_distance','same_polarity','same_aspect','same_tense','same_class','csignals_in_bw','csignal_position','tlink_exists','e1_is_sent_root','e2_is_sent_root','causal_relation_exists']

        COLUMN_NAMES = ['filename', 'sentence', 'relation', 'governor',
                 'governor_idx', 'dependent', 'dependent_idx']

        self.data = []

        self.deps = pd.read_csv('data/text/_out_dependencies.csv', 
                                    names=COLUMN_NAMES, sep='\t')

    def recursive_search(self, df, path, to_find_token, 
        to_find_index, to_find_sentence, governor_token,
        governor_index, governor_sentence):
        
        dependencies = df[(self.deps['governor'] == governor_token) & 
                            (self.deps['governor_idx'] == int(governor_index)) &
                            (self.deps['sentence'] == int(governor_sentence))]

        for i in range(len(dependencies)):

            dependency = dependencies.iloc[i]

            #Weird idiosynracy I came across where the governor and the dependent 
            #were the same token
            if ((dependency['governor'] == dependency['dependent']) and
                (dependency['dependent_idx'] == dependency['governor_idx'])):
                continue

            #check break condition
            if (dependency['dependent'] == to_find_token and
                dependency['dependent_idx'] == to_find_index and
                dependency['sentence'] == to_find_sentence):

                path = path+' '+dependency['relation']
                break

            else:
                path_to_pass = path+' '+dependency['relation'] 
                path_returned = self.recursive_search(
                         df, path_to_pass, to_find_token, 
                         to_find_index, to_find_sentence, dependency['dependent'],
                         dependency['dependent_idx'], dependency['sentence'])

                if path_returned != path_to_pass:
                    path = path_returned
                    break

        return path

    def get_dependency_path(self, filename, e1_token, e1_token_id,
                           e1_sentence, e2_token,
                           e2_token_id, e2_sentence):

        #Since intersentential paths are allowed, the next sentence is 
        #also included
        df = self.deps[(self.deps['filename'] == filename) &
                        ((self.deps['sentence'] == int(e1_sentence)) |
                        (self.deps['sentence'] == int(e1_sentence)+1))]

        path = self.recursive_search(df, '', e2_token, e2_token_id,
                        e2_sentence, e1_token, e1_token_id,
                        e1_sentence)

        if path is not '':
            return path 
        else:
            #Try finding path from e2 to e1
            return self.recursive_search(df, '', e1_token, 
                            e1_token_id, int(e1_sentence), 
                            e2_token, e2_token_id, 
                            int(e2_sentence))

    def parseFile(self, filename):

        f = open(filename)
        soup = BeautifulSoup(f.read())
        events = soup.findAll('event')
        tokens = soup.findAll('token')
        
        for i in range(0,len(events)-1):

            event = events[i]

            for j in range(i+1, len(events)):

                next_event = events[j]

                event_token_id         = event.find('token_anchor').attrs['id']
                next_event_token_id = next_event.find('token_anchor').attrs['id']

                event_token_tag      =    soup.find(lambda tag: (tag.name) == 'token' and
                                                        (tag.attrs['id']) == (event_token_id))

                next_event_token_tag =     soup.find(lambda tag: (tag.name) == 'token' and
                                                        (tag.attrs['id']) == (next_event_token_id))



                event_sentence = event_token_tag['sentence']
                next_event_sentence = next_event_token_tag['sentence']

                if (int(next_event_sentence) - int(event_sentence)) > 1:
                    
                    break # For now, intersentential event pairs can only be one sentence apart 

                else:
                    
                    
                    e1_number       = event_token_tag.attrs['number']
                    e1_sentence     = event_sentence
                    e1_token        = event_token_tag.text
                    e1_aspect       = event.attrs['aspect']
                    e1_certainty    = event.attrs['certainty']
                    e1_class        = event.attrs['class']
                    e1_comment      = event.attrs['comment']
                    e1_factuality   = event.attrs['factuality']
                    e1_event_id     = event.attrs['id']
                    e1_modality     = event.attrs['modality']
                    e1_polarity     = event.attrs['polarity']
                    e1_pos          = event.attrs['pos']
                    e1_tense        = event.attrs['tense']

                    e2_number       = next_event_token_tag.attrs['number']
                    e2_sentence     = event_sentence
                    e2_token        = next_event_token_tag.text
                    e2_aspect       = next_event.attrs['aspect']
                    e2_certainty    = next_event.attrs['certainty']
                    e2_class        = next_event.attrs['class']
                    e2_comment      = next_event.attrs['comment']
                    e2_factuality   = next_event.attrs['factuality']
                    e2_event_id     = next_event.attrs['id']
                    e2_modality     = next_event.attrs['modality']
                    e2_polarity     = next_event.attrs['polarity']
                    e2_pos          = next_event.attrs['pos']
                    e2_tense        = next_event.attrs['tense']
                    
                    causal_relation_exists = len(soup.findAll(lambda tag: 
                                                tag.name == 'source' and 
                                                tag.findParent().name == 'clink' and 
                                                tag.findNextSibling().name == 'target' and

                                                ((tag.attrs['id'] == e1_event_id and 
                                                    tag.findNextSibling().attrs['id'] == e2_event_id) 
                                                or 
                                                (tag.attrs['id'] == e2_event_id and 
                                                    tag.findNextSibling().attrs['id'] == e1_event_id))  )) > 0

                    e1_token_id_offset = soup.find(
                                        lambda tag: tag.name == 'token' and
                                                    tag.attrs['sentence'] == e1_sentence).attrs['id']

                    if e1_sentence == e2_sentence:
                        e2_token_id_offset = e1_token_id_offset
                    else:
                        e2_token_id_offset = soup.find(
                                        lambda tag: tag.name == 'token' and
                                                    tag.attrs['sentence'] == e2_sentence).attrs['id']

                    e1_token_id = int(event_token_tag.attrs['id']) - int(e1_token_id_offset) + 1
                    e2_token_id = int(next_event_token_tag.attrs['id']) - int(e2_token_id_offset) + 1

                    e1_event_id = int(e1_event_id)
                    e2_event_id = int(e2_event_id)

                    same_pos_tag = e1_pos == e2_pos

                    sentence_distance = int(e2_sentence) - int(e1_sentence)

                    event_distance = e2_event_id - e1_event_id + 1

                    same_polarity = e1_polarity == e2_polarity

                    same_aspect = e1_aspect == e2_aspect

                    same_tense = e1_tense == e2_tense

                    same_class = e1_class == e2_class


                    ''' 
                    TODO: The conditions between e1_event_id and e2_event_id maybe don't 
                    make sense because e1_event_id would always be greater than e2_event_id.
                    Reverse causal relations are identified only if e2 is specifed as 
                    source in clink and e1 as target
                    '''
                    csignals_in_bw = soup.findAll(lambda tag: tag.name == 'c-signal' and 
                                            ((  (e1_event_id < e2_event_id) and 
                                                (int(tag.attrs['id']) > e1_event_id) and 
                                                (int(tag.attrs['id']) < e2_event_id)) or 
                                            (e1_event_id > e2_event_id and
                                                int(tag.attrs['id']) > e2_event_id and
                                                int(tag.attrs['id']) < e1_event_id)))

                    csignal_position = csignal = '' 

                    if len(csignals_in_bw) == 0:
                        csignal_tag = event.findPreviousSibling(lambda tag: tag.name == 'c-signal')
                        
                        if csignal_tag is not None:
                            
                            csignal_token_id = csignal_tag.find('token_anchor').attrs['id']
                            
                            csignal_token_tag = soup.find(lambda x: 
                                    x.name == 'token' and x.attrs['id'] == csignal_token_id)

                            if csignal_token_tag.attrs['sentence'] == e1_sentence:
                                
                                csignal = soup.find(lambda x: 
                                    x.name == 'token' and x.attrs['id'] == csignal_token_id).text

                                csignal_position = 'before'
                        
                    else:
                        csignal_token_id = csignals_in_bw[-1].find('token_anchor').attrs['id']
                        csignal = soup.find(lambda x: x.name == 'token' and x.attrs['id'] == csignal_token_id).text
                        csignal_position = 'between'
                    
                    tlink_exists = len(soup.findAll(lambda tag: 
                            tag.name == 'tlink' 
                            and (
                            ((tag.find('source').attrs['id'] == str(e1_event_id)) and
                            (tag.find('target').attrs['id'] == str(e2_event_id))) 
                            or 
                            ((tag.find('source').attrs['id'] == str(e2_event_id)) and
                            (tag.find('target').attrs['id'] == str(e1_event_id))) )
                        )) > 0

                    filename = filename.split('.xml')[0]
                    filename = filename.split('/')
                    filename = filename[len(filename) - 1]

                    dep_path = self.get_dependency_path(
                        filename, e1_token, e1_token_id, e1_sentence,
                        e2_token, e2_token_id, e2_sentence)

                    e1_is_sent_root = len(self.deps[
                                            (self.deps['governor'] == 'ROOT') &
                                            (self.deps['dependent'] == e1_token) &
                                            (self.deps['dependent_idx'] == int(e1_token_id)) &
                                            (self.deps['sentence'] == int(e1_sentence))] ) > 0

                    e2_is_sent_root = len(self.deps[
                                            (self.deps['governor'] == 'ROOT') &
                                            (self.deps['dependent'] == e2_token) &
                                            (self.deps['dependent_idx'] == int(e2_token_id)) &
                                            (self.deps['sentence'] == int(e2_sentence))] ) > 0

                    row = [
                        e1_token_id, 
                        e1_number,
                        e1_sentence,
                        e1_token,
                        e1_aspect, 
                        e1_class,
                        e1_event_id,
                        e1_modality,
                        e1_polarity,
                        e1_pos,
                        e1_tense,
                        e2_token_id, 
                        e2_number,
                        e2_sentence,
                        e2_token,
                        e2_aspect, 
                        e2_class,
                        e2_event_id,
                        e2_modality,
                        e2_polarity,
                        e2_pos,
                        e2_tense,
                        dep_path, 
                        same_pos_tag,
                        sentence_distance,
                        event_distance,
                        same_polarity,
                        same_aspect,
                        same_tense,
                        same_class,
                        csignal,
                        csignal_position,
                        tlink_exists,
                        e1_is_sent_root,
                        e2_is_sent_root,
                        causal_relation_exists  ]


                    self.data.append(row)

        f.close()

    def extract_features(self):

        for folder, subs, files in os.walk('data/xml'):
            
            for filename in files:
                
                try:
                    
                    if ('.xml' in filename) and (filename[0] != '.'):
                        
                        print 'Parsing File: '+filename
                        
                        self.parseFile(os.path.join(folder, filename))

                except Exception as e:
                    traceback.print_exc()
                    continue

        self.data = pd.DataFrame(self.data)

        self.data.columns = self.FEATURE_NAMES

    def save_to_csv(filename):
        self.data.to_csv(filename)

if __name__ == "__main__":
    extractor = FeaturesExtractor()
    extractor.extract_features()
    extractor.save_to_csv('features.csv')


