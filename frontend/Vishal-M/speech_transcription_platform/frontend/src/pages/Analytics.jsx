import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, Clock, FileText } from 'lucide-react'
import axios from 'axios'

export default function Analytics() {
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    failed: 0,
    processing: 0,
    languages: {}
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get('/api/transcripts?limit=1000') // Fetch more to get better stats
      const transcripts = response.data

      const analytics = {
        total: transcripts.length,
        completed: transcripts.filter(t => t.status === 'completed').length,
        failed: transcripts.filter(t => t.status === 'failed').length,
        processing: transcripts.filter(t => t.status === 'processing').length,
        languages: {}
      }

      transcripts.forEach(t => {
        if (t.language) {
          analytics.languages[t.language] = (analytics.languages[t.language] || 0) + 1
        }
      })

      setStats(analytics)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
      setLoading(false)
      // TODO: Add user-facing error message
    }
  }

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className={`text-3xl font-bold ${color} mt-2`}>{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${color} opacity-20 flex items-center justify-center`}>
           {/* Color applied directly to text, Icon color inherited or use text color */}
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  const successRate = stats.total > 0 ? ((stats.completed / stats.total) * 100) : 0;
  const strokeDashoffset = 2 * Math.PI * 70 * (1 - successRate / 100);

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-white">Analytics Dashboard</h1>
        <p className="mt-2 text-gray-400">
          Transcription insights and statistics
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Transcripts"
          value={stats.total}
          icon={FileText}
          color="text-blue-400"
        />
        <StatCard
          title="Completed"
          value={stats.completed}
          icon={TrendingUp}
          color="text-green-400"
        />
        <StatCard
          title="Processing"
          value={stats.processing}
          icon={Clock}
          color="text-yellow-400"
        />
        <StatCard
          title="Failed"
          value={stats.failed}
          icon={BarChart3} // Changed icon for Failed
          color="text-red-400"
        />
      </div>

      <div className="glass-panel p-6">
        <h2 className="text-xl font-semibold text-white mb-6">Language Distribution</h2>
        <div className="space-y-4">
          {Object.entries(stats.languages).sort(([,a],[,b]) => b-a).map(([lang, count]) => {
            const percentage = stats.total > 0 ? (count / stats.total * 100).toFixed(1) : 0;
            return (
              <div key={lang}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-300 font-medium">{lang}</span>
                  <span className="text-gray-400">{count} ({percentage}%)</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-primary-500 to-primary-700 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            )
          })}
          {Object.keys(stats.languages).length === 0 && (
            <p className="text-gray-500 text-center py-8">No language data available</p>
          )}
        </div>
      </div>

       <div className="glass-panel p-6">
         <h2 className="text-xl font-semibold text-white mb-4">Success Rate</h2>
         <div className="flex items-center justify-center py-8">
           <div className="relative w-40 h-40">
             <svg className="transform -rotate-90 w-full h-full" viewBox="0 0 160 160">
               <circle
                 cx="80"
                 cy="80"
                 r="70"
                 stroke="currentColor"
                 strokeWidth="12"
                 fill="transparent"
                 className="text-gray-800"
               />
               <circle
                 cx="80"
                 cy="80"
                 r="70"
                 stroke="currentColor"
                 strokeWidth="12"
                 fill="transparent"
                 strokeDasharray={`${2 * Math.PI * 70}`}
                 strokeDashoffset={strokeDashoffset}
                 className="text-green-500 transition-all duration-500"
                 strokeLinecap="round"
               />
             </svg>
             <div className="absolute inset-0 flex items-center justify-center">
               <span className="text-3xl font-bold text-white">
                 {successRate.toFixed(0)}%
               </span>
             </div>
           </div>
         </div>
       </div>
    </div>
  )
}
