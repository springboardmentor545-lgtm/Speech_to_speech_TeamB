import React, { useState, useEffect } from 'react';
import { Play, Pause, Settings, Network, Monitor, Smartphone, Tv, Server, Database, HardDrive } from 'lucide-react';

const Milestone4 = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTrack, setCurrentTrack] = useState('English');
  const [networkStatus, setNetworkStatus] = useState('excellent');
  const [deviceType, setDeviceType] = useState('web');

  const tracks = [
    { name: 'English', language: 'en' },
    { name: 'Spanish', language: 'es' },
    { name: 'French', language: 'fr' },
    { name: 'German', language: 'de' },
    { name: 'Hindi', language: 'hi' }
  ];

  const deviceTests = [
    { name: 'Browser Compatibility', status: 'pass', details: 'All modern browsers supported' },
    { name: 'Network Speed', status: 'pass', details: '100 Mbps available' },
    { name: 'Audio Quality', status: 'pass', details: 'High fidelity audio' },
    { name: 'Latency', status: 'pass', details: '<200ms response time' }
  ];

  const opsStatus = [
    { name: 'Backend', status: 'running', details: 'Connected to Azure services' },
    { name: 'Database', status: 'connected', details: 'PostgreSQL cluster' },
    { name: 'Render Disk', status: 'mounted', details: '/var/data mounted' },
    { name: 'FFmpeg', status: 'installed', details: 'Audio processing ready' }
  ];

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const changeTrack = (trackName) => {
    setCurrentTrack(trackName);
  };

  useEffect(() => {
    // Simulate network status
    const interval = setInterval(() => {
      setNetworkStatus(prev => {
        if (prev === 'excellent') return 'good';
        if (prev === 'good') return 'fair';
        return 'excellent';
      });
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Milestone 4: Deployment & OTT Integration</h1>
        <p className="text-gray-400">Production-ready deployment with OTT platform integration</p>
      </div>

      {/* OTT Player Preview */}
      <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
        <h2 className="text-lg font-semibold mb-4 text-white">OTT Player Preview</h2>
        
        <div className="relative bg-black rounded-lg overflow-hidden" style={{ paddingBottom: '56.25%' }}>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Play size={24} className="text-white" />
              </div>
              <p className="text-white">OTT Player Preview</p>
              <p className="text-gray-400 text-sm">Content with multilingual audio tracks</p>
            </div>
          </div>
          
          {/* Audio Track Selector */}
          <div className="absolute bottom-4 left-4 flex space-x-2">
            {tracks.map((track) => (
              <button
                key={track.name}
                onClick={() => changeTrack(track.name)}
                className={`px-3 py-1 rounded-full text-xs font-medium ${
                  currentTrack === track.name
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-700 bg-opacity-50 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {track.name}
              </button>
            ))}
          </div>
          
          {/* Play/Pause Button */}
          <div className="absolute bottom-4 right-4">
            <button
              onClick={togglePlay}
              className="w-12 h-12 bg-primary-600 hover:bg-primary-700 rounded-full flex items-center justify-center text-white"
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} />}
            </button>
          </div>
        </div>
        
        <div className="mt-4 flex justify-between items-center">
          <div className="flex space-x-4">
            <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors">
              <Settings size={16} />
              <span>Settings</span>
            </button>
            <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-colors">
              Subtitles
            </button>
          </div>
          
          <div className="text-sm text-gray-400">
            Current Track: <span className="text-white">{currentTrack}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device & Network Tests */}
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-white">Device & Network Testing</h2>
          
          <div className="space-y-3">
            {deviceTests.map((test, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                <div>
                  <div className="font-medium text-white">{test.name}</div>
                  <div className="text-sm text-gray-400">{test.details}</div>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                  test.status === 'pass' 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {test.status}
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-700">
            <h3 className="text-md font-medium text-white mb-3">Supported Devices</h3>
            <div className="flex space-x-4">
              <div className="flex flex-col items-center">
                <Monitor size={32} className="text-blue-400 mb-2" />
                <span className="text-xs text-gray-400">Web</span>
              </div>
              <div className="flex flex-col items-center">
                <Smartphone size={32} className="text-green-400 mb-2" />
                <span className="text-xs text-gray-400">Mobile</span>
              </div>
              <div className="flex flex-col items-center">
                <Tv size={32} className="text-purple-400 mb-2" />
                <span className="text-xs text-gray-400">TV</span>
              </div>
            </div>
          </div>
        </div>

        {/* Network Status */}
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-white">Network Status</h2>
          
          <div className="flex items-center space-x-4 mb-6">
            <div className={`w-3 h-3 rounded-full ${
              networkStatus === 'excellent' ? 'bg-green-500' :
              networkStatus === 'good' ? 'bg-yellow-500' : 'bg-red-500'
            }`}></div>
            <div>
              <div className="font-medium text-white capitalize">{networkStatus} Connection</div>
              <div className="text-sm text-gray-400">Optimized for real-time streaming</div>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-gray-400 mb-1">
                <span>Bandwidth</span>
                <span>100 Mbps</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '95%' }}></div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between text-sm text-gray-400 mb-1">
                <span>Latency</span>
                <span>120 ms</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '70%' }}></div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between text-sm text-gray-400 mb-1">
                <span>Packet Loss</span>
                <span>0.1%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '98%' }}></div>
              </div>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-gray-700/50 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Network size={16} className="text-blue-400" />
              <span className="font-medium text-white">OTT Integration</span>
            </div>
            <p className="text-sm text-gray-400">
              Ready for deployment to major OTT platforms with HLS/DASH streaming and WebVTT subtitles.
            </p>
          </div>
        </div>
      </div>

      {/* Deployment Status */}
      <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
        <h2 className="text-lg font-semibold mb-4 text-white">Deployment Status</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-700/50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-400">98%</div>
            <div className="text-sm text-gray-400">Uptime</div>
          </div>
          <div className="bg-gray-700/50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-400">12+</div>
            <div className="text-sm text-gray-400">Languages</div>
          </div>
          <div className="bg-gray-700/50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-yellow-400">1000+</div>
            <div className="text-sm text-gray-400">Concurrent Users</div>
          </div>
          <div className="bg-gray-700/50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-purple-400">24/7</div>
            <div className="text-sm text-gray-400">Support</div>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opsStatus.map((status, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  status.status === 'running' || status.status === 'connected' || status.status === 'mounted' || status.status === 'installed' 
                    ? 'bg-green-500' 
                    : 'bg-red-500'
                }`}></div>
                <span className="text-sm text-gray-400">{status.name}: </span>
                <span className="text-sm text-white">{status.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Milestone4;
