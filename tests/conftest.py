from pathlib import Path
import pytest
import pandas as pd

@pytest.fixture
def source_path():
    return Path(__file__).parent / "fixtures/synthetic_tcc.xlsx"

@pytest.fixture
def fictitious_df(source_path):
    return pd.read_excel(source_path)
