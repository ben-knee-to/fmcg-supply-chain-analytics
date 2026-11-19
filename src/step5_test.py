from pathlib import Path
import json
import warnings
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, RandomizedSearchCV, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data'/'processed'
OUT = ROOT/'reports'/'step5'
MODELS = ROOT/'models'
TARGET = 'product_wg_ton'
SEED = 42
# Exactly the Step 2 candidate features. No same-period activity or IDs.
FEATURES = [
 'Location_type','WH_capacity_size','zone','WH_regional_zone',
 'Competitor_in_mkt','retail_shop_num','wh_owner_type','distributor_num',
 'flood_impacted','flood_proof','electric_supply','dist_from_hub',
 'workers_num','wh_est_year','temp_reg_mach',
 'approved_wh_govt_certificate','wh_est_year_missing',
 'workers_num_missing','approved_wh_govt_certificate_missing',
 'retailers_per_distributor','distributors_per_1000_retailers',
 'hub_distance_band','has_competition']
CATEGORICAL = ['Location_type','WH_capacity_size','zone','WH_regional_zone',
 'wh_owner_type','approved_wh_govt_certificate','hub_distance_band']
NUMERIC = [x for x in FEATURES if x not in CATEGORICAL]

def load_data():
    df = pd.read_csv(DATA/'fmcg_clean.csv', low_memory=False)
    if len(df) != 25000 or df['Ware_house_ID'].duplicated().any():
        raise ValueError('Unexpected source rows or duplicate warehouse IDs')
    if df[TARGET].isna().any() or not np.isfinite(df[TARGET]).all():
        raise ValueError('Target contains missing or nonfinite values')
    missing = set(FEATURES+[TARGET]) - set(df.columns)
    if missing:
        raise ValueError(f'Missing expected fields: {sorted(missing)}')
    train = pd.read_csv(DATA/'train_index.csv')
    test = pd.read_csv(DATA/'test_index.csv')
    a, b = train.source_row_index.to_numpy(), test.source_row_index.to_numpy()
    if (len(a),len(b)) != (20000,5000):
        raise ValueError('Step 2 split sizes changed')
    if len(set(a)|set(b)) != len(df) or len(set(a)&set(b)):
        raise ValueError('Train/tests split overlap or incomplete coverage')
    if not np.array_equal(df.iloc[a][TARGET].to_numpy(), train[TARGET].to_numpy()):
        raise ValueError('Train indices do not match the Step 2 source row order')
    if not np.array_equal(df.iloc[b][TARGET].to_numpy(), test[TARGET].to_numpy()):
        raise ValueError('Holdout indices do not match the Step 2 source row order')
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    for c in CATEGORICAL:
        df[c] = df[c].astype('object').where(df[c].notna(), np.nan)
        df[c] = df[c].replace('', np.nan)
    return df,a,b

def preprocessing():
    return ColumnTransformer([
      ('num', Pipeline([('imputer',SimpleImputer(strategy='median', add_indicator=False)),
                        ('scaler',StandardScaler())]), NUMERIC),
      ('cat', Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),
                        ('encoder',OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), CATEGORICAL)
    ], sparse_threshold=0)

def pipeline(estimator):
    return Pipeline([('prep',preprocessing()),('model',estimator)])

def metrics(y, pred):
    return {'mae':float(mean_absolute_error(y,pred)),
            'rmse':float(np.sqrt(mean_squared_error(y,pred))),
            'r2':float(r2_score(y,pred))}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    MODELS.mkdir(parents=True,exist_ok=True)
    df,a,b = load_data()
    X,y = df[FEATURES],df[TARGET]
    X_train,y_train = X.iloc[a],y.iloc[a]
    X_test,y_test = X.iloc[b],y.iloc[b]
    cv = KFold(n_splits=3,shuffle=True,random_state=SEED)
    candidates = {
      'dummy': pipeline(DummyRegressor(strategy='mean')),
      'ridge': pipeline(Ridge(alpha=100.0)),
      'random_forest': pipeline(RandomForestRegressor(n_estimators=100,min_samples_leaf=5,max_features=0.8,n_jobs=-1,random_state=SEED)),
      'hist_gradient_boosting': pipeline(HistGradientBoostingRegressor(max_iter=120,learning_rate=0.06,max_leaf_nodes=15,l2_regularization=10,random_state=SEED))
    }
    rows=[]
    for name,model in candidates.items():
        scores=cross_validate(model,X_train,y_train,cv=cv,
          scoring={'mae':'neg_mean_absolute_error','mse':'neg_mean_squared_error','r2':'r2'},n_jobs=1)
        rows.append({'model':name,'cv_mae':float(-scores['test_mae'].mean()),
                     'cv_rmse':float(np.sqrt(-scores['test_mse'].mean())),
                     'cv_r2':float(scores['test_r2'].mean())})
        print(name,rows[-1],flush=True)
    baseline=pd.DataFrame(rows).sort_values('cv_mae')
    baseline.to_csv(OUT/'cv_baselines.csv',index=False)
    # Tune both nonlinear candidates using training-only CV. No holdout inspection.
    searches={
      'random_forest':(RandomForestRegressor(n_jobs=-1,random_state=SEED),{
        'model__n_estimators':[60,80], 'model__max_depth':[10,20,None],
        'model__min_samples_leaf':[3,8,15], 'model__max_features':[0.6,1.0]}),
      'hist_gradient_boosting':(HistGradientBoostingRegressor(random_state=SEED),{
        'model__max_iter':[100,180], 'model__learning_rate':[0.04,0.08],
        'model__max_leaf_nodes':[10,20,31], 'model__l2_regularization':[1.0,20.0]})}
    tuning=[]; tuned={}
    for name,(est,params) in searches.items():
        search=RandomizedSearchCV(pipeline(est),params,n_iter=2,scoring='neg_mean_absolute_error',
          cv=cv,random_state=SEED,n_jobs=1,refit=True,error_score='raise')
        search.fit(X_train,y_train)
        tuned[name]=search.best_estimator_
        tuning.append({'model':name,'cv_mae':float(-search.best_score_),
                       'best_params':json.dumps(search.best_params_)})
        print('tuned',name,tuning[-1],flush=True)
    pd.DataFrame(tuning).to_csv(OUT/'tuning_results.csv',index=False)
    # Choose solely by training CV. Include untuned baselines in competition.
    ranking=[(r['model'],r['cv_mae']) for r in rows]
    ranking += [(r['model']+'_tuned',r['cv_mae']) for r in tuning]
    winner, best_cv_mae=min(ranking,key=lambda p:p[1])
    if winner.endswith('_tuned'):
        best=tuned[winner.removesuffix('_tuned')]
    else:
        best=candidates[winner].fit(X_train,y_train)
    # The only holdout evaluation in this script.
    pred=best.predict(X_test)
    score=metrics(y_test,pred)
    print('FINAL SELECTED',winner,'HOLDOUT',score,flush=True)
    result={'selected_model':winner,'cv_selection_mae':best_cv_mae,
            'holdout':score,'n_train':len(a),'n_holdout':len(b),
            'features':FEATURES,'evaluation':'random warehouse holdout, not future-period validation',
            'target':'historical shipment weight, not customer demand'}
    (OUT/'final_metrics.json').write_text(json.dumps(result,indent=2))
    joblib.dump({'pipeline':best,'features':FEATURES,'target':TARGET,'metrics':result},MODELS/'fmcg_shipment_model.joblib')
    diagnostic=pd.DataFrame({'source_row_index':b,'warehouse_id':df.iloc[b]['Ware_house_ID'].to_numpy(),
                             'actual':y_test.to_numpy(),'predicted':pred,
                             'residual':y_test.to_numpy()-pred,
                             'zone':df.iloc[b]['zone'].to_numpy(),
                             'location_type':df.iloc[b]['Location_type'].to_numpy()})
    diagnostic.to_csv(OUT/'holdout_predictions.csv',index=False)
    groups=[]
    for col in ['zone','location_type']:
        for val,g in diagnostic.groupby(col,dropna=False):
            groups.append({'segment':col,'value':str(val),'n':len(g),
                           **metrics(g.actual,g.predicted),'bias':float(g.residual.mean())})
    pd.DataFrame(groups).to_csv(OUT/'segment_diagnostics.csv',index=False)
    # Permutation importance on a fixed subset of training data, not holdout.
    sample=X_train.sample(n=min(1500,len(X_train)),random_state=SEED)
    importance=permutation_importance(best,sample,y_train.loc[sample.index],
        n_repeats=3,random_state=SEED,scoring='neg_mean_absolute_error',n_jobs=1)
    pd.DataFrame({'feature':FEATURES,'mae_increase':importance.importances_mean,
                  'std':importance.importances_std}).sort_values('mae_increase',ascending=False).to_csv(
                      OUT/'permutation_importance.csv',index=False)
    plt.figure(figsize=(7,5));plt.scatter(pred,diagnostic.residual,s=5,alpha=.25)
    plt.axhline(0,color='black',lw=1);plt.xlabel('Predicted shipment weight');plt.ylabel('Actual minus predicted')
    plt.title('Holdout residual diagnostics');plt.tight_layout();plt.savefig(OUT/'residuals.png',dpi=160);plt.close()
    plt.figure(figsize=(7,5));plt.scatter(diagnostic.actual,pred,s=5,alpha=.25)
    lim=[min(diagnostic.actual.min(),pred.min()),max(diagnostic.actual.max(),pred.max())]
    plt.plot(lim,lim,color='black',ls='--');plt.xlabel('Actual shipment weight');plt.ylabel('Predicted shipment weight')
    plt.title('Holdout predictions');plt.tight_layout();plt.savefig(OUT/'actual_vs_predicted.png',dpi=160);plt.close()
    print('Artifacts saved in',OUT,'and',MODELS)

if __name__=='__main__':
    main()


