#!/usr/bin/env python3
"""
K线图数据API
专门为前端K线图组件提供数据
"""
import logging
import asyncio
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


class MarketOverviewItem(BaseModel):
    """单个指数/市场指标"""
    name: str
    code: str
    price: float
    change: float
    up: bool
    market: str


class MarketOverviewGroup(BaseModel):
    """按市场分组的概览数据"""
    market: str
    indices: list[MarketOverviewItem]


class MarketOverviewResponse(BaseModel):
    """市场概览响应"""
    success: bool
    markets: list[MarketOverviewGroup]
    indices: list[MarketOverviewItem]
    updated_at: str


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


def _fetch_index_snapshot_from_yfinance(name: str, code: str, market: str) -> Optional[dict]:
    """使用 yfinance 获取指数快照。"""
    try:
        import yfinance as yf
    except Exception as exc:
        logger.warning(f"yfinance not available for {code}: {exc}")
        return None

    try:
        hist = yf.Ticker(code).history(period="5d", interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            return None

        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else None
        close = float(latest.get("Close") or 0)
        if prev is not None and prev.get("Close"):
            prev_close = float(prev.get("Close") or 0)
            change = round((close - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0.0
        else:
            change = 0.0

        return {
            "name": name,
            "code": code,
            "price": round(close, 2),
            "change": change,
            "up": change >= 0,
            "market": market,
        }
    except Exception as exc:
        logger.warning(f"Failed to fetch index snapshot from yfinance for {code}: {exc}")
        return None


async def _fetch_index_snapshot_async(name: str, code: str, market: str) -> Optional[dict]:
    """异步获取指数快照，避免阻塞首页接口。"""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_fetch_index_snapshot_from_yfinance, name, code, market),
            timeout=6,
        )
    except Exception as exc:
        logger.warning(f"Index snapshot timeout or failed for {code}: {exc}")
        return None


@router.get("/overview", response_model=MarketOverviewResponse)
async def get_market_overview():
    """
    获取主要指数实时行情
    数据源: BaoStock + yfinance
    """
    market_indices = {
        "A股": [
            {"name": "上证指数", "code": "sh.000001"},
            {"name": "深证成指", "code": "sz.399001"},
            {"name": "创业板指", "code": "sz.399006"},
            {"name": "沪深300", "code": "sh.000300"},
        ],
        "港股": [
            {"name": "恒生指数", "code": "^HSI"},
            {"name": "恒生中国企业指数", "code": "^HSCE"},
            {"name": "恒生科技指数", "code": "^HSTECH"},
        ],
        "美股": [
            {"name": "道琼斯指数", "code": "^DJI"},
            {"name": "纳斯达克指数", "code": "^IXIC"},
            {"name": "标普500", "code": "^GSPC"},
        ],
    }

    grouped_results: list[MarketOverviewGroup] = []
    flat_results: list[MarketOverviewItem] = []

    import baostock as bs
    lg = bs.login()
    if lg.error_code != '0':
        raise HTTPException(status_code=503, detail="Baostock 登录失败")

    try:
        a_share_items: list[MarketOverviewItem] = []
        for idx in market_indices["A股"]:
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
                price = float(latest[3]) if latest[3] else 0
                change = float(latest[7]) if latest[7] else 0
                item = MarketOverviewItem(
                    name=idx["name"],
                    code=idx["code"],
                    price=round(price, 2),
                    change=round(change, 2),
                    up=change >= 0,
                    market="A股",
                )
                a_share_items.append(item)
                flat_results.append(item)
        if a_share_items:
            grouped_results.append(MarketOverviewGroup(market="A股", indices=a_share_items))
    finally:
        bs.logout()

    for market_name, items in (("港股", market_indices["港股"]), ("美股", market_indices["美股"])):
        snapshots = await asyncio.gather(
            *[_fetch_index_snapshot_async(idx["name"], idx["code"], market_name) for idx in items],
            return_exceptions=True,
        )
        market_results: list[MarketOverviewItem] = []
        for snapshot in snapshots:
            if isinstance(snapshot, Exception) or not snapshot:
                continue
            item = MarketOverviewItem(**snapshot)
            market_results.append(item)
            flat_results.append(item)
        if market_results:
            grouped_results.append(MarketOverviewGroup(market=market_name, indices=market_results))

    if not flat_results:
        raise HTTPException(status_code=404, detail="未获取到指数数据")

    return {
        "success": True,
        "markets": grouped_results,
        "indices": flat_results,
        "updated_at": datetime.now().isoformat(),
    }


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
