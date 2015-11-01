
from bs4 import BeautifulSoup
import os
import pandas as pd
import sys
import traceback
from sklearn.feature_extraction.text import CountVectorizer

class OutWriter:

    def __init__(self):

        self.HTML_ANNOTATION_COLORS = ['yellow', 'silver', 'lightblue', 'cyan', 'gray', 'orange', 
            'red', 'green','pink', 'brown']

        self.OUT_PATH = "out/"

        self.HEADER = "<style>\
                    table, td, th {\
                        border: 1px solid white;\
                }</style>"

        self.FOOTER = ""

    def _make_doc_name_link(self, name):
        name = name.split('/')[-1].replace(".","_")
        name = "<a href='"+name+".html'>"+name+"</a>"
        return name

    def index_page(self, df):
            
        docs = df[['doc_name', 'date']].drop_duplicates().sort(['doc_name'], ascending=False).reset_index(drop=True)
        docs['doc_name'] = docs['doc_name'].apply(self._make_doc_name_link)

        out_html = self.HEADER+docs.to_html(escape=False)+self.FOOTER
        with open(self.OUT_PATH+'index.html', 'w') as f:
            f.write(out_html)

    def save_html_output(self, doc_name, soup, causations_in_doc):

        tokens = soup.findAll('token')

        token_arr = [token.text for token in tokens]

        color_idx = 0

        for idx, row in causations_in_doc.iterrows():

            c_idx = int(row['c_token_id'])-1
            e_idx = int(row['e_token_id'])-1
            token_arr[c_idx] = "<span style='background:"+self.HTML_ANNOTATION_COLORS[color_idx]+"'>"+str(token_arr[c_idx])+"</span>"
            token_arr[e_idx] = "<span style='background:"+self.HTML_ANNOTATION_COLORS[color_idx]+"'>"+str(token_arr[e_idx])+"</span>"
            color_idx = color_idx + 1

        text = ' '.join(token_arr)

        html_content = self.HEADER +"<p>"+text+"</p>"

        if len(causations_in_doc) > 0:

            html_content = html_content + "<h3>Causal Relations \
                with events defined as verb or nouns (Mirza's work):</h3>"

            causations_in_doc['relation'] = "caused"
            
            html_content = html_content + \
                causations_in_doc[['c_lemma', 'relation', 'e_lemma']].rename(columns={'c_lemma':'event 1', 'e_lemma':'event 2'}).to_html()

            html_content = html_content + "<h3>Cause and effect redefined as event,subject pairs</h3>"

            causations_in_doc['cause_with_subj'] = causations_in_doc.apply(lambda x: "( %s , %s )" %(x["cause"], x["c_subj"]), axis=1)

            causations_in_doc['cause (event,subj)'] = causations_in_doc.apply(lambda x: "( "+x["c_lemma"]+", "+x["c_subj"]+" )", axis=1)
            causations_in_doc['effect (event, subj)'] = causations_in_doc.apply(lambda x: "( "+x["e_lemma"]+", "+x["e_subj"]+" )", axis=1)
            html_content = html_content + causations_in_doc[['cause (event,subj)', 'relation', 'effect (event, subj)']].to_html()


        html_content = html_content+self.FOOTER

        doc_name = doc_name.split('/')[-1]

        doc_name = doc_name.replace(".", "_")
        f = open("out/"+doc_name+".html", "w")
        f.write(html_content)
        f.close()

    def write_linkages(self, linkages):

        for folder, subs, files in os.walk('out/'):
                
            for filename in files:

                    if 'index' in filename:
                        print 'index found'
                        continue
                    
                    with open(os.path.join(folder, filename), 'a') as f:

                        doc_name = "data/xml/"+filename.replace("_xml", ".xml")
                        doc_name = doc_name.replace(".html", "")

                        print doc_name

                        f.write("<h3>Incoming edges (causes in this document found as effects in older documents)</h3>")

                        doc_links = linkages[linkages['doc_name_x'] == doc_name]

                        if len(doc_links) == 0:
                            f.write("None found")
                        else:
                            doc_links['common_event'] = doc_links.apply(lambda x: "(%s, %s)" %(x['cause_x'], x['c_subj_x']), axis=1)
                            doc_links['time_difference'] = doc_links.apply(lambda x: x['date_x'] - x['date_y'], axis=1)
                            doc_links['doc_name_y'] = doc_links['doc_name_y'].apply(self._make_doc_name_link)
                            f.write(doc_links[['doc_name_y', 'time_difference', 'common_event']].to_html(escape=False))


                        f.write("<h3>Outgoing edges (effects in this document found as causes in more recent documents)</h3>")

                        doc_links = linkages[linkages['doc_name_y'] == doc_name]

                        if len(doc_links) == 0:
                            f.write("None found")
                        else:
                            doc_links['common_event'] = doc_links.apply(lambda x: "(%s, %s)" %(x['effect_y'], x['e_subj_y']), axis=1)
                            doc_links['time_difference'] = doc_links.apply(lambda x: x['date_x'] - x['date_y'], axis=1)
                            doc_links['doc_name_x'] = doc_links['doc_name_x'].apply(self._make_doc_name_link)
                            f.write(doc_links[['doc_name_x', 'time_difference', 'common_event']].to_html(escape=False))






