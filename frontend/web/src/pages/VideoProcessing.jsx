import { useEffect, useRef, useState } from 'react'
import { HERO_IMAGE, AVATAR_PLACEHOLDER } from '../utils/constants'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const UPLOAD_AUDIO_ENDPOINT = `${API_BASE_URL}/uploadAudio` // Added this

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

const getRecognitionWebSocketUrl = () => {
  if (typeof window === 'undefined') {
    return ''
  }
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const apiBase = import.meta.env.VITE_API_BASE || ''
  if (apiBase) {
    const normalized = apiBase.replace(/^http/, 'ws').replace(/\/$/, '')
    return `${normalized}/ws/recognition`
  }
  return `${protocol}://${window.location.hostname}:8000/ws/recognition`
}

function VideoProcessing() {
  const [frameSrc, setFrameSrc] = useState('')
  const [status, setStatus] = useState('Connecting to stream...')
  const [isRecording, setIsRecording] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState('Ready to record')
  const [voiceUrl, setVoiceUrl] = useState('')
  const [voiceBlob, setVoiceBlob] = useState(null)
  const [recognizedPerson, setRecognizedPerson] = useState(null)
  const urlRef = useRef('')
  const voiceUrlRef = useRef('')
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const cancelRef = useRef(false)
  const lastRecognizedIdRef = useRef('')

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

  useEffect(() => {
    const wsUrl = getRecognitionWebSocketUrl()
    if (!wsUrl) {
      return undefined
    }

    const socket = new WebSocket(wsUrl)
    let isActive = true

    socket.onmessage = async (event) => {
      let payload = null
      try {
        payload = JSON.parse(event.data)
      } catch {
        return
      }

      const contactId = payload?.contact_id
      if (!contactId || contactId === lastRecognizedIdRef.current) {
        return
      }

      lastRecognizedIdRef.current = contactId

      try {
        const response = await fetch(`${API_BASE_URL}/person/${contactId}`)
        if (!response.ok) {
          throw new Error('Recognition lookup failed')
        }
        const data = await response.json()
        if (isActive) {
          setRecognizedPerson(data)
        }
      } catch {
        if (isActive) {
          setRecognizedPerson(null)
        }
      }
    }

    socket.onerror = () => {
      if (isActive) {
        setRecognizedPerson(null)
      }
    }

    return () => {
      isActive = false
      socket.close()
    }
  }, [])

  useEffect(() => {
    return () => {
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        recorderRef.current.stop()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (voiceUrlRef.current) {
        URL.revokeObjectURL(voiceUrlRef.current)
      }
    }
  }, [])

  const startVoiceRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setVoiceStatus('Recording not supported in this browser')
      return
    }

    try {
      setVoiceStatus('Requesting microphone access...')
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const recorder = new MediaRecorder(stream)
      const chunks = []

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunks.push(event.data)
        }
      }

      recorder.onstop = () => {
        if (cancelRef.current) {
          cancelRef.current = false
          setVoiceStatus('Recording cancelled')
          setIsRecording(false)
          setVoiceBlob(null)
          if (voiceUrlRef.current) {
            URL.revokeObjectURL(voiceUrlRef.current)
            voiceUrlRef.current = ''
          }
          setVoiceUrl('')
          return
        }

        const blob = new Blob(chunks, {
          type: recorder.mimeType || 'audio/webm',
        })
        if (voiceUrlRef.current) {
          URL.revokeObjectURL(voiceUrlRef.current)
        }
        const nextUrl = URL.createObjectURL(blob)
        voiceUrlRef.current = nextUrl
        setVoiceUrl(nextUrl)
        setVoiceStatus('Sample saved')
        setVoiceBlob(blob)
        setIsRecording(false)
      }

      recorder.onerror = () => {
        setVoiceStatus('Recording error')
        setIsRecording(false)
      }

      recorderRef.current = recorder
      recorder.start()
      setIsRecording(true)
      setVoiceStatus('Recording...')
    } catch (error) {
      setVoiceStatus('Microphone access denied')
      setIsRecording(false)
    }
  }

  const stopVoiceRecording = () => {
    cancelRef.current = false
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }

  const cancelVoiceRecording = () => {
    if (isRecording) {
      cancelRef.current = true
      stopVoiceRecording()
      return
    }

    if (voiceUrlRef.current) {
      URL.revokeObjectURL(voiceUrlRef.current)
      voiceUrlRef.current = ''
    }
    setVoiceUrl('')
    setVoiceBlob(null)
    setVoiceStatus('Sample cleared')
  }

  const saveVoiceSample = async () => {
    if (!voiceBlob) {
      setVoiceStatus('No sample to send')
      return
    }
    
    // Retrieve the current user's ID
    const storedUser = localStorage.getItem('altitudeUser')
    if (!storedUser) {
      setVoiceStatus('No user logged in')
      return
    }
    let userId = ''
    try {
      const parsed = JSON.parse(storedUser)
      userId = parsed.user_id || parsed.id
    } catch {
      setVoiceStatus('Invalid user data')
      return
    }

    if (!userId) {
      setVoiceStatus('User ID missing')
      return
    }

    setVoiceStatus('Uploading sample...')
    try {
      const formData = new FormData()
      formData.append('user_id', userId)
      formData.append('file', voiceBlob, 'recording.wav')

      const response = await fetch(UPLOAD_AUDIO_ENDPOINT, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`)
      }
      
      const result = await response.json()
      setVoiceStatus('Audio saved successfully!')
      console.log('Audio uploaded:', result.url)
    } catch (error) {
      console.error(error)
      setVoiceStatus('Error uploading audio')
    }
  }

  const recognizedName = recognizedPerson
    ? `${recognizedPerson.first_name ?? ''} ${recognizedPerson.last_name ?? ''}`.trim() || 'Unknown Person'
    : 'No one recognized yet'
  const recognizedAvatar = recognizedPerson?.photo ?? AVATAR_PLACEHOLDER

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
                style={{
                  backgroundImage: `url(${recognizedAvatar})`,
                }}
              />
              <div className="video__person-details">
                <span className="video__person-label">Recognized</span>
                <span className="video__person-name">{recognizedName}</span>
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

        <section
          className="home__card video__config"
          aria-label="Voice Configuration"
        >
          <div className="video__config-header">
            <h2 className="video__config-title">Voice Configuration</h2>
            <div className="video__config-actions">
              <button
                className="video__config-save video__config-save--primary"
                type="button"
                onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
              >
                {isRecording ? 'Stop recording' : 'Record sample'}
              </button>
              <button
                className="video__config-save video__config-save--ghost"
                type="button"
                onClick={cancelVoiceRecording}
                disabled={!isRecording && !voiceUrl}
              >
                {isRecording ? 'Cancel' : 'Clear sample'}
              </button>
              <button
                className="video__config-save"
                type="button"
                onClick={saveVoiceSample}
                disabled={!voiceBlob || isRecording}
              >
                Save sample
              </button>
            </div>
          </div>

          <div className="video__config-form">
            <div className="video__config-field">
              <span>Voice sample</span>
              <p className="video__config-hint">{voiceStatus}</p>
              <div className="video__voice-player">
                {voiceUrl ? (
                  <audio controls src={voiceUrl} />
                ) : (
                  <p className="video__config-hint">
                    Record a short sample so the system can use your voice.
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default VideoProcessing
