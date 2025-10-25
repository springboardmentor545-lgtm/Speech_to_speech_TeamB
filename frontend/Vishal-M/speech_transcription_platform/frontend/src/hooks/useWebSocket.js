import { useEffect, useRef, useState, useCallback } from 'react'

export function useWebSocket(url, options = {}) {
  const { onOpen, onMessage, onError, onClose } = options;
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)

  const connect = useCallback(() => {
    if (!url || wsRef.current) return // Don't connect if no URL or already connected/connecting

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      console.log(`WebSocket connected to ${url}`);
      setIsConnected(true)
      onOpen?.()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLastMessage(data)
        onMessage?.(data)
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
        // Handle non-JSON messages or errors if necessary
      }
    }

    ws.onerror = (error) => {
      console.error(`WebSocket error on ${url}:`, error)
      onError?.(error)
      // Consider adding automatic reconnection logic here if needed
    }

    ws.onclose = (event) => {
      console.log(`WebSocket disconnected from ${url}. Code: ${event.code}, Reason: ${event.reason}`);
      setIsConnected(false)
      wsRef.current = null // Clear ref on close
      onClose?.(event)
      // Consider adding automatic reconnection logic here if needed
    }
  }, [url, onOpen, onMessage, onError, onClose]);


  const disconnect = useCallback(() => {
     if (wsRef.current) {
        console.log(`Closing WebSocket connection to ${url}`);
        wsRef.current.close();
        // State updates (isConnected=false, wsRef=null) happen in the onclose handler
     }
  }, [url]);

  // Effect to connect on mount (if url is provided) and disconnect on unmount
  useEffect(() => {
    connect(); // Attempt connection when URL changes or component mounts

    return () => {
      disconnect(); // Disconnect when component unmounts or URL changes
    }
  }, [connect, disconnect]) // Depend on memoized connect/disconnect

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
        console.warn("WebSocket not open. Cannot send message.");
    }
  }, []);

  const sendBinary = useCallback((data) => {
     if (wsRef.current?.readyState === WebSocket.OPEN) {
       wsRef.current.send(data)
     } else {
         console.warn("WebSocket not open. Cannot send binary data.");
     }
   }, []);

  return { isConnected, lastMessage, sendMessage, sendBinary, connect, disconnect }
}
