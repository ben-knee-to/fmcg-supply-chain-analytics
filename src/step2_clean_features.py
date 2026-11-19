from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/FMCG_data.csv'
OUT = ROOT / 'data/processed'
REPORT = ROOT / 'reports/step2'
TARGET = 'product_wg_ton'
ID_COLS = ['Ware_house_ID', 'WH_Manager_ID']
CAT_COLS = ['Location_type','WH_capacity_size','zone','WH_regional_zone','wh_owner_type','approved_wh_govt_certificate']
BINARY_COLS = ['flood_impacted','flood_proof','electric_supply','temp_reg_mach']
COUNT_COLS = ['num_refill_req_l3m','transport_issue_l1y','Competitor_in_mkt','retail_shop_num','distributor_num','workers_num','storage_issue_reported_l3m','wh_breakdown_l3m','govt_check_l3m']
LEAKAGE_RISK = ['num_refill_req_l3m','storage_issue_reported_l3m','wh_breakdown_l3m','govt_check_l3m','transport_issue_l1y']
EXPECTED = ID_COLS + CAT_COLS + BINARY_COLS + COUNT_COLS + ['dist_from_hub','wh_est_year',TARGET]


def load_validate(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f'Copy FMCG_data.csv to {path}')
    df = pd.read_csv(path)
    if df.columns.duplicated().any():
        raise ValueError('Duplicate column names')
    missing = sorted(set(EXPECTED) - set(df.columns))
    if missing:
        raise ValueError(f'Missing expected columns: {missing}')
    if df[TARGET].isna().any():
        raise ValueError('Missing target values: cannot proceed')
    if df['Ware_house_ID'].isna().any() or df['Ware_house_ID'].duplicated().any():
        raise ValueError('Warehouse IDs must be present and unique')
    return df.copy()


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    issues = []
    for col in CAT_COLS + ID_COLS:
        df[col] = df[col].astype('string').str.strip().replace('', pd.NA)
    for col in BINARY_COLS + COUNT_COLS + ['dist_from_hub','wh_est_year',TARGET]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # No learned imputation or target-based transformations are performed here.
    for col in COUNT_COLS + ['dist_from_hub', TARGET]:
        bad = df[col].notna() & (df[col] < 0)
        issues.append({'check':f'{col}: negative','affected_rows':int(bad.sum()),'severity':'error'})
    for col in BINARY_COLS:
        bad = df[col].notna() & ~df[col].isin([0,1])
        issues.append({'check':f'{col}: not 0/1','affected_rows':int(bad.sum()),'severity':'error'})
    for col in COUNT_COLS + ['wh_est_year']:
        bad = df[col].notna() & (df[col] % 1 != 0)
        issues.append({'check':f'{col}: non-integer','affected_rows':int(bad.sum()),'severity':'error'})
    bad_year = df.wh_est_year.notna() & ~df.wh_est_year.between(1900,2026)
    issues.append({'check':'wh_est_year: outside 1900-2026','affected_rows':int(bad_year.sum()),'severity':'review'})
    for col in CAT_COLS:
        issues.append({'check':f'{col}: missing','affected_rows':int(df[col].isna().sum()),'severity':'review'})
    issues.append({'check':'exact duplicate rows','affected_rows':int(df.duplicated().sum()),'severity':'review'})
    # Flag missingness without replacing unknown years or worker counts.
    for col in ['wh_est_year','workers_num','approved_wh_govt_certificate']:
        df[col+'_missing'] = df[col].isna().astype('int8')
    # Pre-decision features, conditional on source timestamp verification.
    df['retailers_per_distributor'] = df.retail_shop_num.div(df.distributor_num.replace(0,np.nan))
    df['distributors_per_1000_retailers'] = 1000*df.distributor_num.div(df.retail_shop_num.replace(0,np.nan))
    df['hub_distance_band'] = pd.cut(df.dist_from_hub,[-np.inf,50,100,200,np.inf],labels=['<=50km','51-100km','101-200km','>200km'])
    df['has_competition'] = df.Competitor_in_mkt.gt(0).astype('int8')
    return df, pd.DataFrame(issues)


