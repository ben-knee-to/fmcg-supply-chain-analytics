import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from step5_train import FEATURES, load_data, metrics, pipeline
from sklearn.dummy import DummyRegressor
import numpy as np

def test_split_and_target():
    df,a,b=load_data()
    assert len(a)==20000 and len(b)==5000
    assert not set(a)&set(b)
    assert len(FEATURES)==23
    assert 'storage_issue_reported_l3m' not in FEATURES
    assert 'Ware_house_ID' not in FEATURES

def test_pipeline_and_metrics():
    df,a,b=load_data()
    model=pipeline(DummyRegressor())
    model.fit(df.iloc[a[:100]][FEATURES],df.iloc[a[:100]].product_wg_ton)
    pred=model.predict(df.iloc[b[:10]][FEATURES])
    assert len(pred)==10 and np.isfinite(pred).all()
    assert metrics(df.iloc[b[:10]].product_wg_ton,pred)['mae']>=0
