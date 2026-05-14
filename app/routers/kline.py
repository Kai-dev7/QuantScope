#!/usr/bin/env python3
"""
K线图数据API
专门为前端K线图组件提供数据
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kline", tags=["K线图"])


class KLineRecord(BaseModel):
    """单条K线数据"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    change: Optional[float] = None  # 涨跌幅 %
    turnover: Optional[float] = None  # 换手率 %


class KLineResponse(BaseModel):
    """K线图响应"""
    success: bool
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None
    records: list[KLineRecord]
    count: int
    period: str


def _fetch_from_baostock(symbol: str, limit: int) -> list[dict]:
    """从baostock获取A股K线数据"""
    import baostock as bs

    # 登录
    bs.login()

    # 转换代码格式: 000001 -> sz.000001, 600000 -> sh.600000
    if symbol.startswith('6'):
        bs_symbol = f'sh.{symbol}'
    else:
        bs_symbol = f'sz.{symbol}'

    # 获取日K线 (去掉不支持的 adjust 参数)
    rs = bs.query_history_k_data_plus(
        bs_symbol,
        'date,open,high,low,close,volume,amount,turn',
        start_date=(datetime.now() - timedelta(days=limit * 2)).strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d'),
        frequency='d',
    )

    bs.logout()

    records = []
    prev_close = None
    while rs.error_code == '0' and rs.next():
        row = rs.get_row_data()
        date = row[0]
        open_p = float(row[1]) if row[1] else 0
        high = float(row[2]) if row[2] else 0
        low = float(row[3]) if row[3] else 0
        close = float(row[4]) if row[4] else 0
        volume = float(row[5]) if row[5] else 0
        turn = float(row[7]) if row[7] else None

        change = None
        if prev_close is not None and prev_close > 0:
            change = round((close - prev_close) / prev_close * 100, 2)

        records.append({
            'date': date,
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'change': change,
            'turnover': turn,
        })
        prev_close = close

    # 取最近N条
    records = records[-limit:]
    return records


def _fetch_from_akshare(symbol: str, limit: int) -> list[dict]:
    """从akshare获取A股K线数据"""
    import akshare as ak

    # 判断A股市场
    if symbol.startswith('68'):
        code = f"sh{symbol}"  # 科创板
    elif symbol.startswith('6'):
        code = f"sh{symbol}"  # 上证
    else:
        code = f"sz{symbol}"  # 深证

    df = ak.stock_zh_a_hist(symbol=symbol, period='daily', start_date='', end_date='', adjust='qfq')
    df = df.tail(limit)

    # 列名: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
    records = []
    prev_close = None
    for _, row in df.iterrows():
        date = str(row['日期'])
        open_p = float(row['开盘'])
        close = float(row['收盘'])
        high = float(row['最高'])
        low = float(row['最低'])
        volume = float(row['成交量'])
        turnover = float(row['换手率']) if '换手率' in row and row['换手率'] != '-' else None
        change = float(row['涨跌幅']) if '涨跌幅' in row and row['涨跌幅'] != '-' else None

        records.append({
            'date': date,
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'change': change,
            'turnover': turnover,
        })

    return records


def _fetch_from_akshare_realtime(symbol: str) -> Optional[dict]:
    """获取A股实时行情快照"""
    import akshare as ak

    if symbol.startswith(('60', '68', '000', '001', '002', '003', '300')):
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == symbol]
        if row.empty:
            return None
        r = row.iloc[0]
        return {
            'name': r['名称'],
            'price': float(r['最新价']) if r['最新价'] != '-' else None,
            'change': float(r['涨跌幅']) if r['涨跌幅'] != '-' else None,
            'open': float(r['今开']) if r['今开'] != '-' else None,
            'high': float(r['最高']) if r['最高'] != '-' else None,
            'low': float(r['最低']) if r['最低'] != '-' else None,
            'volume': float(r['成交量']) if r['成交量'] != '-' else None,
            'amount': float(r['成交额']) if r['成交额'] != '-' else None,
        }
    return None


@router.get("/overview")
async def get_market_overview():
    """
    获取主要指数实时行情
    数据源: BaoStock（免费，无需token）
    """
    indices = [
        {"name": "上证指数", "code": "sh.000001"},
        {"name": "深证成指", "code": "sz.399001"},
        {"name": "创业板指", "code": "sz.399006"},
        {"name": "沪深300", "code": "sh.000300"},
    ]

    import baostock as bs
    lg = bs.login()
    if lg.error_code != '0':
        raise HTTPException(status_code=503, detail="Baostock 登录失败")

    results = []
    try:
        for idx in indices:
            rs = bs.query_history_k_data_plus(
                idx["code"],
                "date,open,high,low,close,volume,amount,pctChg",
                start_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
                frequency="d",
            )
            rows = []
            while rs.error_code == '0' and rs.next():
                rows.append(rs.get_row_data())
            if rows:
                latest = rows[-1]
                price = float(latest[3]) if latest[3] else 0      # close
                change = float(latest[7]) if latest[7] else 0     # pctChg
                results.append({
                    "name": idx["name"],
                    "code": idx["code"],
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "up": change >= 0,
                })
    finally:
        bs.logout()

    if not results:
        raise HTTPException(status_code=404, detail="未获取到指数数据")

    return {"success": True, "indices": results, "updated_at": datetime.now().isoformat()}


@router.get("/{symbol}", response_model=KLineResponse)
async def get_kline(
    symbol: str,
    period: str = Query('daily', description="周期: daily/weekly/monthly"),
    limit: int = Query(60, ge=5, le=300, description="K线数量"),
):
    """
    获取股票K线数据

    数据源: Baostock（免费，无需token，稳定）
    """
    records = None
    source = None

    # 优先用 baostock
    try:
        records = _fetch_from_baostock(symbol, limit)
        source = 'baostock'
    except Exception as e:
        logger.warning(f"BaoStock failed for {symbol}: {e}")

    # baostock 失败则用 akshare
    if not records:
        try:
            records = _fetch_from_akshare(symbol, limit)
            source = 'akshare'
        except Exception as e:
            logger.warning(f"AKShare also failed for {symbol}: {e}")

    if not records:
        raise HTTPException(status_code=404, detail=f"未找到股票 {symbol} 的K线数据")

    return KLineResponse(
        success=True,
        symbol=symbol,
        records=[KLineRecord(**r) for r in records],
        count=len(records),
        period=period,
    )


@router.get("/{symbol}/realtime")
async def get_realtime_quote(symbol: str):
    """
    获取实时行情（快照）
    数据源: 腾讯财经（免费，无需token）
    """
    try:
        result = _fetch_from_akshare_realtime(symbol)
        if not result:
            raise HTTPException(status_code=404, detail=f"股票 {symbol} 未找到")
        return {
            'success': True,
            'symbol': symbol,
            **result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时行情失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取实时行情失败: {e}")
