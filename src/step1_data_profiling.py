from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data' / 'raw' / 'FMCG_data.csv'
OUT = ROOT / 'reports' / 'step1'
TARGET = 'product_wg_ton'
EXPECTED = ['Ware_house_ID','WH_Manager_ID','Location_type','WH_capacity_size','zone','WH_regional_zone','num_refill_req_l3m','transport_issue_l1y','Competitor_in_mkt','retail_shop_num','wh_owner_type','distributor_num','flood_impacted','flood_proof','electric_supply','dist_from_hub','workers_num','wh_est_year','storage_issue_reported_l3m','temp_reg_mach','approved_wh_govt_certificate','wh_breakdown_l3m','govt_check_l3m','product_wg_ton']

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if not INPUT.is_file():
        raise FileNotFoundError(f'Missing input CSV: {INPUT}')
    df = pd.read_csv(INPUT, low_memory=False)
    if TARGET not in df.columns:
        raise ValueError(f'Missing target: {TARGET}')
    missing_expected = sorted(set(EXPECTED) - set(df.columns))
    unexpected = sorted(set(df.columns) - set(EXPECTED))
    missing = df.isna().sum()
    profile = pd.DataFrame({'column':df.columns,'dtype':[str(df[c].dtype) for c in df], 'non_null':[int(df[c].notna().sum()) for c in df], 'missing_count':[int(missing[c]) for c in df], 'missing_pct':[round(float(df[c].isna().mean()*100),3) for c in df], 'unique_non_null':[int(df[c].nunique(dropna=True)) for c in df]})
    profile.to_csv(OUT/'column_profile.csv',index=False)
    numeric = df.select_dtypes(include='number')
    numeric.describe().T.to_csv(OUT/'numeric_summary.csv',index_label='column')
    categorical = df.select_dtypes(exclude='number')
    category_rows=[]
    for col in categorical:
        for value,count in df[col].fillna('<MISSING>').astype(str).value_counts().items():
            category_rows.append({'column':col,'category':value,'count':int(count),'percentage':round(100*count/len(df),3)})
    pd.DataFrame(category_rows).to_csv(OUT/'categorical_frequencies.csv',index=False)
    checks=[]
    def check(name, affected, severity, note):
        checks.append({'check':name,'affected_rows':int(affected),'severity':severity,'note':note})
    check('duplicate_rows',df.duplicated().sum(),'high','Exact duplicate rows')
    check('duplicate_warehouse_ids',df['Ware_house_ID'].duplicated().sum(),'review','Unique ID assumption; verify grain')
    check('missing_target',df[TARGET].isna().sum(),'high','Target must be present')
    check('nonpositive_target',(df[TARGET]<=0).sum(),'high','Target should be positive')
    check('missing_establishment_year',df['wh_est_year'].isna().sum(),'review','Do not impute before investigating')
    check('future_establishment_year',(df['wh_est_year']>pd.Timestamp.today().year).sum(),'review','Potential invalid year')
    check('negative_worker_count',(df['workers_num']<0).sum(),'high','Negative counts invalid')
    for col in ['num_refill_req_l3m','transport_issue_l1y','Competitor_in_mkt','retail_shop_num','distributor_num','dist_from_hub','storage_issue_reported_l3m','wh_breakdown_l3m','govt_check_l3m']:
        check('negative_'+col,(df[col]<0).sum(),'high','Negative count or distance')
    for col in ['flood_impacted','flood_proof','electric_supply','temp_reg_mach']:
        check('invalid_binary_'+col,(~df[col].isin([0,1])).sum(),'high','Expected 0 or 1')
    pd.DataFrame(checks).to_csv(OUT/'data_quality_checks.csv',index=False)
    target = df[TARGET].describe()
    summary={'rows':len(df),'columns':len(df.columns),'missing_cells':int(missing.sum()),'duplicate_rows':int(df.duplicated().sum()),'unique_warehouse_ids':int(df['Ware_house_ID'].nunique()),'missing_expected_columns':missing_expected,'unexpected_columns':unexpected,'target':{str(k):round(float(v),4) for k,v in target.items()},'note':'Shipment target is historical shipped weight, not observed demand or optimal allocation.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(figsize=(9,5))
    ax.hist(df[TARGET].dropna(),bins=35,edgecolor='white')
    ax.set(xlabel='Product shipped (dataset tonnage units)',ylabel='Warehouse records',title='Historical shipment weight distribution')
    fig.tight_layout();fig.savefig(OUT/'target_distribution.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4))
    affected=profile.loc[profile.missing_count>0].sort_values('missing_pct')
    ax.barh(affected['column'],affected['missing_pct'])
    ax.set(xlabel='Missing values (%)',title='Missingness by column',xlim=(0,100))
    fig.tight_layout();fig.savefig(OUT/'missingness.png',dpi=160);plt.close(fig)
    report=f'''# Step 1: FMCG Data Profiling Report\n\n- Rows: {len(df):,}\n- Columns: {len(df.columns)}\n- Missing cells: {int(missing.sum()):,}\n- Duplicate rows: {int(df.duplicated().sum()):,}\n- Unique warehouse IDs: {df['Ware_house_ID'].nunique():,}\n- Missing expected columns: {missing_expected}\n- Unexpected columns: {unexpected}\n\n## Target: {TARGET}\n\n- Mean: {target['mean']:,.2f}\n- Median: {target['50%']:,.2f}\n- Standard deviation: {target['std']:,.2f}\n- Minimum: {target['min']:,.0f}\n- Maximum: {target['max']:,.0f}\n\n## Missing data\n\n{profile.loc[profile.missing_count>0,['column','missing_count','missing_pct']].to_markdown(index=False) if False else profile.loc[profile.missing_count>0,['column','missing_count','missing_pct']].to_string(index=False)}\n\n## Interpretation\n\nThe target measures historical shipments in the prior three months, not demand. Without stockouts, sales, inventory, dates and costs, optimal allocation cannot be established. Do not drop or impute missing values in Step 1. Verify target units and dataset grain with the data owner.\n'''
    (OUT/'profiling_report.md').write_text(report,encoding='utf-8')
    print(report)
    print(f'All outputs saved to: {OUT}')

if __name__=='__main__':
    main()
