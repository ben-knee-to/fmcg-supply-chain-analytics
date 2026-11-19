import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from step6_audit import FEATURES,BANNED,ABLATONS,model_for

def test_no_forbidden_predictors():
    assert not set(FEATURES)&BANNED
    assert all(not set(cols)&BANNED for cols in ABLATONS.values())

def test_all_scenarios_have_predictors():
    assert all(cols for cols in ABLATONS.values())
    assert model_for(ABLATONS['stable_operational']) is not None
