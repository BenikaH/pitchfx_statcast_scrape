import datetime
import requests
from bs4 import BeautifulSoup
from itertools import count
from itertools import groupby
import xml.etree.cElementTree as et
import pandas as pd

class MlbamGame:
    def __init__(self, gid, write_folder, include=None, exclude=None):
        if self._validate_id(gid):
            self.gid = gid
            self.url = self._make_mlbam_base_path(gid)
            self.include = include
            self.exclude = exclude
            self.write_folder = write_folder
        else:
            raise Exception('{} is not a valid gameid. it must be before today and of the form \"gid_YYYY_MM_DD_<away><league>_<home><league>_<gamenum>\"'.format(gid))

    @staticmethod
    def _validate_id(gid):
        if type(gid) != str:
            return False
        if len(gid) != 30:
            return False
        if datetime.datetime.strptime(gid[4:14], '%Y_%m_%d').date() > datetime.date.today():
            return False
        if datetime.datetime.strptime(gid[4:14], '%Y_%m_%d').date() < datetime.date(2008, 1, 1):
            return False
        return True
    
    @staticmethod
    def _make_mlbam_base_path(gid):
        url_template = 'http://gd2.mlb.com/components/game/mlb/year_{}/month_{}/day_{}/{}/'
        assert(gid[4:8].isnumeric())
        assert(gid[9:11].isnumeric())
        assert(gid[12:14].isnumeric())
        return(url_template.format(gid[4:8], gid[9:11], gid[12:14], gid))
    
    def get_links_in_game(self, exclude=None, include=None):
        if exclude is not None and type(exclude) is not list:
            exclude = [exclude]
        if include is not None and type(include) is not list:
            include = [include]

        if include is not None and exclude is not None:
            raise Exception('only exclude OR include allowed')

        def recurse_links(base_path):
            response = requests.get(base_path)
            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a')[1:]:
                new_base_path = base_path + link.get('href')
                if new_base_path.split('.')[-1] in {'xml', 'plist'}:
                    if exclude is not None and not any([x in new_base_path for x in exclude]):
                        target.append(new_base_path)
                    elif include is not None and any([x in new_base_path for x in include]):
                        target.append(new_base_path)
                    elif exclude is None and include is None:
                        target.append(new_base_path)
                else:
                    recurse_links(new_base_path)

        target = list()
        recurse_links(self.url)
        return(target)

    @staticmethod
    def get_xml_tree(path):
        if path.startswith('http'):
            response = requests.get(path)
        xmltree = et.fromstring(response.text)
        return(xmltree)
    
    def xml_to_table(self, root_node):
        
        def get_key(node):
            if node in indexes:
                return(next(indexes[node]))
            else:
                indexes[node] = count()
                return(next(indexes[node]))

        def recurse_xml(node, referer=None, referer_key=None):
            key = get_key(node.tag)
            subtables = set([child.tag for child in node.getchildren()]) or 'NONE'
            attribs = dict()
            text = ''

            if bool(node.attrib):
                attribs = node.attrib
            if node.text:
                text = node.text

            for child in node.getchildren():
                recurse_xml(child, node.tag, key)

            target.append({
                    'gid': self.gid,
                    'node_type': node.tag,
                    'key': key,
                    'parent_table': referer, 
                    'parent_key': referer_key,
                    'text': text.strip(),
                    **attribs
                })

        indexes = dict()
        target = list()
        recurse_xml(root_node)
        return(target)

    def write_tables(self, rows, rootpath, group_key='node_type'):
        group_func = lambda x: x[group_key]
        for key, group in groupby(sorted(rows, key=group_func), key=group_func):
            table = pd.DataFrame(list(group))
            table.drop(group_key, axis=1, inplace=True)
            table.to_csv('{}{}.tsv'.format(rootpath, key), sep='\t', index=False)
            
    def scrape(self):
        links = self.get_links_in_game(self.exclude, self.include)
        for link in links:
            tree = self.get_xml_tree(link)
            table = self.xml_to_table(tree)
            self.write_tables(table, self.write_folder)
