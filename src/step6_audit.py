from pathlib import Path
import argparse, json, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET='product_wg_ton'; SEED=42
FEATURES=['Location_type','WH_capacity_size','zone','WH_regional_zone','Competitor_in_mkt','retail_shop_num','wh_owner_type','distributor_num','flood_impacted','flood_proof','electric_supply','dist_from_hub','workers_num','wh_est_year','temp_reg_mach','approved_wh_govt_certificate','wh_est_year_missing','workers_num_missing','approved_wh_govt_certificate_missing','retailers_per_distributor','distributors_per_1000_retailers','hub_distance_band','has_competition']
CAT=['Location_type','WH_capacity_size','zone','WH_regional_zone','wh_owner_type','approved_wh_govt_certificate','hub_distance_band']
ABLATONS={
 'full_conservative': FEATURES,
 'without_est_year': [x for x in FEATURES if x!='wh_est_year'],
 'without_year_or_flag': [x for x in FEATURES if x not in ('wh_est_year','wh_est_year_missing')],
 'without_year_or_missingness': [x for x in FEATURES if x not in ('wh_est_year','wh_est_year_missing','workers_num_missing','approved_wh_govt_certificate_missing')],
 'without_year_or_certificate': [x for x in FEATURES if x not in ('wh_est_year','wh_est_year_missing','approved_wh_govt_certificate','approved_wh_govt_certificate_missing')],
 'stable_operational': [x for x in FEATURES if x not in ('wh_est_year','wh_est_year_missing','approved_wh_govt_certificate','approved_wh_govt_certificate_missing','workers_num_missing')],
}
# No target-derived fields or same-period operational variables appear in FEATURES.
BANNED={'Ware_house_ID','WH_Manager_ID','storage_issue_reported_l3m','num_refill_req_l3m','wh_breakdown_l3m','govt_check_l3m','transport_issue_l1y',TARGET}

def model_for(features, dummy=False):
    numeric=[x for x in features if x not in CAT]
    categorical=[x for x in features if x in CAT]
    transformers=[]
    if numeric:
        transformers.append(('numeric',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),numeric))
    if categorical:
        transformers.append(('categorical',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),categorical))
    pre=ColumnTransformer(transformers,sparse_threshold=0)
    est=DummyRegressor(strategy='mean') if dummy else HistGradientBoostingRegressor(max_iter=120,learning_rate=.06,max_leaf_nodes=15,l2_regularization=10,random_state=SEED)
    return Pipeline([('prep',pre),('model',est)])

def load_train(root):
    folder=root/'data'/'processed'
    df=pd.read_csv(folder/'fmcg_clean.csv',low_memory=False)
    idx=pd.read_csv(folder/'train_index.csv')
    assert len(df)==25000 and len(idx)==20000
    a=idx['source_row_index'].to_numpy(dtype=int)
    assert len(set(a))==len(a) and np.all((a>=0)&(a<len(df)))
    assert np.array_equal(df.iloc[a][TARGET].to_numpy(),idx[TARGET].to_numpy()), 'Source order changed'
    assert not (set(FEATURES)&BANNED)
    train=df.iloc[a].copy().reset_index(drop=True)
    for col in FEATURES:
        if col in CAT:
            train[col]=train[col].astype('object').where(train[col].notna(),np.nan).replace('',np.nan)
        else:
            train[col]=pd.to_numeric(train[col],errors='coerce')
    return train

