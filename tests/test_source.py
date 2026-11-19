from pathlib import Path
import pandas as pd

def test_csv_contract():
    path=Path(__file__).resolve().parents[1]/'data/analytics/warehouse_fact_staging.csv'
    df=pd.read_csv(path)
    assert len(df)==25000
    assert df.Ware_house_ID.is_unique
    assert df.product_wg_ton.sum()==552565823
    assert len(df.columns)==31

