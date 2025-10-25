import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Trash2, Eye, Filter, Loader, X } from 'lucide-react'
import axios from 'axios'

// Debounce function
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}


export default function TranscriptTable({ refreshTrigger }) {
  const [transcripts, setTranscripts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedTranscript, setSelectedTranscript] = useState(null)
  const [pollingInterval, setPollingInterval] = useState(null)

  const fetchTranscripts = async (showLoading = true) => {
    if (showLoading) setLoading(true)
    setError(null)
    try {
      const response = await axios.get('/api/transcripts', {
        params: { limit: 100 } // Fetch last 100, adjust if needed
      })
      setTranscripts(response.data)
      // Check if any are still processing/pending to start/stop polling
      const needsPolling = response.data.some(t => t.status === 'processing' || t.status === 'pending');
      if (needsPolling && !pollingInterval) {
        startPolling();
      } else if (!needsPolling && pollingInterval) {
        stopPolling();
      }

    } catch (err) {
      console.error('Failed to fetch transcripts:', err)
      setError('Failed to load history. Please try refreshing.')
    } finally {
      if (showLoading) setLoading(false)
    }
  }

  // Debounced version of fetchTranscripts for polling
  const debouncedFetch = useCallback(debounce(() => fetchTranscripts(false), 500), []);


  const startPolling = () => {
    if (pollingInterval) return; // Already polling
    console.log("Starting polling for transcript status...");
    const intervalId = setInterval(() => {
      debouncedFetch();
    }, 5000); // Poll every 5 seconds
    setPollingInterval(intervalId);
  };

  const stopPolling = () => {
    if (pollingInterval) {
      console.log("Stopping polling.");
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };


  useEffect(() => {
    fetchTranscripts()
    // Start polling if needed after initial fetch
    return () => stopPolling(); // Cleanup on unmount
  }, [refreshTrigger]) // Also re-fetch on external trigger

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this transcript permanently?')) return

    try {
      await axios.delete(`/api/transcripts/${id}`)
      setTranscripts(transcripts.filter(t => t.id !== id))
      setSelectedTranscript(null) // Close modal if open
    } catch (error) {
      console.error('Failed to delete transcript:', error)
      alert('Failed to delete transcript. Please try again.')
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      completed: 'bg-green-900/50 text-green-400 border-green-500/30',
      processing: 'bg-yellow-900/50 text-yellow-400 border-yellow-500/30 animate-pulse',
      failed: 'bg-red-900/50 text-red-400 border-red-500/30',
      pending: 'bg-blue-900/50 text-blue-400 border-blue-500/30'
    }
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${styles[status] || styles.pending}`}>
        {status}
      </span>
    )
  }

  const filteredTranscripts = statusFilter === 'all'
    ? transcripts
    : transcripts.filter(t => t.status === statusFilter)

  if (loading) {
    return (
      <div className="glass-panel p-8 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white">Transcription History</h2>
        <div className="flex items-center gap-3">
          <div className="relative">
             <Filter className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"/>
             <select
               value={statusFilter}
               onChange={(e) => setStatusFilter(e.target.value)}
               className="glass-panel pl-10 pr-4 py-2 rounded-lg text-white border-0 focus:ring-2 focus:ring-primary-500 appearance-none bg-gray-800/70"
             >
               <option value="all">All Status</option>
               <option value="completed">Completed</option>
               <option value="processing">Processing</option>
               <option value="failed">Failed</option>
               <option value="pending">Pending</option>
             </select>
          </div>
          <button
            onClick={() => fetchTranscripts()} // Explicitly show loading on manual refresh
            className="btn-secondary flex items-center gap-2"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
         <div className="glass-panel border-red-500/50 bg-red-900/20 p-4">
           <p className="text-red-400">{error}</p>
         </div>
       )}

      {filteredTranscripts.length === 0 && !error ? (
        <div className="glass-panel p-12 text-center border-dashed border-gray-700">
          <p className="text-gray-400">No transcripts found matching the filter.</p>
        </div>
      ) : (
        <div className="glass-panel overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Filename
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Language
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filteredTranscripts.map((transcript) => (
                <tr
                  key={transcript.id}
                  className="hover:bg-gray-800/30 transition-colors"
                >
                  <td className="px-6 py-4 text-sm font-medium text-white truncate max-w-xs">
                    {transcript.filename}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300">
                    {transcript.language || '-'}
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(transcript.status)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400 whitespace-nowrap">
                    {new Date(transcript.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right space-x-3 whitespace-nowrap">
                    <button
                      onClick={() => setSelectedTranscript(transcript)}
                      className="text-primary-400 hover:text-primary-300 transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4 inline" />
                    </button>
                    <button
                      onClick={() => handleDelete(transcript.id)}
                      className="text-red-400 hover:text-red-300 transition-colors"
                      title="Delete Transcript"
                    >
                      <Trash2 className="w-4 h-4 inline" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal for viewing transcript details */}
      {selectedTranscript && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50 animate-fade-in"
          onClick={() => setSelectedTranscript(null)}
        >
          <div
            className="glass-panel max-w-3xl w-full p-6 max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()} // Prevent closing modal when clicking inside
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white truncate">{selectedTranscript.filename}</h3>
              <button
                onClick={() => setSelectedTranscript(null)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
               <div>
                 <p className="text-sm text-gray-400 mb-1">Language</p>
                 <p className="text-white font-medium">{selectedTranscript.language || 'Unknown'}</p>
               </div>

               <div>
                 <p className="text-sm text-gray-400 mb-1">Status</p>
                 {getStatusBadge(selectedTranscript.status)}
               </div>

              {selectedTranscript.text && (
                <div>
                  <p className="text-sm text-gray-400 mb-2">Transcript</p>
                  <div className="glass-panel bg-gray-950/70 p-4 max-h-60 overflow-y-auto rounded-md">
                    <p className="text-gray-200 whitespace-pre-wrap">{selectedTranscript.text}</p>
                  </div>
                </div>
              )}

              {selectedTranscript.error_message && (
                <div>
                  <p className="text-sm text-gray-400 mb-2">Error Details</p>
                  <div className="glass-panel p-4 border border-red-500/50 bg-red-900/20 rounded-md">
                    <p className="text-red-400 whitespace-pre-wrap">{selectedTranscript.error_message}</p>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm pt-4 border-t border-gray-800">
                <div>
                  <p className="text-gray-400">Created</p>
                  <p className="text-white">{new Date(selectedTranscript.created_at).toLocaleString()}</p>
                </div>
                {selectedTranscript.processed_at && (
                  <div>
                    <p className="text-gray-400">Processed</p>
                    <p className="text-white">{new Date(selectedTranscript.processed_at).toLocaleString()}</p>
                  </div>
                )}
                {selectedTranscript.file_size_bytes && (
                  <div>
                    <p className="text-gray-400">File Size</p>
                    <p className="text-white">{(selectedTranscript.file_size_bytes / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                )}
                 {selectedTranscript.duration_seconds && (
                   <div>
                     <p className="text-gray-400">Duration</p>
                     <p className="text-white">{selectedTranscript.duration_seconds} seconds</p>
                   </div>
                 )}
              </div>
               <div className="flex justify-end pt-4">
                  <button
                     onClick={() => handleDelete(selectedTranscript.id)}
                     className="btn-secondary bg-red-800 hover:bg-red-700 text-red-100 flex items-center gap-2"
                   >
                     <Trash2 className="w-4 h-4" /> Delete
                   </button>
               </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
