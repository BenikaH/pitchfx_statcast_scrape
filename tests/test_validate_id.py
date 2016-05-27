import pytest
from scrapers import MlbamGame 

def test_simple_case():
        assert(MlbamGame._validate_id('gid_2016_05_10_clemlb_houmlb_1') == True)

def test_exception():
         assert(MlbamGame._validate_id('') == False)
         assert(MlbamGame._validate_id('gid_9016_05_10_clemlb_houmlb_1') == False)
         assert(MlbamGame._validate_id(124) == False)
