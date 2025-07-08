import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

interface AnalyticsData {
  performance: {
    total_trades: number
    total_profit: number
    avg_profit_per_trade: number
    win_rate: number
    best_trade: number
    worst_trade: number
    daily_breakdown: {
      profits: Record<string, number>
      trade_counts: Record<string, number>
    }
  }
  symbol_performance: Array<{
    symbol: string
    trade_count: number
    total_profit: number
    avg_profit: number
  }>
  exchange_performance: Array<{
    buy_exchange: string
    sell_exchange: string
    trade_count: number
    total_profit: number
  }>
}

const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [period, setPeriod] = useState(30)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        
        const [performanceRes, symbolRes, exchangeRes] = await Promise.all([
          fetch(`/api/analytics/performance?days=${period}`),
          fetch('/api/analytics/symbols'),
          fetch('/api/analytics/exchanges')
        ])

        const performanceData = await performanceRes.json()
        const symbolData = await symbolRes.json()
        const exchangeData = await exchangeRes.json()

        setData({
          performance: performanceData.performance,
          symbol_performance: symbolData.symbol_performance || [],
          exchange_performance: exchangeData.exchange_performance || []
        })
        setError(null)
      } catch (err) {
        setError('Failed to fetch analytics data')
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [period])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading analytics...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-red-400 text-xl">{error || 'No data available'}</div>
      </div>
    )
  }

  // Prepare chart data
  const profitChartData = {
    labels: Object.keys(data.performance.daily_breakdown.profits),
    datasets: [
      {
        label: 'Daily Profit ($)',
        data: Object.values(data.performance.daily_breakdown.profits),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.1
      }
    ]
  }

  const tradeCountData = {
    labels: Object.keys(data.performance.daily_breakdown.trade_counts),
    datasets: [
      {
        label: 'Daily Trades',
        data: Object.values(data.performance.daily_breakdown.trade_counts),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1
      }
    ]
  }

  const symbolData = {
    labels: data.symbol_performance.map(s => s.symbol),
    datasets: [
      {
        label: 'Profit by Symbol',
        data: data.symbol_performance.map(s => s.total_profit),
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 205, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)'
        ]
      }
    ]
  }

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        labels: { color: 'white' }
      }
    },
    scales: {
      x: {
        ticks: { color: 'white' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
      y: {
        ticks: { color: 'white' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      }
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Head>
        <title>Analytics - Crypto Arbitrage Bot</title>
      </Head>

      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-2xl font-bold text-white">Analytics Dashboard</h1>
            <nav className="flex space-x-4">
              <Link href="/" className="text-gray-300 hover:text-white px-3 py-2 rounded-md">
                Dashboard
              </Link>
              <Link href="/trades" className="text-gray-300 hover:text-white px-3 py-2 rounded-md">
                Trades
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Period Selector */}
        <div className="mb-8">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Analysis Period
          </label>
          <select
            value={period}
            onChange={(e) => setPeriod(Number(e.target.value))}
            className="bg-gray-800 text-white border border-gray-600 rounded-md px-3 py-2"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">Total Profit</h3>
            <p className={`text-2xl font-bold ${
              data.performance.total_profit >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              ${data.performance.total_profit.toFixed(2)}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">Total Trades</h3>
            <p className="text-2xl font-bold text-blue-400">
              {data.performance.total_trades}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">Win Rate</h3>
            <p className="text-2xl font-bold text-purple-400">
              {(data.performance.win_rate * 100).toFixed(1)}%
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">Avg Profit/Trade</h3>
            <p className={`text-2xl font-bold ${
              data.performance.avg_profit_per_trade >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              ${data.performance.avg_profit_per_trade.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Daily Profit Chart */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Daily Profit Trend</h2>
            <div className="h-64">
              <Line data={profitChartData} options={chartOptions} />
            </div>
          </div>

          {/* Daily Trade Count */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Daily Trade Volume</h2>
            <div className="h-64">
              <Bar data={tradeCountData} options={chartOptions} />
            </div>
          </div>

          {/* Symbol Performance */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Profit by Symbol</h2>
            <div className="h-64">
              <Doughnut 
                data={symbolData} 
                options={{
                  responsive: true,
                  plugins: {
                    legend: {
                      labels: { color: 'white' }
                    }
                  }
                }}
              />
            </div>
          </div>

          {/* Symbol Statistics Table */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Symbol Performance</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2">Symbol</th>
                    <th className="text-right py-2">Trades</th>
                    <th className="text-right py-2">Total Profit</th>
                    <th className="text-right py-2">Avg Profit</th>
                  </tr>
                </thead>
                <tbody>
                  {data.symbol_performance.map((symbol) => (
                    <tr key={symbol.symbol} className="border-b border-gray-700">
                      <td className="py-2 font-medium">{symbol.symbol}</td>
                      <td className="text-right py-2">{symbol.trade_count}</td>
                      <td className={`text-right py-2 ${
                        symbol.total_profit >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        ${symbol.total_profit.toFixed(2)}
                      </td>
                      <td className={`text-right py-2 ${
                        symbol.avg_profit >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        ${symbol.avg_profit.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Exchange Performance */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Exchange Pair Performance</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-2">Buy Exchange</th>
                  <th className="text-left py-2">Sell Exchange</th>
                  <th className="text-right py-2">Trades</th>
                  <th className="text-right py-2">Total Profit</th>
                </tr>
              </thead>
              <tbody>
                {data.exchange_performance.map((exchange, index) => (
                  <tr key={index} className="border-b border-gray-700">
                    <td className="py-2 text-green-400">{exchange.buy_exchange}</td>
                    <td className="py-2 text-red-400">{exchange.sell_exchange}</td>
                    <td className="text-right py-2">{exchange.trade_count}</td>
                    <td className={`text-right py-2 ${
                      exchange.total_profit >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      ${exchange.total_profit.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}

export default AnalyticsPage
