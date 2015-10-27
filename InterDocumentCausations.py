
from bs4 import BeautifulSoup
import os
import pandas as pd
import sys
import traceback
from sklearn.feature_extraction.text import CountVectorizer

class Parser:

    def __init__(self):

        COLUMN_NAMES = ['cause', 'c_token_id', 'effect','e_token_id', 'date', 'doc_name']

        self.causal_df = pd.DataFrame(columns=COLUMN_NAMES)

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
        clinks = soup.findAll('clink')

        date_tag = soup.find(lambda x: (x.name == 'timex3') and 
            (x.attrs['functionindocument'] == 'CREATION_TIME'))

        date_val = date_tag.attrs['value']

        for i, clink in enumerate(clinks):

            cause_event_id  = clink.find('source').attrs['id']
            effect_event_id = clink.find('target').attrs['id']

            cause_event_tag = soup.find(lambda x: (x.name == 'event') and 
                (x.attrs['id'] == cause_event_id))

            effect_event_tag = soup.find(lambda x: (x.name == 'event') and 
                (x.attrs['id'] == effect_event_id))

            cause_token_id = cause_event_tag.find('token_anchor').attrs['id']

            effect_token_id = effect_event_tag.find('token_anchor').attrs['id']

            print cause_token_id

            cause_token = soup.find(lambda x: (x.name == 'token') and 
                (x.attrs['id'] == str(cause_token_id)))

            cause_token = cause_token.text

            effect_token = soup.find(lambda x: (x.name == 'token') and 
                (x.attrs['id'] == str(effect_token_id))).text

            self.causal_df.loc[len(self.causal_df)] = [cause_token, cause_token_id,
                effect_token, effect_token_id, date_val, filename]
        
            
        self.save_as_html(filename, soup)

        f.close()

    def save_as_html(self, doc_name, soup):

        colors_arr = ['yellow', 'silver', 'lightblue', 'cyan', 'gray', 'orange', 'red']

        causations_in_doc = self.causal_df[self.causal_df['doc_name'] == doc_name]

        tokens = soup.findAll('token')

        token_arr = [token.text for token in tokens]

        color_idx = 0

        for idx, row in causations_in_doc.iterrows():

            c_idx = int(row['c_token_id'])-1
            e_idx = int(row['e_token_id'])-1
            token_arr[c_idx] = "<span style='background:"+colors_arr[color_idx]+"'>"+str(token_arr[c_idx])+"</span>"
            token_arr[e_idx] = "<span style='background:"+colors_arr[color_idx]+"'>"+str(token_arr[e_idx])+"</span>"
            color_idx = color_idx + 1

        text = ' '.join(token_arr)

        html_content = "<html><body><p>"+text+"</p></body></html>"

        doc_name = doc_name.split('/')[-1]

        doc_name = doc_name.replace(".", "_")
        f = open("data/html/"+doc_name+".html", "w")
        f.write(html_content)
        f.close()

    def populate_causal_df(self):

        for folder, subs, files in os.walk('data/xml'):
            
            for filename in files:
                
                try:
                    
                    if ('.xml' in filename) and (filename[0] != '.'):
                        
                        print 'Parsing File: '+filename
                        
                        self.parseFile(os.path.join(folder, filename))

                except Exception as e:
                    traceback.print_exc()
                    continue
                    # break

        self.causal_df.to_csv('causal_df.csv')

    def causal_chain(self):

        self.causal_df['date'] = pd.to_datetime(self.causal_df['date'])

        merged = pd.merge(self.causal_df, self.causal_df, left_on='cause', right_on='effect')
        merged = merged[merged['date_x'] >= merged['date_y']]
        merged[['cause_y', 'effect_y', 'date_y', 'doc_name_y', 'cause_x', 'effect_x', 'date_x', 'doc_name_x']]

    def save_to_csv(filename):
        self.data.to_csv(filename)

if __name__ == "__main__":
    parser = Parser()
    parser.populate_causal_df()
    


