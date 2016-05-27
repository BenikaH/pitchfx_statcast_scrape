import pytest
from scrapers import MlbamGame

def test_simple():
    assert(MlbamGame._make_mlbam_base_path('gid_2016_05_10_clemlb_houmlb_1') == 'http://gd2.mlb.com/components/game/mlb/year_2016/month_05/day_10/gid_2016_05_10_clemlb_houmlb_1/')
