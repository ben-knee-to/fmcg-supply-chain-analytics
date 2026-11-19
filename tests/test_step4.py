import pandas as pd
from src.step4_eda import summarise

def test_summary_counts_and_totals():
    df=pd.DataFrame({'zone':['A','A','B'],'product_wg_ton':[10,20,30]})
    result=summarise(df,['zone'])
    assert result.record_count.sum()==3
    assert result.total_shipped_weight.sum()==60
    assert abs(result.share_of_recorded_shipments_pct.sum()-100)<1e-9

def test_summary_means():
    df=pd.DataFrame({'zone':['A','A','B'],'product_wg_ton':[10,20,30]})
    result=summarise(df,['zone']).set_index('zone')
    assert result.loc['A','mean_shipped_weight']==15