def outliers(df: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for col in COUNT_COLS + ['dist_from_hub',TARGET]:
        x=df[col].dropna()
        q1,q3=x.quantile([.25,.75]); iqr=q3-q1
        lower=q1-1.5*iqr; upper=q3+1.5*iqr
        flagged=int(((x<lower)|(x>upper)).sum()) if iqr>0 else 0
        rows.append({'column':col,'q1':q1,'q3':q3,'iqr':iqr,'lower_fence':lower,'upper_fence':upper,'flagged_count':flagged,'flagged_pct':round(100*flagged/len(x),3) if len(x) else None,'minimum':x.min(),'maximum':x.max()})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True); REPORT.mkdir(parents=True,exist_ok=True)
    raw=load_validate(RAW)
    df, checks=clean(raw)
    severe=checks.loc[(checks.severity=='error') & (checks.affected_rows>0)]
    if not severe.empty:
        checks.to_csv(REPORT/'validation_checks.csv',index=False)
        raise ValueError(f'Invalid source values detected; inspect {REPORT / "validation_checks.csv"}')
    df.to_csv(OUT/'fmcg_clean.csv',index=False)
    checks.to_csv(REPORT/'validation_checks.csv',index=False)
    outliers(df).to_csv(REPORT/'outlier_report.csv',index=False)
    missing=pd.DataFrame({'column':raw.columns,'missing_count':raw.isna().sum().values,'missing_pct':(100*raw.isna().mean()).round(3).values})
    missing.to_csv(REPORT/'missingness_report.csv',index=False)
    grouped=df.groupby('zone',dropna=False)[TARGET].agg(['count','mean','median','std']).reset_index()
    grouped.to_csv(REPORT/'zone_shipment_summary.csv',index=False)
    # Retain NaN in features: imputation must be FIT on training data only.
    conservative=[c for c in raw.columns if c not in ID_COLS+[TARGET]+LEAKAGE_RISK]
    engineered=['wh_est_year_missing','workers_num_missing','approved_wh_govt_certificate_missing','retailers_per_distributor','distributors_per_1000_retailers','hub_distance_band','has_competition']
    model_cols=conservative+engineered+[TARGET]
    df[model_cols].to_csv(OUT/'fmcg_model_candidate.csv',index=False)
    manifest={'raw_rows':len(raw),'clean_rows':len(df),'raw_columns':len(raw.columns),'clean_columns':len(df.columns),'target':TARGET,'target_missing':int(df[TARGET].isna().sum()),'duplicate_warehouse_ids':int(df.Ware_house_ID.duplicated().sum()),'model_columns':model_cols,'excluded_identifiers':ID_COLS,'excluded_timing_risk':LEAKAGE_RISK,'note':'Candidate features only. Confirm each field was available at prediction time. Impute and encode inside training folds, never on full data.'}
    (REPORT/'feature_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    text=f'''# Step 2 data-quality report\n\n- Records retained: {len(df):,} / {len(raw):,}\n- Missing establishment year: {int(raw.wh_est_year.isna().sum()):,}\n- Missing workers: {int(raw.workers_num.isna().sum()):,}\n- Missing certificate: {int(raw.approved_wh_govt_certificate.isna().sum()):,}\n- Unique warehouse IDs: {raw.Ware_house_ID.nunique():,}\n- Missing targets: {int(raw[TARGET].isna().sum())}\n- Full-dataset imputation: **not performed**\n- Outliers: flagged, not deleted or capped\n- Leakage-risk features: {', '.join(LEAKAGE_RISK)}\n\n## Interpretation\nThe target measures historical shipped weight, not observed demand. No temporal or demand forecast is justified without further data. All categorical encoding and numeric imputation must be fitted on training data only.\n'''
    (REPORT/'cleaning_summary.md').write_text(text,encoding='utf-8')
    print(text)
    print('Saved:',OUT.resolve(),REPORT.resolve())

if __name__=='__main__':
    main()

