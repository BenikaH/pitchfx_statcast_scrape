
# coding: utf-8

# In[16]:

import requests
import xml.etree.ElementTree as et
from os import path
from bs4 import BeautifulSoup


# In[17]:

ROOTPATH = '/home/ubuntu/baseballdata/'

def xml_recurse(table_name, node, gid, referer='NONE', depth=0):
    subtables = list(set([child.tag for child in node.getchildren()])) or ['NONE']
    attribs = list()
    text = ''
    
    if bool(node.attrib):
        attribs = list(node.attrib.values())
    if node.text:
        text = node.text
        
    for child in node.getchildren():
        xml_recurse(table_name, child, node.tag, depth=depth+1)
    
    write_node(table_name, xmltree.tag, node.tag, gid, subtables, referer, attribs, text.strip())
            
def write_node(table_name, rootnode, tag, gid, subtables, parent, attributes, text):
    write_path = '{}.{}.{}.txt'.format(ROOTPATH + table_name, rootnode, tag)
    attributes = '\t'.join(attributes)
    for subtable in subtables:
        with open(write_path, 'a+') as tmp:
            tmp.write('\t'.join([gid, subtable, parent, attributes, text]) + '\n')


# In[18]:

def get_links_in_game(path, depth=0):
    response = requests.get(path)
    soup = BeautifulSoup(response.text, 'html.parser')

    for link in soup.find_all('a')[1:]:
        mylink = link.get('href')
        if mylink.split('.')[-1] in {'xml', 'plist'}:
            table_name = ''
            if depth == 0:
                table_name = (path[96:] + mylink).split('.')[0]
            elif depth == 1:
                table_name = (path[96:] + mylink).split('.')[0].split('/')[0]
            else:
                table_name = (path[96:] + mylink).split('.')[0].split('/')[1] + '_' + (path[96:] + mylink).split('.')[0].split('/')[3]                
            response = requests.get(path + mylink)
            xmltree = et.fromstring(response.text)
            gameid = path + mylink
            gameid = gameid.split('/')[9]
            xml_recurse(table_name, xmltree, gameid)
        else:
            get_links_in_game(path + mylink, depth+1)


# In[20]:

get_links_in_game('http://gd2.mlb.com/components/game/mlb/year_2016/month_05/day_07/gid_2016_05_07_oakmlb_balmlb_1/')
get_links_in_game('http://gd2.mlb.com/components/game/mlb/year_2016/month_05/day_07/gid_2016_05_07_oakmlb_balmlb_2/')


# In[21]:




# In[ ]:



