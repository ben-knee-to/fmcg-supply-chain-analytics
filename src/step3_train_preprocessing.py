from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/processed/fmcg_model_candidate.csv'
DEST=ROOT/'data/processed'; REPORT=ROOT/'reports/step2'

def main():
    df=pd.read_csv(SOURCE)
    y=df.pop('product_wg_ton')
    X=df.replace([np.inf,-np.inf],np.nan)
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.20,random_state=42)
    cat=X.select_dtypes(include=['object','category','string']).columns.tolist()
    num=[c for c in X.columns if c not in cat]
    pre=ColumnTransformer([
        ('num',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),('scale',StandardScaler())]),num),
        ('cat',Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='Missing')),('encode',OneHotEncoder(handle_unknown='ignore'))]),cat)
    ])
    pre.fit(X_train)
    # Persist split indices rather than transformed tests features, to keep evaluation controlled.
    pd.DataFrame({'source_row_index':X_train.index,'product_wg_ton':y_train.to_numpy()}).to_csv(DEST/'train_index.csv',index=False)
    pd.DataFrame({'source_row_index':X_test.index,'product_wg_ton':y_test.to_numpy()}).to_csv(DEST/'test_index.csv',index=False)
    joblib.dump(pre,DEST/'train_fitted_preprocessor.joblib')
    (REPORT/'split_metadata.json').write_text(json.dumps({'train_rows':len(X_train),'test_rows':len(X_test),'random_state':42,'numeric_columns':num,'categorical_columns':cat,'note':'Random holdout is illustrative only; temporal validation requires timestamped records. Do not inspect tests performance until final evaluation.'},indent=2))
    print(f'Train={len(X_train):,}, untouched tests={len(X_test):,}. Train-only preprocessor saved.')

if __name__=='__main__':main()

