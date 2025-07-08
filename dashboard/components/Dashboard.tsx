import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface DashboardData {
  bot_status: {
    running: boolean
    paper_trading: boolean
    total_value: number
    daily_pnl: number
    total_trades: number
    active_opportunities: number
  }
  portfolio_metrics: {
    total_value: number
    total_return_pct: number
    sharpe_ratio: number
    max_drawdown_pct: number
    win_rate_pct: number
  }
  recent_trades: Array<{
    id: string
    symbol: string
    profit_abs: number
    profit_pct: number
    timestamp: string
  }>
  performance_data: {
    daily_breakdown: {
      profits: Record<string, number>
      trade_counts: Record<string, number>
    }
  }
}

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Fetch multiple endpoints
      const [botResponse, portfolioResponse, tradesResponse, analyticsResponse] = await Promise.all([
        fetch('/api/bot/status'),
        fetch('/api/portfolio/metrics'),
        fetch('/api/database/trades?limit=10'),
        fetch('/api/analytics/performance?days=30')
      ])

      const botData = await botResponse.json()
      const portfolioData = await portfolioResponse.json()
      const tradesData = await tradesResponse.json()
      const analyticsData = await analyticsResponse.json()

      setData({
        bot_status: botData,
        portfolio_metrics: portfolioData.metrics || {},
        recent_trades: tradesData.trades || [],
        performance_data: analyticsData.performance || { daily_breakdown: { profits: {}, trade_counts: {} } }
      })
      setError(null)
    } catch (err) {
      setError('Failed to fetch dashboard data')
      console.error('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-red-400 text-xl">{error}</div>
      </div>
    )
  }

  // Prepare chart data
  const chartData = {
    labels: Object.keys(data?.performance_data.daily_breakdown.profits || {}),
    datasets: [
      {
        label: 'Daily P&L',
        data: Object.values(data?.performance_data.daily_breakdown.profits || {}),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.1
      }
    ]
  }

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: 'white'
        }
      },
      title: {
        display: true,
        text: 'Daily Performance (30 Days)',
        color: 'white'
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
        <title>Crypto Arbitrage Bot - Dashboard</title>
        <meta name="description" content="Real-time monitoring dashboard for crypto arbitrage trading bot" />
      </Head>

      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-white">Crypto Arbitrage Bot</h1>
              <div className={`ml-4 px-3 py-1 rounded-full text-sm font-medium ${
                data?.bot_status.running ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
              }`}>
                {data?.bot_status.running ? 'RUNNING' : 'STOPPED'}
              </div>
              {data?.bot_status.paper_trading && (
                <div className="ml-2 px-3 py-1 rounded-full text-sm font-medium bg-yellow-600 text-white">
                  PAPER TRADING
                </div>
              )}
            </div>
            <nav className="flex space-x-4">
              <Link href="/trades" className="text-gray-300 hover:text-white px-3 py-2 rounded-md">
                Trades
              </Link>
              <Link href="/analytics" className="text-gray-300 hover:text-white px-3 py-2 rounded-md">
                Analytics
              </Link>
              <Link href="/settings" className="text-gray-300 hover:text-white px-3 py-2 rounded-md">
                Settings
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">Portfolio Value</h3>
            <p className="text-2xl font-bold text-green-400">
              ${(data?.portfolio_metrics.total_value || 0).toLocaleString()}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">Daily P&L</h3>
            <p className={`text-2xl font-bold ${
              (data?.bot_status.daily_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              ${(data?.bot_status.daily_pnl || 0).toFixed(2)}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">Total Trades</h3>
            <p className="text-2xl font-bold text-blue-400">
              {data?.bot_status.total_trades || 0}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">Win Rate</h3>
            <p className="text-2xl font-bold text-purple-400">
              {(data?.portfolio_metrics.win_rate_pct || 0).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Performance Chart */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">Performance Chart</h2>
          <div className="h-64">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Trades */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Recent Trades</h2>
            <div className="space-y-3">
              {data?.recent_trades.map((trade) => (
                <div key={trade.id} className="flex justify-between items-center border-b border-gray-700 pb-2">
                  <div>
                    <p className="font-medium">{trade.symbol}</p>
                    <p className="text-sm text-gray-400">
                      {new Date(trade.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`font-bold ${
                      trade.profit_abs >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      ${trade.profit_abs.toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-400">
                      {trade.profit_pct.toFixed(2)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Portfolio Metrics */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Portfolio Metrics</h2>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-400">Total Return</span>
                <span className={`font-bold ${
                  (data?.portfolio_metrics.total_return_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {(data?.portfolio_metrics.total_return_pct || 0).toFixed(2)}%
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-400">Sharpe Ratio</span>
                <span className="font-bold text-blue-400">
                  {(data?.portfolio_metrics.sharpe_ratio || 0).toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-400">Max Drawdown</span>
                <span className="font-bold text-red-400">
                  {(data?.portfolio_metrics.max_drawdown_pct || 0).toFixed(2)}%
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-400">Active Opportunities</span>
                <span className="font-bold text-yellow-400">
                  {data?.bot_status.active_opportunities || 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard
