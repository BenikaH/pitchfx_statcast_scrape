import datetime
from bs4 import BeautifulSoup

class MlbamGame:
    def __init__(self, gid):
        if self._validate_id(gid):
            self.gid = gid
            self.url = self._make_mlbam_base_path(gid)
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
