
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.cross_validation import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_moons, make_circles, make_classification
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.naive_bayes import GaussianNB
from sklearn.lda import LDA
from sklearn.qda import QDA
from scipy.sparse.csr import csr_matrix
from scipy.sparse import vstack
from sklearn import cross_validation
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
import json



import pandas as pd

class Classifier:

    def __init__(self):

        self.features_df = None

        self.data = pd.read_csv('features.csv', header=0, index_col=0)

        self.y = self.data['causal_relation_exists']

        del self.data['causal_relation_exists']

    def get_dep_features(self):
        dep_features = self.encode_dependency_path(self.data[22])

        dep_features.columns = ['dep_'+col for col in dep_features.columns]

        self.data = pd.concat([self.data, dep_features], axis=1)

        del self.data[22]

    def encode_dependency_path(self, dep_paths):

        self.dep_vectorizer = CountVectorizer()
        self.dep_features = self.dep_vectorizer.fit_transform(dep_paths)

        dep_features = pd.DataFrame([ pd.Series(self.dep_features[i].toarray().ravel()) 
                              for i in range(self.dep_features.shape[0]) ])

        return dep_features

    def encode_features(self):

        encoders = {
            # 'e1_token_id', 
         #    'e1_number',
         #    'e1_sentence',
            'e1_token':         [LabelEncoder(), OneHotEncoder()],
            'e1_aspect':        [LabelEncoder(), OneHotEncoder()], 
            'e1_class':            [LabelEncoder(), OneHotEncoder()], 
            # 'e1_event_id',
            'e1_modality':        [LabelEncoder(), OneHotEncoder()], 
            'e1_polarity':        [LabelEncoder()], 
            'e1_pos':            [LabelEncoder(), OneHotEncoder()], 
            'e1_tense':            [LabelEncoder(), OneHotEncoder()], 
            # 'e2_token_id', 
            # 'e2_number',
            # 'e2_sentence',
            'e2_token':         [LabelEncoder(), OneHotEncoder()],
            'e2_aspect':        [LabelEncoder(), OneHotEncoder()], 
            'e2_class':            [LabelEncoder(), OneHotEncoder()], 
            # 'e2_event_id',
            'e2_modality':        [LabelEncoder(), OneHotEncoder()], 
            'e2_polarity':        [LabelEncoder()], 
            'e2_pos':            [LabelEncoder(), OneHotEncoder()], 
            'e2_tense':            [LabelEncoder(), OneHotEncoder()], 
            'dep_path':            [CountVectorizer()],
            'same_pos_tag':        [LabelEncoder()],
            'sentence_distance':    [],    
            'event_distance':     [],
            'same_polarity':    [LabelEncoder()], 
            'same_aspect':        [LabelEncoder()], 
            'same_tense':        [LabelEncoder()], 
            'same_class':        [LabelEncoder()], 
            'csignals_in_bw':    [LabelEncoder(), OneHotEncoder()],
            'csignal_position': [LabelEncoder(), OneHotEncoder()],
            'tlink_exists':        [LabelEncoder()],
            'e1_is_sent_root':     [LabelEncoder()],
            'e2_is_sent_root':     [LabelEncoder()]
        }

        features = []

        self.features_df = []

        for feature, feature_encoders in encoders.iteritems():

            # print feature

            transformed = self.data[feature].fillna('')

            for encoder in feature_encoders:

                # print encoder

                transformed = encoder.fit_transform(transformed)

                if type(encoder) == CountVectorizer:
                    transformed = transformed.transpose()
                break
            # if type(transformed) == csr_matrix:
            #     enc_features_df = pd.DataFrame([ pd.Series(transformed[i].toarray().ravel())
            #                           for i in range(transformed.shape[0]) ])                
            # else:
            #     enc_features_df = pd.DataFrame(transformed)



            self.features_df = vstack((self.features_df, transformed), format='csr')

        self.features_df = self.features_df.transpose()
        # for col in df.columns:
        #     le = LabelEncoder().fit(df[col])
        #     df[col] = le.transform(df[col])
        #     encoders[col] = le

    def encode_features_using_dict_vectorizer(self):

        self.data = self.data.fillna('')
        json_content = self.data.to_json(orient='records')
        data = json.loads(json_content)
        vec = DictVectorizer()
        self.features_df = vec.fit_transform(data)

    def classify(self):

        num_rows = self.features_df.shape[0]

    
        # train_x = self.features_df[np.random.permutation(num_rows)[:-5000]]
        # train_y = self.y[np.random.permutation(num_rows)[:-5000]]

        # test_x = self.features_df[np.random.permutation(num_rows)[-5000:]]
        # test_y = self.y[np.random.permutation(num_rows)[-5000:]]

        train_x = self.features_df[:18000]
        train_y = self.y[:18000]

        test_x = self.features_df[18000:]
        test_y = self.y[18000:]


        # clf = SVC()
        # clf.fit(train_x, train_y) 

        names = [
            "Nearest Neighbors", 
            # "Linear SVM", 
            # "RBF SVM", 
            "Decision Tree",
            "Random Forest", 
            # "AdaBoost", 
            # "Naive Bayes", 
            # "LDA", 
            # "QDA"
        ]

        self.classifiers = [
            KNeighborsClassifier(2),
            # SVC(kernel="linear", C=0.025),
            # SVC(gamma=2, C=1),
            DecisionTreeClassifier(),#max_depth=5
            RandomForestClassifier(),#max_depth=5, n_estimators=10, max_features=1
            # AdaBoostClassifier(),
            # GaussianNB(),
            # LDA(),
            # QDA()
        ]

        for name, clf in zip(names, self.classifiers):

            clf = clf.fit(train_x, train_y)
            predictions = clf.predict(test_x)

            print "Classifier: "+name.upper()

            print "Total number of causal relations predicted: "+str(sum(predictions == 1))

            print "Causal Relations predicted correctly: "+str(sum((predictions == 1) & (test_y == 1)))+" out of "+str(sum(test_y == 1))

            print "------------------------------"


if __name__ == "__main__":
    clf = Classifier()
    clf.encode_features_using_dict_vectorizer()
    # clf.encode_features()
    clf.classify()
