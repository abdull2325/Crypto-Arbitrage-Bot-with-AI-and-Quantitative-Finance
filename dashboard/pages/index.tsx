import type { NextPage } from 'next'
import Dashboard from '../components/Dashboard'

const Home: NextPage = () => {
  return <Dashboard />
}

export default Home
      }
      
      // Refresh status after action
      setTimeout(fetchData, 1000)
    } catch (err) {
      console.error('Error controlling bot:', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-gray-400">Loading...</div>
      </div>
    )
  }

  return (
    <>
      <Head>
        <title>Crypto Arbitrage Bot Dashboard</title>
        <meta name="description" content="Real-time dashboard for crypto arbitrage trading bot" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">
            Crypto Arbitrage Bot
          </h1>
          
          <div className="flex items-center space-x-4">
            {botStatus && (
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                botStatus.running 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {botStatus.running ? 'Running' : 'Stopped'}
              </div>
            )}
            
            <button
              onClick={handleStartStop}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium ${
                botStatus?.running
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {botStatus?.running ? (
                <>
                  <StopIcon className="w-4 h-4" />
                  <span>Stop Bot</span>
                </>
              ) : (
                <>
                  <PlayIcon className="w-4 h-4" />
                  <span>Start Bot</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-6">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
              {error}
            </div>
          </div>
        )}

        {/* Status Cards */}
        {botStatus && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-dark-card p-6 rounded-lg border border-gray-700">
              <div className="flex items-center">
                <CurrencyDollarIcon className="w-8 h-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Total Value</p>
                  <p className="text-2xl font-bold text-white">
                    ${botStatus.total_value.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-dark-card p-6 rounded-lg border border-gray-700">
              <div className="flex items-center">
                <ChartBarIcon className="w-8 h-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Daily P&L</p>
                  <p className={`text-2xl font-bold ${
                    botStatus.daily_pnl >= 0 ? 'text-green-500' : 'text-red-500'
                  }`}>
                    ${botStatus.daily_pnl.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-dark-card p-6 rounded-lg border border-gray-700">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                  T
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Total Trades</p>
                  <p className="text-2xl font-bold text-white">
                    {botStatus.total_trades}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-dark-card p-6 rounded-lg border border-gray-700">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center text-white font-bold">
                  O
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Opportunities</p>
                  <p className="text-2xl font-bold text-white">
                    {opportunities.length}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Trading Mode Banner */}
        {botStatus && (
          <div className={`mb-8 p-4 rounded-lg border ${
            botStatus.paper_trading
              ? 'bg-blue-900 border-blue-700 text-blue-100'
              : 'bg-red-900 border-red-700 text-red-100'
          }`}>
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
              <span className="font-medium">
                {botStatus.paper_trading ? 'Paper Trading Mode' : 'Live Trading Mode'}
              </span>
              <span className="ml-2 text-sm">
                {botStatus.paper_trading 
                  ? '(Simulated trades only)' 
                  : '(Real money at risk!)'}
              </span>
            </div>
          </div>
        )}

        {/* Opportunities Table */}
        <div className="bg-dark-card rounded-lg border border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">
              Active Arbitrage Opportunities
            </h2>
          </div>
          
          {opportunities.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-dark-accent">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Buy Exchange
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Sell Exchange
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Profit %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Confidence
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Timestamp
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-dark-card divide-y divide-gray-700">
                  {opportunities.map((opp) => (
                    <tr key={opp.id} className="hover:bg-dark-accent">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                        {opp.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {opp.buy_exchange}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {opp.sell_exchange}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-500">
                        {opp.profit_pct.toFixed(3)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        <div className="flex items-center">
                          <div className="w-full bg-gray-600 rounded-full h-2 mr-2">
                            <div 
                              className="bg-crypto-blue h-2 rounded-full" 
                              style={{ width: `${opp.confidence_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs">
                            {(opp.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {new Date(opp.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="px-6 py-8 text-center text-gray-400">
              <p>No opportunities detected</p>
              <p className="text-sm mt-1">
                {botStatus?.running ? 'Scanning markets...' : 'Start the bot to begin scanning'}
              </p>
            </div>
          )}
        </div>
      </main>
    </>
  )
}
