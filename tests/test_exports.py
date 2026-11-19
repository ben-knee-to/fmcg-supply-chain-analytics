from pathlib import Path
import pandas as pd

def test_holdout_export():
    path=Path(__file__).resolve().parents[1]/'powerbi'/'imports'/'model_holdout_predictions.csv'
    df=pd.read_csv(path)
    assert len(df)==5000
    assert df.warehouse_id.is_unique
    assert (df.absolute_error-(df.actual_shipment_weight-df.predicted_shipment_weight).abs()).abs().max()<1e-7

def test_ablation_export():
    path=Path(__file__).resolve().parents[1]/'powerbi'/'imports'/'model_ablation.csv'
    df=pd.read_csv(path)
    assert {'full_conservative','without_est_year'}.issubset(set(df.scenario))
