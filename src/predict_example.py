from pathlib import Path
import joblib
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
artifact = joblib.load(ROOT/'models'/'fmcg_shipment_model.joblib')
frame = pd.read_csv(ROOT/'data'/'processed'/'fmcg_clean.csv').head(5)
pred = artifact['pipeline'].predict(frame[artifact['features']])
print(pd.DataFrame({'warehouse_id':frame['Ware_house_ID'],'predicted_shipment_weight':pred}).to_string(index=False))