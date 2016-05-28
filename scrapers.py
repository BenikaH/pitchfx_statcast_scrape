import datetime
import requests
from bs4 import BeautifulSoup
from itertools import count
from itertools import groupby
from io import StringIO
import xml.etree.cElementTree as et
import pandas as pd

class Game:
    mlabam_to_savant_team = {'ana': 'LAA', 
                             'hou': 'HOU', 
                             'oak': 'OAK', 
                             'tor': 'TOR', 
                             'atl': 'ATL', 
                             'mil': 'MIL', 
                             'sln': 'STL', 
                             'chn': 'CHC', 
                             'ari': 'ARI', 
                             'lan': 'LAD', 
                             'sfn': 'SF', 
                             'cle': 'CLE', 
                             'sea': 'SEA', 
                             'mia': 'MIA', 
                             'nyn': 'NYM', 
                             'was': 'WSH', 
                             'bal': 'BAL', 
                             'sdn': 'SD', 
                             'phi': 'PHI', 
                             'pit': 'PIT', 
                             'tex': 'TEX', 
                             'tba': 'TB', 
                             'bos': 'BOS', 
                             'cin': 'CIN', 
                             'col': 'COL', 
                             'kca': 'KC', 
                             'det': 'DET', 
                             'min': 'MIN', 
                             'cha': 'CWS', 
                             'nya': 'NYY'
                        }

    def __init__(self, gid, write_folder, include='default', exclude=None):
        if include == 'default':
            include = ['inning_all', 'boxscore.xml', 'game.xml']
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
            
    def get_statcast_data(self):
        year = self.gid[4:8]
        month = self.gid[9:11]
        day = self.gid[12:14]
        away = self.mlabam_to_savant_team[self.gid[15:18]]
        home = self.mlabam_to_savant_team[self.gid[22:25]]

        date = '-'.join([year, month, day])
        savant_url = 'https://baseballsavant.mlb.com/statcast_search/csv?all=true&hfPT=&hfZ=&hfGT=R%7C&hfPR=&hfAB=&stadium=&hfBBT=&hfBBL=&hfC=&season={}&player_type=batter&hfOuts=&pitcher_throws=&batter_stands=&start_speed_gt=&start_speed_lt=&perceived_speed_gt=&perceived_speed_lt=&spin_rate_gt=&spin_rate_lt=&exit_velocity_gt=&exit_velocity_lt=&launch_angle_gt=&launch_angle_lt=&distance_gt=&distance_lt=&batted_ball_angle_gt=&batted_ball_angle_lt=&game_date_gt={}&game_date_lt={}&team={}&position=&hfRO=&home_road=&hfInn=&min_pitches=0&min_results=0&group_by=name&sort_col=pitches&sort_order=desc&min_abs=0&xba_gt=&xba_lt=&px1=&px2=&pz1=&pz2=&type=details&'
        home_url = savant_url.format(year, date, date, home)
        statcast = requests.get(home_url)
        home_table = pd.read_csv(StringIO(statcast.text))
        away_url = savant_url.format(year, date, date, away)
        statcast = requests.get(away_url)
        away_table = pd.read_csv(StringIO(statcast.text))

        return(pd.concat([home_table, away_table]))
            
    def scrape(self):
        links = self.get_links_in_game(self.exclude, self.include)
        for link in links:
            tree = self.get_xml_tree(link)
            table = self.xml_to_table(tree)
            self.write_tables(table, self.write_folder)
        
        statcast_table = self.get_statcast_data()
        statcast_table.to_csv('{}{}.tsv'.format(self.write_folder, 'statcast'), sep='\t', index=False)