def describe_missingness(train,out):
    rows=[]
    for col in ['wh_est_year','workers_num','approved_wh_govt_certificate']:
        for missing,g in train.groupby(train[col].isna()):
            rows.append({'field':col,'is_missing':bool(missing),'n':len(g),'mean_target':g[TARGET].mean(),'median_target':g[TARGET].median(),'std_target':g[TARGET].std()})
    pd.DataFrame(rows).to_csv(out/'missingness_target_summary.csv',index=False)
    # Quantify apparent mechanical relationships with known-year records only.
    known=train.dropna(subset=['wh_est_year']).copy()
    year_stats=known.groupby('wh_est_year')[TARGET].agg(['size','mean','std']).reset_index()
    year_stats.to_csv(out/'establishment_year_target_summary.csv',index=False)
    # Target-band summaries expose conspicuous missingness mechanisms without implying causality.
    train['target_decile']=pd.qcut(train[TARGET],10,labels=False,duplicates='drop')
    deciles=train.groupby('target_decile',observed=True).agg(n=(TARGET,'size'),mean_target=(TARGET,'mean'),year_missing_rate=('wh_est_year',lambda x:x.isna().mean()),certificate_missing_rate=('approved_wh_govt_certificate',lambda x:x.isna().mean()),workers_missing_rate=('workers_num',lambda x:x.isna().mean())).reset_index()
    deciles.to_csv(out/'missingness_by_target_decile.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,5))
    ax.plot(deciles['target_decile']+1,deciles['year_missing_rate'],marker='o',label='Year missing')
    ax.plot(deciles['target_decile']+1,deciles['certificate_missing_rate'],marker='o',label='Certificate missing')
    ax.set(xlabel='Training target decile (low to high)',ylabel='Missing fraction',title='Missingness across shipment-weight deciles');ax.legend();fig.tight_layout();fig.savefig(out/'missingness_by_decile.png',dpi=160);plt.close(fig)
    return rows

def cv_audit(train,out,n_splits=3):
    y=train[TARGET].to_numpy()
    cv=KFold(n_splits=n_splits,shuffle=True,random_state=SEED)
    foldrows=[]
    scenarios={'mean_baseline':FEATURES,**ABLATONS}
    for name,cols in scenarios.items():
        if set(cols)&BANNED: raise ValueError('Forbidden feature')
        print('Evaluating',name,flush=True)
        for fold,(tr,va) in enumerate(cv.split(train),start=1):
            pipe=model_for(cols,dummy=(name=='mean_baseline'))
            pipe.fit(train.iloc[tr][cols],y[tr]);pred=pipe.predict(train.iloc[va][cols])
            foldrows.append({'scenario':name,'fold':fold,'n_validation':len(va),'mae':mean_absolute_error(y[va],pred),'rmse':np.sqrt(mean_squared_error(y[va],pred)),'r2':r2_score(y[va],pred)})
    folds=pd.DataFrame(foldrows);folds.to_csv(out/'ablation_fold_metrics.csv',index=False)
    summary=folds.groupby('scenario',as_index=False).agg(cv_mae=('mae','mean'),cv_mae_sd=('mae','std'),cv_rmse=('rmse','mean'),cv_r2=('r2','mean'))
    summary=summary.sort_values('cv_mae');summary.to_csv(out/'ablation_summary.csv',index=False)
    # Paired fold differences are descriptive, not confidence intervals with only 3 folds.
    full=folds[folds.scenario=='full_conservative'].set_index('fold')['mae']
    paired=[]
    for name in scenarios:
        v=folds[folds.scenario==name].set_index('fold')['mae']
        paired.append({'scenario':name,'mae_difference_vs_full':float((v-full).mean()),'fold_differences':json.dumps((v-full).round(2).tolist())})
    pd.DataFrame(paired).to_csv(out/'paired_cv_differences.csv',index=False)
    fig,ax=plt.subplots(figsize=(10,5));a=summary.sort_values('cv_mae',ascending=False)
    ax.barh(a.scenario,a.cv_mae);ax.set(xlabel='Training-only CV MAE (lower is better)',title='Leakage and missingness ablations');fig.tight_layout();fig.savefig(out/'ablation_cv_mae.png',dpi=160);plt.close(fig)
    return summary

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--output',type=Path,default=None);args=ap.parse_args()
    root=args.project_root.resolve();out=(args.output or root/'reports'/'step5b').resolve();out.mkdir(parents=True,exist_ok=True)
    train=load_train(root);describe_missingness(train,out);summary=cv_audit(train,out)
    # Diagnostic-only correlations: all measured on training records.
    cols=['wh_est_year','storage_issue_reported_l3m','wh_breakdown_l3m','num_refill_req_l3m','retail_shop_num','dist_from_hub']
    corr=train[cols+[TARGET]].corr(method='pearson')[TARGET].drop(TARGET).rename('pearson_r').to_frame()
    corr['spearman_r']=train[cols+[TARGET]].corr(method='spearman')[TARGET].drop(TARGET)
    corr.to_csv(out/'training_target_correlations.csv')
    report=['# FMCG Step 5B robustness audit','', 'All results below use the original 20,000-row training partition only. The 5,000-row holdout is not read or rescored.','', '## Cross-validation ablations','',summary.round(3).to_markdown(index=False),'','## Interpretation','', 'High correlation is not proof of synthetic generation, causality or leakage. Timing, missingness mechanism and source provenance require independent verification.','', 'No new deployment-ready model is designated by this audit. The original Step 5 model is preserved.','', 'Do not use predicted historical shipments as measured demand or optimal inventory quantities.']
    (out/'audit_report.md').write_text('\n'.join(report),encoding='utf-8')
    (out/'audit_metadata.json').write_text(json.dumps({'training_rows':len(train),'holdout_accessed':False,'seed':SEED,'folds':3,'target':TARGET,'feature_sets':ABLATONS,'recommendation':'research-only; no automated allocation'},indent=2))
    print(summary.to_string(index=False));print('Reports:',out)


if __name__=='__main__': main()
