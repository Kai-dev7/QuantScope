import json
import sys
import types

import pandas as pd

from app.services.data_sources.akshare_adapter import AKShareAdapter


def test_get_stock_list_falls_back_to_spot_api(monkeypatch):
    fake_akshare = types.SimpleNamespace()

    def broken_code_name():
        raise json.JSONDecodeError("Expecting value", "", 0)

    def spot_em():
        return pd.DataFrame(
            [
                {"代码": "000001", "名称": "平安银行"},
                {"代码": "sh600000", "名称": "浦发银行"},
                {"代码": "000001", "名称": "重复数据"},
            ]
        )

    fake_akshare.stock_info_a_code_name = broken_code_name
    fake_akshare.stock_zh_a_spot_em = spot_em
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    df = AKShareAdapter().get_stock_list()

    assert df is not None
    assert list(df["symbol"]) == ["000001", "600000"]
    assert list(df["ts_code"]) == ["000001.SZ", "600000.SH"]
    assert list(df.columns) == ["symbol", "name", "ts_code", "area", "industry", "market", "list_date"]


def test_normalize_stock_list_rejects_unexpected_columns():
    adapter = AKShareAdapter()
    df = adapter._normalize_stock_list(pd.DataFrame([{"foo": "000001", "bar": "平安银行"}]), "fake")

    assert df is None
