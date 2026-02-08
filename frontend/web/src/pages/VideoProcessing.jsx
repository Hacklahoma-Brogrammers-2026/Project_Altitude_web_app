import { useEffect, useRef, useState } from 'react'
import { HERO_IMAGE } from '../utils/constants'

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
        <img src={HERO_IMAGE} alt="" />
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
          aria-label="LLM Configuration"
        >
          <div className="video__config-header">
            <h2 className="video__config-title">LLM Configuration</h2>
            <button className="video__config-save" type="submit" form="llmConfig">
              Send
            </button>
          </div>

          <form className="video__config-form" id="llmConfig">
            <label className="video__config-field" htmlFor="llmPrompt">
              Configuration Prompt
              <textarea
                className="video__config-textarea"
                id="llmPrompt"
                name="llmPrompt"
                rows={4}
                placeholder="Describe how the model should configure video processing..."
              />
            </label>
            <p className="video__config-hint">
              This will be sent to the configuration service once wired up.
            </p>
          </form>
        </section>
      </main>
    </div>
  )
}

export default VideoProcessing
