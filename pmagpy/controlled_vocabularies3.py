#!/usr/bin/env python
import pandas as pd
from pandas import Series, DataFrame
import urllib2
import httplib
import json
import os
import backup_vocabulary as backup
# get list of controlled vocabularies form this part of the api:
#'http://api.earthref.org/MagIC/vocabularies.json'
# then, use that list to determine whether or not any given column has a controlled vocabulary list
import check_updates
from pmagpy import data_model3
pmag_dir = check_updates.get_pmag_dir()
data_model_dir = os.path.join(pmag_dir, 'pmagpy', 'data_model')
# if using with py2app, the directory structure is flat,
# so check to see where the resource actually is
if not os.path.exists(data_model_dir):
    data_model_dir = os.path.join(pmag_dir, 'data_model')

class Vocabulary(object):

    def __init__(self):
        self.vocabularies = []
        self.possible_vocabularies = []
        self.all_codes = []
        self.code_types = []
        self.methods = []
        self.age_methods = []

    def get_meth_codes(self):
        """
        Get method codes from the MagIC API
        """
        try:
            #old_raw_codes = pd.io.json.read_json('https://api.earthref.org/MagIC/method_codes.json')
            raw_codes = pd.io.json.read_json(os.path.join(pmag_dir, "3_0", "method_codes.json"))
        except urllib2.URLError:
            return [], []
        except httplib.BadStatusLine:
            return [], []
        code_types = raw_codes.ix['label']
        all_codes = []
        for code_name in code_types.index:
            #code_url = 'https://api.earthref.org/MagIC/method_codes/{}.json'.format(code_name)
            # if internet fails in the middle, cut out
            try:
                #raw_df = pd.io.json.read_json(raw_codes[code_name]['codes'])
                df = pd.DataFrame(raw_codes[code_name]['codes'])
            except urllib2.URLError:
                return [], []
            except httplib.BadStatusLine:
                return [], []
            # remake the dataframe with the code (i.e., 'SM_VAR') as the index
            df.index = df['code']
            del df['code']
            # add a column with the code type (i.e., 'anisotropy_estimation')
            df['dtype'] = code_name

            little_series = df['definition']
            big_series = Series()
            if any(all_codes):
                all_codes = pd.concat([all_codes, df])
                big_series = pd.concat([big_series, little_series])
            else:
                all_codes = df
                big_series = little_series

        # format code_types and age column
        code_types = raw_codes.T
        code_types['age'] = False
        age = ['geochronology_method']
        code_types.ix[age, 'age'] = True
        code_types['other'] = ~code_types['age']
        return all_codes, code_types

    def get_one_meth_type(self, mtype, method_list):
        """
        Get all codes of one type (i.e., 'anisotropy_estimation')
        """
        cond = method_list['dtype'] == mtype
        codes = method_list[cond]
        return codes

    def get_one_meth_category(self, category, all_codes, code_types):
        """
        Get all codes in one category (i.e., all age codes).
        This can include multiple method types (i.e., 'anisotropy_estimation', 'sample_prepartion', etc.)
        """
        categories = Series(code_types[code_types[category] == True].index)
        cond = all_codes['dtype'].isin(categories)
        codes = all_codes[cond]
        return codes

    def get_tiered_meth_category(self, mtype, all_codes, code_types):
        """
        Get a tiered list of all er/pmag_age codes
        i.e. pmag_codes = {'anisotropy_codes': ['code1', 'code2'], 
        'sample_preparation': [code1, code2], ...}
        """
        #cond = code_types[code_types[mtype] == True]
        categories = Series(code_types[code_types[mtype] == True].index)
        codes = {cat: list(self.get_one_meth_type(cat, all_codes).index) for cat in categories}
        return codes

    default_vocab_types = ('lithologies', 'geologic_classes', 'geologic_types', 'location_types',
                           'age_unit')

    def get_controlled_vocabularies(self, vocab_types=default_vocab_types):
        """
        Get all non-method controlled vocabularies
        """
        connected = True
        try:
            controlled_vocabularies = []
            print '-I- Importing controlled vocabularies from https://earthref.org'
            #url = 'https://api.earthref.org/MagIC/vocabularies.json'
            url = os.path.join(pmag_dir, "3_0", "controlled_vocabularies.json")
            data = pd.io.json.read_json(url)
            possible_vocabularies = data.columns
            ## this line means, grab every single controlled vocabulary
            vocab_types = list(possible_vocabularies)

            def get_cv_from_list(lst):
                """
                Check a validations list from the data model.
                If there is a controlled vocabulary validation,
                return which category of controlled vocabulary it is.
                This will generally be applied to the validations col 
                of the data model
                """
                try:
                    for i in lst:
                        if "cv(" in i:
                            return i[4:-2]
                except TypeError:
                    return None
                else:
                    return None

            vocab_col_names = []
            data_model = data_model3.DataModel()
            for dm_key in data_model.dm:
                df = data_model.dm[dm_key]
                df['vocab_name'] = df['validations'].apply(get_cv_from_list)
                lst = zip(df[df['vocab_name'].notnull()]['vocab_name'], df[df['vocab_name'].notnull()].index)
                # in lst, first value is the name of the controlled vocabulary
                # second value is the name of the dataframe column
                vocab_col_names.extend(lst)

            # vocab_col_names is now a list of tuples
            # consisting of the vocabulary name and the column name
            # i.e., (u'type', u'geologic_types')
                
            # remove duplicate col_names:
            vocab_col_names = sorted(set(vocab_col_names))
            # add in boolean category to controlled vocabularies
            bool_items = [{'item': True}, {'item': False}, {'item': 'true'},
                          {'item': 'false'}, {'item': 0}, {'item': 1}]
            series = Series({'label': 'Boolean', 'items': bool_items})
            data['boolean'] = series
            # use vocabulary name to get possible values for the column name
            for vocab in vocab_col_names[:]:
                items = data[vocab[0]]['items']
                stripped_list = [item['item'] for item in items]
                controlled_vocabularies.append(stripped_list)
            # create series with the column name as the index, and the possible values as the values
            vocabularies = pd.Series(controlled_vocabularies, index=[i[1] for i in vocab_col_names])
            return vocabularies, vocabularies
        except urllib2.URLError:
            connected = False
        except httplib.BadStatusLine:
            connected = False
        if not connected:
            print "-W- Could not connect to internet -- will not be able to provide all controlled vocabularies"
            vocabularies = pd.Series([backup.site_lithology, backup.site_class, backup.site_type,
                                      backup.location_type, backup.age_unit, backup.site_definition], index=vocab_types)
            possible_vocabularies = []
        return vocabularies, possible_vocabularies


    #def get_all_possible_vocabularies(possible_list):

    def get_tiered_meth_category_offline(self):
        path = os.path.join(data_model_dir, 'er_methods.txt')
        dfile = open(path)
        json_data = json.load(dfile)
        dfile.close()
        return json_data


    def get_all_vocabulary(self):
        all_codes, code_types = self.get_meth_codes()
        
        ## do it this way if you want a non-nested list of all codes
        ## i.e. er_codes = [code1, code2,...]
        ##def get_one_meth_category(category, all_codes, code_types):

        ## do it this way if you want a tiered list of all codes
        ## i.e. er_codes = {'anisotropy_codes': ['code1', 'code2'], ...}
        ##def get_tiered_meth_category(mtype, all_codes, code_types):

        if any(all_codes):
            methods = self.get_tiered_meth_category('other', all_codes, code_types)
            age_methods = self.get_tiered_meth_category('age', all_codes, code_types)
        else:
            methods = self.get_tiered_meth_category_offline()
            age_methods = self.get_tiered_meth_category_offline()
            path = os.path.join(data_model_dir, 'code_types.txt')
            with open(path, 'r') as type_file:
                raw_code_types = json.load(type_file)
            code_types = pd.read_json(raw_code_types)
            path = os.path.join(data_model_dir, 'all_codes.txt')
            with open(path, 'r') as code_file:
                raw_all_codes = json.load(code_file)
            all_codes = pd.read_json(raw_all_codes)

        vocabularies, possible_vocabularies = self.get_controlled_vocabularies()
        self.vocabularies = vocabularies
        self.possible_vocabularies = possible_vocabularies
        self.all_codes = all_codes
        self.code_types = code_types
        self.methods = methods
        self.age_methods = age_methods

    
vocab = Vocabulary()