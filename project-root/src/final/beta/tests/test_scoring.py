import pandas as pd


def normalize_series(s: pd.Series, invert: bool = False) -> pd.Series:
    min_v, max_v = float(s.min()), float(s.max())
    if max_v - min_v <= 1e-9:
        out = pd.Series([0.5] * len(s), index=s.index)
    else:
        out = (s - min_v) / (max_v - min_v)
    return 1 - out if invert else out


def test_normalize_series_standard_case():
    s = pd.Series([10, 20, 30])
    out = normalize_series(s)
    assert out.iloc[0] == 0
    assert out.iloc[-1] == 1


def test_normalize_series_inverted():
    s = pd.Series([10, 20, 30])
    out = normalize_series(s, invert=True)
    assert out.iloc[0] == 1
    assert out.iloc[-1] == 0