class Parser:

    def __init__(self):

        COLUMN_NAMES = ['cause', 'c_lemma','cause_pos', 'c_token_id', 'c_subj', 'c_subj_token_id', 'c_pos_deps', 
        'effect', 'e_lemma', 'effect_pos', 'e_token_id', 'e_subj','e_subj_token_id', 'e_pos_deps', 'date', 'doc_name']

        self.causal_df = pd.DataFrame(columns=COLUMN_NAMES)

        self.outWriter = OutWriter()

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

        ## Dependencies ##
        file_prefix = (filename.split('/')[-1]).split(".xml")[0]
        
        deps = pd.read_csv('data/deps/'+file_prefix+".deps", sep='\t', header=-1,
            names=['idx', 'token', 'lemma', 'pos', 'ner', 'head_idx', 'relation'])

        deps['token_id'] = deps.index + 1
        deps['sentence_no'] = (deps['idx'] == 1).cumsum()
        deps['pos_trimmed'] = deps['pos'].apply(lambda x: x[:2])

        for i, clink in enumerate(clinks):

            cause_event_id  = clink.find('source').attrs['id']
            effect_event_id = clink.find('target').attrs['id']

            cause_event_tag = soup.find(lambda x: (x.name == 'event') and 
                (x.attrs['id'] == cause_event_id))

            cause_pos = cause_event_tag.attrs['pos']

            effect_event_tag = soup.find(lambda x: (x.name == 'event') and 
                (x.attrs['id'] == effect_event_id))

            effect_pos = effect_event_tag.attrs['pos']

            cause_token_id = cause_event_tag.find('token_anchor').attrs['id']

            effect_token_id = effect_event_tag.find('token_anchor').attrs['id']

            cause_token_tag = soup.find(lambda x: (x.name == 'token') and 
                (x.attrs['id'] == str(cause_token_id)))

            cause_sentence = cause_token_tag.attrs['sentence']

            cause_token = cause_token_tag.text

            all_cause_tokens = soup.findAll(lambda x: (x.text == cause_token) & (x.name == 'token'))

            c_tokens_arr = [c_token.attrs['id'] for c_token in all_cause_tokens]

            c_occurence = c_tokens_arr.index(cause_token_id)

            effect_token_tag = soup.find(lambda x: (x.name == 'token') and 
                (x.attrs['id'] == str(effect_token_id)))

            effect_sentence = effect_token_tag.attrs['sentence']

            effect_token = effect_token_tag.text

            all_effect_tokens = soup.findAll(lambda x: (x.text == effect_token) & (x.name == 'token'))

            e_tokens_arr = [e_token.attrs['id'] for e_token in all_effect_tokens]

            e_occurence = e_tokens_arr.index(effect_token_id)

            c_dep = deps[deps['token'] == cause_token].iloc[c_occurence]
            e_dep = deps[deps['token'] == effect_token].iloc[e_occurence]

            c_pos_from_deps = c_dep['pos']
            e_pos_from_deps = e_dep['pos']

            c_lemma = c_dep['lemma']
            e_lemma = e_dep['lemma']

            print cause_token+" -> "+effect_token

            resp = self.get_cause_effect_subjects(deps, cause_token, c_occurence, cause_sentence, cause_token_id,
                effect_token, e_occurence, effect_sentence, effect_token_id)

            self.causal_df.loc[len(self.causal_df)] = [cause_token, c_lemma, cause_pos, cause_token_id, resp['c_subj'],
                resp['c_subj_token_id'], c_pos_from_deps, effect_token, e_lemma, effect_pos, effect_token_id, resp['e_subj'], 
                resp['e_subj_token_id'], e_pos_from_deps, date_val, filename]
        
            
        self.outWriter.save_html_output(filename, soup, self.causal_df[self.causal_df['doc_name'] == filename])

        f.close()

  

    def populate_causal_df(self):

        for folder, subs, files in os.walk('data/xml'):
            
            for filename in files:
                
                try:
                    
                    if ('.xml' in filename) and (filename[0] != '.'):
                        
                        print '\n'+'Parsing File: '+filename+'\n'
                        
                        if 'wsj' in filename:

                            self.parseFile(os.path.join(folder, filename))

                except Exception as e:
                    traceback.print_exc()
                    continue
                    # break

        self.causal_df.to_csv('causal_df.csv')

    def get_cause_effect_subjects(self, deps, c_token, c_occurence, c_sentence, c_token_id, e_token, e_occurence,
            e_sentence, e_token_id):

        return_dict = {'e_subj':'', 'c_subj':'', 'e_subj_token_id':-1, 'c_subj_token_id':-1}
        
        # c_row = deps[deps['token_id'] == int(c_token_id)].iloc[0]
        # c_rows = deps[(deps['token'] == c_token) & (deps['sentence_no'] == (int(c_sentence)+1))]

        c_rows = deps[deps['token'] == c_token]

        if len(c_rows) > c_occurence:

            c_row = c_rows.iloc[c_occurence]

            c_deps = self.recursive_trace(deps[(deps['sentence_no'] == c_row['sentence_no'])], c_row['idx'], "pos_trimmed", "NN") # , "relation", "nsubj"

            if c_deps is not None:
                return_dict['c_subj'] = c_deps.iloc[0]['token']
                return_dict['c_subj_token_id'] = c_deps.iloc[0]['token_id']

        else:

            print 'No Causal Rows found'

        e_rows = deps[deps['token'] == e_token]

        if len(e_rows) > e_occurence:

            e_row = e_rows.iloc[e_occurence]

            e_deps = self.recursive_trace(deps[(deps['sentence_no'] == e_row['sentence_no'])], e_row['idx'],"pos_trimmed", "NN") #  "relation", "nsubj"

            if e_deps is not None:
                return_dict['e_subj'] = e_deps.iloc[0]['token']
                return_dict['e_subj_token_id'] = e_deps.iloc[0]['token_id']

        else:

            print 'No Effect Rows found'

        return return_dict
            
    def visualize_dependency_tree(df, sentenceNumber):
        df = df[(df['sentence_no'] == sentenceNumber)]

        print '\nSentence:'+(' '.join(list(df['token'])))+'\n'

        root = df[df['relation'] == 'ROOT'].iloc[0]

        print root.token+' ('+root.pos+', '+root.relation+')\n'

        _recursive_parse(df, root.idx, 1)

    def _recursive_parse(df, head_idx, depth):

        step_str = '    '

        deps = df[df['head_idx'] == head_idx]

        for i in range(len(deps)):

            dep = deps.iloc[i]
            print (step_str*depth)+dep.token+' ('+dep.pos+', '+dep.relation+')\n'

            _recursive_parse(df, dep.idx, depth+1)

    def trace_dependency_path(df, dep_path, start_col, start_val, end_col, end_val):

        recursive_trace(df[df[start_col] == start_val], dep_path, end_col, end_val)

    def recursive_trace(self, df, current_idx, end_col, end_val):

        deps_current_head = df[df['head_idx'] == current_idx]

        print len(deps_current_head)

        df_search = deps_current_head[deps_current_head[end_col] == end_val]

        if len(df_search) == 0:

            for idx, row in deps_current_head.iterrows():

                print row['idx']

                return self.recursive_trace(
                    df,
                    row['idx'],
                    end_col,
                    end_val)

        else:
            return df_search

    def identify_inter_doc_linkages(self):

        self.causal_df['date'] = pd.to_datetime(self.causal_df['date'])

        self.linkages = pd.merge(self.causal_df, self.causal_df, left_on=['c_lemma', 'c_subj'], right_on=['e_lemma', 'e_subj'])
        self.linkages = self.linkages[(self.linkages['date_x'] >= self.linkages['date_y'])]
        self.linkages[['cause_y', 'c_subj_y', 'effect_y', 'e_subj_y', 'date_y', 'doc_name_y', 'cause_x', 'c_subj_x', 'effect_x', 'e_subj_x', 'date_x', 'doc_name_x']]

        self.outWriter.write_linkages(self.linkages)

        return self.linkages

    def create_index_page(self):
        self.outWriter.index_page(self.causal_df)
        

if __name__ == "__main__":
    parser = Parser()
    parser.populate_causal_df()
    chains = parser.identify_inter_doc_linkages()
    parser.create_index_page()
    


