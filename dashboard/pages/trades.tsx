import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import Link from 'next/link'

interface Trade {
  id: string
  symbol: string
  buy_exchange: string
  sell_exchange: string
  buy_price: number
  sell_price: number
  amount: number
  profit_abs: number
  profit_pct: number
  status: string
  timestamp: string
}

const TradesPage: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const response = await fetch('/api/database/trades?limit=100')
        const data = await response.json()
        setTrades(data.trades || [])
        setError(null)
      } catch (err) {
        setError('Failed to fetch trades')
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchTrades()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading trades...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Head>
        <title>Trades - Crypto Arbitrage Bot</title>
      </Head>

      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-2xl font-bold text-white">Trade History</h1>
            <nav className="flex space-x-4">
              <Link href="/" className="text-gray-300 hover:text-white px-3 py-2 rounded-md">
                Dashboard
              </Link>
              <Link href="/analytics" className="text-gray-300 hover:text-white px-3 py-2 rounded-md">
                Analytics
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error ? (
          <div className="text-red-400 text-center">{error}</div>
        ) : (
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700">
              <h2 className="text-lg font-medium">Recent Trades ({trades.length})</h2>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Exchanges
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Prices
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Profit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Time
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {trades.map((trade) => (
                    <tr key={trade.id} className="hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                        {trade.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        <div>
                          <div className="text-green-400">Buy: {trade.buy_exchange}</div>
                          <div className="text-red-400">Sell: {trade.sell_exchange}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        <div>
                          <div className="text-green-400">${trade.buy_price.toFixed(4)}</div>
                          <div className="text-red-400">${trade.sell_price.toFixed(4)}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {trade.amount.toFixed(6)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className={`${trade.profit_abs >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          <div>${trade.profit_abs.toFixed(2)}</div>
                          <div>{trade.profit_pct.toFixed(2)}%</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          trade.status === 'completed' ? 'bg-green-100 text-green-800' :
                          trade.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {trade.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {new Date(trade.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default TradesPage
