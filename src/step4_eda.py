from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'data/processed/fmcg_clean.csv'
if not INPUT.exists(): INPUT=ROOT/'data/analytics/_input_clean.csv'
OUT=ROOT/'data/analytics'; REPORT=ROOT/'reports/step3'; CHARTS=REPORT/'charts'
TARGET='product_wg_ton'
GROUPS=['zone','WH_regional_zone','Location_type','WH_capacity_size','wh_owner_type','approved_wh_govt_certificate','flood_impacted','flood_proof','electric_supply','temp_reg_mach','hub_distance_band']
NUMERIC=['retail_shop_num','distributor_num','Competitor_in_mkt','dist_from_hub','workers_num','wh_est_year','num_refill_req_l3m','transport_issue_l1y','storage_issue_reported_l3m','wh_breakdown_l3m','govt_check_l3m','retailers_per_distributor']
OPERATIONAL=['num_refill_req_l3m','transport_issue_l1y','storage_issue_reported_l3m','wh_breakdown_l3m','govt_check_l3m']

def summarise(df,keys):
    t=df.groupby(keys,dropna=False,observed=True)[TARGET].agg(record_count='size',total_shipped_weight='sum',mean_shipped_weight='mean',median_shipped_weight='median',std_shipped_weight='std').reset_index()
    t['share_of_recorded_shipments_pct']=100*t.total_shipped_weight/df[TARGET].sum()
    t['share_of_warehouses_pct']=100*t.record_count/len(df)
    t['se_mean']=t.std_shipped_weight/np.sqrt(t.record_count)
    t['ci95_low_approx']=t.mean_shipped_weight-1.96*t.se_mean
    t['ci95_high_approx']=t.mean_shipped_weight+1.96*t.se_mean
    return t.sort_values('total_shipped_weight',ascending=False)

def save_plot(name):
    plt.tight_layout();plt.savefig(CHARTS/name,dpi=155,bbox_inches='tight');plt.close()

def main():
    OUT.mkdir(parents=True,exist_ok=True);CHARTS.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(INPUT)
    if TARGET not in df or df[TARGET].isna().any(): raise ValueError('Missing target or target column')
    if df.Ware_house_ID.duplicated().any():raise ValueError('Duplicate warehouse IDs')
    sns.set_theme(style='whitegrid')
    summary={'rows':len(df),'unique_warehouses':df.Ware_house_ID.nunique(),'total_recorded_shipped_weight':float(df[TARGET].sum()),'mean_shipped_weight':float(df[TARGET].mean()),'median_shipped_weight':float(df[TARGET].median()),'std_shipped_weight':float(df[TARGET].std()),'target_units':'tons per source dictionary (unverified)','warning':'Shipment weight is not actual customer demand; no time series is provided.'}
    (REPORT/'kpis.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    df[TARGET].describe(percentiles=[.05,.25,.5,.75,.95,.99]).to_frame('value').to_csv(REPORT/'shipment_descriptive_statistics.csv')
    groups=[]
    for key in GROUPS:
        if key not in df:continue
        t=summarise(df,[key]);t.insert(0,'dimension',key);t=t.rename(columns={key:'dimension_value'});t.to_csv(OUT/f'group_{key}.csv',index=False);groups.append(t)
    pd.concat(groups,ignore_index=True).to_csv(OUT/'warehouse_segment_summary.csv',index=False)
    if {'zone','WH_regional_zone'}.issubset(df):summarise(df,['zone','WH_regional_zone']).to_csv(OUT/'zone_regional_summary.csv',index=False)
    if {'zone','WH_capacity_size'}.issubset(df):summarise(df,['zone','WH_capacity_size']).to_csv(OUT/'zone_capacity_summary.csv',index=False)
    if {'zone','Location_type'}.issubset(df):summarise(df,['zone','Location_type']).to_csv(OUT/'zone_location_summary.csv',index=False)
    if {'zone','wh_owner_type'}.issubset(df):summarise(df,['zone','wh_owner_type']).to_csv(OUT/'zone_ownership_summary.csv',index=False)
    # Descriptive warehouse fact table for database staging; keep IDs and source columns.
    df.to_csv(OUT/'warehouse_fact_staging.csv',index=False)
    corr=[]
    for c in NUMERIC:
        if c not in df:continue
        pair=df[[c,TARGET]].replace([np.inf,-np.inf],np.nan).dropna()
        corr.append({'feature':c,'complete_pairs':len(pair),'pearson_r':pair[c].corr(pair[TARGET],method='pearson') if len(pair)>2 else np.nan,'spearman_r':pair[c].corr(pair[TARGET],method='spearman') if len(pair)>2 else np.nan,'missing_count':int(df[c].isna().sum()),'same_period_or_timing_risk':c in OPERATIONAL})
    corr=pd.DataFrame(corr).sort_values('spearman_r',key=lambda s:s.abs(),ascending=False)
    corr.to_csv(REPORT/'numeric_correlations.csv',index=False)
    op=[]
    for c in OPERATIONAL:
        if c not in df:continue
        x=df[c]
        for label,mask in [('zero',x.eq(0)),('positive',x.gt(0)),('missing',x.isna())]:
            y=df.loc[mask,TARGET]
            op.append({'metric':c,'group':label,'record_count':len(y),'mean_shipped_weight':y.mean(),'median_shipped_weight':y.median(),'total_shipped_weight':y.sum()})
    pd.DataFrame(op).to_csv(OUT/'operational_issue_summary.csv',index=False)
    missing=df.isna().sum().rename('missing_count').reset_index().rename(columns={'index':'column'});missing['missing_pct']=100*missing.missing_count/len(df)
    missing.to_csv(REPORT/'clean_dataset_missingness.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,5));sns.histplot(df[TARGET],bins=45,ax=ax,color='#2563eb');ax.set(title='Historical warehouse shipment weights',xlabel='Recorded shipped weight (source-stated tons)',ylabel='Warehouse count');save_plot('shipment_distribution.png')
    for group in ['zone','WH_capacity_size','Location_type','wh_owner_type']:
        if group not in df:continue
        g=summarise(df,[group]).sort_values('mean_shipped_weight',ascending=False)
        fig,ax=plt.subplots(figsize=(9,5));sns.barplot(data=g,x=group,y='mean_shipped_weight',ax=ax,color='#2878b5');ax.set(title=f'Mean shipment weight by {group}',ylabel='Mean recorded shipment weight',xlabel=group);ax.tick_params(axis='x',rotation=25);save_plot(f'mean_by_{group}.png')
    if 'zone' in df:
        fig,ax=plt.subplots(figsize=(10,5));sns.boxplot(data=df,x='zone',y=TARGET,showfliers=False,ax=ax);ax.set(title='Shipment weight spread by zone',ylabel='Recorded shipment weight');save_plot('zone_boxplot.png')
    numeric_corr=corr.dropna(subset=['spearman_r']).head(12).sort_values('spearman_r')
    fig,ax=plt.subplots(figsize=(10,6));sns.barplot(data=numeric_corr,x='spearman_r',y='feature',color='#2878b5',ax=ax);ax.set(title='Rank correlation with shipment weight (descriptive only)',xlabel='Spearman correlation',ylabel='');save_plot('numeric_spearman_correlations.png')
    for col in ['retail_shop_num','distributor_num','dist_from_hub','workers_num']:
        if col not in df:continue
        s=df[[col,TARGET]].dropna().sample(n=min(3000,df[col].notna().sum()),random_state=42)
        fig,ax=plt.subplots(figsize=(8,5));sns.scatterplot(data=s,x=col,y=TARGET,alpha=.25,s=12,ax=ax);ax.set(title=f'{col} vs shipped weight (sample)',ylabel='Recorded shipped weight');save_plot(f'scatter_{col}.png')
    # Narrative assembled from computed results, not invented business conclusions.
    z=summarise(df,['zone']);top=z.iloc[0]
    lines=['# Step 3 EDA — business findings','',f'- Warehouse records: **{len(df):,}**',f'- Total recorded shipped weight: **{df[TARGET].sum():,.0f}** (source-stated tons, unit not independently verified)',f'- Average shipped weight: **{df[TARGET].mean():,.2f}**',f'- Median shipped weight: **{df[TARGET].median():,.2f}**',f'- Zone with highest aggregate recorded shipment weight: **{top.zone}**, {top.total_shipped_weight:,.0f}, from {int(top.record_count):,} warehouses.','', '## Interpretation boundaries','- Shipment volume is not demand, sales, stockouts, service level or profitability.','- Comparisons are observational and not causal.','- Recent operational measures may be contemporaneous with shipments; do not use them as pre-decision model predictors without timing verification.','- Each warehouse appears once; no time-series trends or forecasting are justified.','- Aggregate shipment sums assume each row is a distinct nonoverlapping warehouse observation.','- Large regional totals reflect both record counts and per-warehouse shipment volumes.','- Source states tons; confirm business units before operational use.','', '## Further analysis','- Review warehouse counts and confidence intervals alongside mean differences.','- Investigate missing establishment years before any age-related claims.','- Obtain demand, inventory, costs, lead times and dates to support true supply optimisation.']
    (REPORT/'business_findings.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print('\n'.join(lines[:8]));print(f'Created {len(list(CHARTS.glob("*.png")))} charts, {len(list(OUT.glob("*.csv")))} analytical CSVs')
if __name__=='__main__':main()


