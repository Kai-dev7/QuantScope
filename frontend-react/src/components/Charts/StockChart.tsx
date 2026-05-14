import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import { KLineRecord } from '@/services/market'

interface StockChartProps {
  symbol: string
  stockName?: string
  records: KLineRecord[]
  height?: number
  showVolume?: boolean
}

export default function StockChart({
  symbol,
  stockName,
  records,
  height = 400,
  showVolume = true,
}: StockChartProps) {
  // 反转数据，因为API返回的是降序
  const data = useMemo(() => {
    return [...records].reverse()
  }, [records])

  const option: EChartsOption = useMemo(() => {
    const dates = data.map(r => r.date)
    const opens = data.map(r => r.open)
    const closes = data.map(r => r.close)
    const lows = data.map(r => r.low)
    const highs = data.map(r => r.high)
    const volumes = data.map(r => r.volume)
    const changes = data.map(r => r.change ?? 0)

    // 计算 MA
    const ma5 = calculateMA(closes, 5)
    const ma10 = calculateMA(closes, 10)
    const ma20 = calculateMA(closes, 20)

    return {
      backgroundColor: 'transparent',
      animation: true,
      animationDuration: 800,

      title: {
        text: showVolume ? '' : `${stockName || symbol} (${symbol})`,
        textStyle: { color: '#fff', fontSize: 14, fontWeight: 600 },
        left: 10,
        top: 5,
      },

      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          lineStyle: { color: 'rgba(255,255,255,0.2)' },
          crossStyle: { color: 'rgba(255,255,255,0.2)' },
        },
        backgroundColor: 'rgba(17,25,39,0.95)',
        borderColor: 'rgba(255,255,255,0.1)',
        textStyle: { color: '#fff', fontSize: 12 },
        formatter: (params: any) => {
          const candle = params.find((p: any) => p.seriesName === 'K线')
          if (!candle) return ''
          const { date, open, close, high, low, volume, change: chg } = data[candle.dataIndex]
          const change = chg ?? 0
          const color = change >= 0 ? '#ef4444' : '#22c55e'
          const arrow = change >= 0 ? '▲' : '▼'
          return `
            <div style="padding:4px">
              <div style="color:#aaa;font-size:11px;margin-bottom:4px">${date}</div>
              <div style="display:grid;grid-template-columns:auto 1fr;gap:2px 8px;font-size:12px">
                <span style="color:#888">开盘</span><span style="color:#fff">${open.toFixed(2)}</span>
                <span style="color:#888">收盘</span><span style="color:#fff">${close.toFixed(2)}</span>
                <span style="color:#888">最高</span><span style="color:#fff">${high.toFixed(2)}</span>
                <span style="color:#888">最低</span><span style="color:#fff">${low.toFixed(2)}</span>
                <span style="color:#888">涨跌</span><span style="color:${color}">${arrow} ${Math.abs(change ?? 0).toFixed(2)}%</span>
                <span style="color:#888">成交量</span><span style="color:#fff">${fmtVolume(volume)}</span>
              </div>
            </div>
          `
        },
      },

      legend: {
        top: 5,
        right: 10,
        data: ['MA5', 'MA10', 'MA20'],
        textStyle: { color: '#aaa', fontSize: 11 },
        itemWidth: 16,
        itemHeight: 2,
      },

      grid: {
        left: '8%',
        right: '5%',
        top: showVolume ? '15%' : '10%',
        bottom: showVolume ? '18%' : '8%',
      },

      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#666',
          fontSize: 10,
          formatter: (v: string) => v.slice(5), // 只显示 MM-DD
          interval: Math.floor(dates.length / 6),
        },
        splitLine: { show: false },
      },

      yAxis: {
        scale: true,
        position: 'left',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#666',
          fontSize: 10,
          formatter: (v: number) => v.toFixed(2),
        },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      },

      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          start: Math.max(0, 100 - Math.round(60 / data.length * 100)),
          end: 100,
        },
        {
          type: 'slider',
          xAxisIndex: 0,
          bottom: showVolume ? '2%' : '0%',
          height: 20,
          borderColor: 'transparent',
          backgroundColor: 'rgba(255,255,255,0.03)',
          fillerColor: 'rgba(59,130,246,0.15)',
          handleStyle: { color: '#3b82f6', borderColor: '#3b82f6' },
          textStyle: { color: '#666', fontSize: 10 },
          dataBackground: {
            lineStyle: { color: 'rgba(255,255,255,0.1)' },
            areaStyle: { color: 'rgba(255,255,255,0.02)' },
          },
        },
      ],

      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: opens.map((o, i) => [o, closes[i], lows[i], highs[i]]),
          itemStyle: {
            color: '#ef4444',       // 上涨 - 红色
            color0: '#22c55e',      // 下跌 - 绿色
            borderColor: '#ef4444',
            borderColor0: '#22c55e',
            borderColorDoji: '#fff',
          },
        },
        {
          name: 'MA5',
          type: 'line',
          data: ma5,
          smooth: false,
          symbol: 'none',
          lineStyle: { color: '#f59e0b', width: 1 },
          z: 10,
        },
        {
          name: 'MA10',
          type: 'line',
          data: ma10,
          smooth: false,
          symbol: 'none',
          lineStyle: { color: '#8b5cf6', width: 1 },
          z: 10,
        },
        {
          name: 'MA20',
          type: 'line',
          data: ma20,
          smooth: false,
          symbol: 'none',
          lineStyle: { color: '#06b6d4', width: 1 },
          z: 10,
        },
        ...(showVolume
          ? [
              {
                name: '成交量',
                type: 'bar' as const,
                xAxisIndex: 0,
                yAxisIndex: 1,
                data: volumes.map((v, i) => ({
                  value: v,
                  itemStyle: {
                    color: changes[i] >= 0
                      ? 'rgba(239,68,68,0.5)'
                      : 'rgba(34,197,94,0.5)',
                  },
                })),
                barWidth: '60%',
              } as any,
            ]
          : []),
      ],

      ...(showVolume
        ? {
            grid: {
              left: '8%',
              right: '5%',
              top: '15%',
              bottom: '18%',
            },
            yAxis: [
              {
                scale: true,
                position: 'left',
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: {
                  color: '#666',
                  fontSize: 10,
                  formatter: (v: number) => v.toFixed(2),
                },
                splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
              },
              {
                scale: true,
                position: 'right',
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { show: false },
                splitLine: { show: false },
              },
            ],
          }
        : {}),
    }
  }, [data, showVolume])

  return (
    <div className="w-full">
      <ReactECharts
        option={option}
        style={{ height: `${height}px`, width: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  )
}

// 计算移动平均线
function calculateMA(data: number[], period: number): (number | null)[] {
  return data.map((_, i) => {
    if (i < period - 1) return null
    const slice = data.slice(i - period + 1, i + 1)
    const avg = slice.reduce((a, b) => a + b, 0) / period
    return Math.round(avg * 100) / 100
  })
}

// 格式化成交量
function fmtVolume(v: number): string {
  if (v >= 1e8) return (v / 1e8).toFixed(2) + '亿'
  if (v >= 1e4) return (v / 1e4).toFixed(0) + '万'
  return v.toFixed(0)
}
