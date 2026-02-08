import { useEffect, useRef, useState } from 'react'

const heroImage =
  'https://www.figma.com/api/mcp/asset/55c25fd1-e61b-4263-a50f-2ba9d4e4bc55'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/e1cc52ac-9fe1-43fd-9bcf-79865cf93c24'

const getWebSocketUrl = () => {
  if (typeof window === 'undefined') {
    return ''
  }
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const apiBase = import.meta.env.VITE_API_BASE || ''
  if (apiBase) {
    const normalized = apiBase.replace(/^http/, 'ws').replace(/\/$/, '')
    return `${normalized}/ws/video-consumer`
  }
  return `${protocol}://${window.location.hostname}:8000/ws/video-consumer`
}

function VideoProcessing() {
  const [frameSrc, setFrameSrc] = useState('')
  const [status, setStatus] = useState('Connecting to stream...')
  const urlRef = useRef('')

  useEffect(() => {
    const wsUrl = getWebSocketUrl()
    if (!wsUrl) {
      return undefined
    }

    const socket = new WebSocket(wsUrl)
    socket.binaryType = 'blob'

    socket.onopen = () => {
      setStatus('Live stream')
    }

    socket.onmessage = (event) => {
      const blob = event.data
      const nextUrl = URL.createObjectURL(blob)
      if (urlRef.current) {
        URL.revokeObjectURL(urlRef.current)
      }
      urlRef.current = nextUrl
      setFrameSrc(nextUrl)
    }

    socket.onerror = () => {
      setStatus('Stream error')
    }

    socket.onclose = () => {
      setStatus('Stream disconnected')
    }

    return () => {
      socket.close()
      if (urlRef.current) {
        URL.revokeObjectURL(urlRef.current)
      }
    }
  }, [])

  return (
    <div className="home video">
      <div className="home__bg" aria-hidden="true">
        <img src={heroImage} alt="" />
      </div>

      <main className="home__content video__content">
        <p className="home__greeting">Video Processing</p>

        <section className="home__card video__card" aria-label="Video Processing">
          <div className="video__layout">
            <div className="video__feed" aria-label="Camera feed">
              {frameSrc ? (
                <img className="video__feed-image" src={frameSrc} alt="" />
              ) : null}
              <span className="video__feed-label">Camera Feed</span>
              <span className="video__feed-status">{status}</span>
            </div>

            <div className="video__person">
              <div
                className="video__person-avatar"
                role="img"
                aria-label="Recognized person"
              />
              <div className="video__person-details">
                <span className="video__person-label">Recognized</span>
                <span className="video__person-name">First Last</span>
              </div>
            </div>
          </div>
        </section>

        <section
          className="home__card video__config"
          aria-label="Data Collection Configuration"
        >
          <div className="video__config-header">
            <h2 className="video__config-title">Configurations</h2>
            <button className="video__config-save" type="button">
              Save
            </button>
          </div>

          <div className="video__config-grid">
            <label className="video__config-field">
              Capture Interval
              <select className="video__config-select" defaultValue="5s">
                <option value="1s">Every 1s</option>
                <option value="5s">Every 5s</option>
                <option value="10s">Every 10s</option>
              </select>
            </label>
            <label className="video__config-field">
              Recognition Mode
              <select className="video__config-select" defaultValue="balanced">
                <option value="balanced">Balanced</option>
                <option value="fast">Fast</option>
                <option value="accurate">High accuracy</option>
              </select>
            </label>
            <label className="video__config-field">
              Store Snapshots
              <select className="video__config-select" defaultValue="on">
                <option value="on">On</option>
                <option value="off">Off</option>
              </select>
            </label>
            <label className="video__config-field">
              Data Retention
              <select className="video__config-select" defaultValue="30d">
                <option value="7d">7 days</option>
                <option value="30d">30 days</option>
                <option value="90d">90 days</option>
              </select>
            </label>
          </div>
        </section>
      </main>
    </div>
  )
}

export default VideoProcessing
