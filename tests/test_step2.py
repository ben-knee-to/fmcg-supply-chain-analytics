import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from step2_clean_features import clean,load_validate

def test_clean_preserves_rows_and_unknowns():
    sample=pd.read_csv(Path(__file__).resolve().parents[1]/'data/raw/FMCG_data.csv').head(20)
    result,checks=clean(sample)
    assert len(result)==len(sample)
    assert result.wh_est_year.isna().sum()==sample.wh_est_year.isna().sum()
    assert 'retailers_per_distributor' in result
    assert checks.shape[0]>0

def test_raw_ids_unique():
    df=load_validate(Path(__file__).resolve().parents[1]/'data/raw/FMCG_data.csv')
    assert df.Ware_house_ID.is_unique
