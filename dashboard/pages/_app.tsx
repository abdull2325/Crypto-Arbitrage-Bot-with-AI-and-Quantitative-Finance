import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import { useEffect, useState } from 'react'
import axios from 'axios'

// Set up axios defaults
axios.defaults.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function App({ Component, pageProps }: AppProps) {
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Check API connection on startup
    const checkConnection = async () => {
      try {
        await axios.get('/health')
        setIsConnected(true)
      } catch (error) {
        setIsConnected(false)
        console.error('Failed to connect to API:', error)
      }
    }

    checkConnection()
    
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-dark-bg">
      {!isConnected && (
        <div className="bg-red-600 text-white text-center py-2">
          ⚠️ Cannot connect to bot API. Please check if the bot is running.
        </div>
      )}
      <Component {...pageProps} />
    </div>
  )
}
