from pathlib import Path
import argparse
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def build(step5: Path, step5b: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    pred = pd.read_csv(step5 / 'holdout_predictions.csv')
    required = {'source_row_index','warehouse_id','actual','predicted','residual','zone','location_type'}
    assert required.issubset(pred.columns), required - set(pred.columns)
    assert len(pred) == 5000 and pred.warehouse_id.is_unique
    assert (pred.actual - pred.predicted - pred.residual).abs().max() < 1e-6
    pred = pred.rename(columns={'actual':'actual_shipment_weight','predicted':'predicted_shipment_weight','residual':'signed_error_actual_minus_predicted'})
    pred['absolute_error'] = pred.signed_error_actual_minus_predicted.abs()
    pred['squared_error'] = pred.signed_error_actual_minus_predicted.pow(2)
    pred['evaluation_scope'] = 'Step 5 previously evaluated random holdout'
    pred.to_csv(out / 'model_holdout_predictions.csv',index=False)
    ab = pd.read_csv(step5b / 'ablation_summary.csv')
    assert {'scenario','cv_mae','cv_rmse','cv_r2'}.issubset(ab.columns)
    ab['evaluation_scope'] = 'Step 5B training-only 3-fold CV'
    ab.to_csv(out / 'model_ablation.csv',index=False)
    missing = pd.read_csv(step5b / 'missingness_target_summary.csv')
    missing['evaluation_scope'] = 'Step 5B training-only records'
    missing.to_csv(out / 'training_missingness.csv',index=False)
    seg = pd.read_csv(step5 / 'segment_diagnostics.csv')
    seg['evaluation_scope'] = 'Step 5 previously evaluated random holdout'
    seg.to_csv(out / 'model_segment_diagnostics.csv',index=False)
    with open(step5 / 'final_metrics.json',encoding='utf8') as f: metrics=json.load(f)
    expected = metrics['holdout']
    mae=pred.absolute_error.mean()
    rmse=(pred.squared_error.mean())**.5
    r2=1-pred.squared_error.sum()/((pred.actual_shipment_weight-pred.actual_shipment_weight.mean())**2).sum()
    for key,value in [('mae',mae),('rmse',rmse),('r2',r2)]:
        assert abs(value-expected[key])<1e-6, f'{key} mismatch'
    summary={'n_holdout':len(pred),'holdout_mae':mae,'holdout_rmse':rmse,'holdout_r2':r2,'ablation_scenarios':len(ab),'warning':'Historical shipment prediction only; not demand or optimal replenishment.'}
    (out / 'validation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(json.dumps(summary,indent=2))
    return summary

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--step5',type=Path,required=True,help='Directory containing final_metrics.json, holdout_predictions.csv and segment_diagnostics.csv')
    parser.add_argument('--step5b',type=Path,required=True,help='Directory containing ablation_summary.csv and missingness_target_summary.csv')
    parser.add_argument('--out',type=Path,default=ROOT/'powerbi'/'imports')
    args=parser.parse_args()
    build(args.step5,args.step5b,args.out)