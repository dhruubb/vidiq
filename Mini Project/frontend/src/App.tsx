import React, { useMemo, useState, useEffect, useRef } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { Login } from './pages/Login'
import './styles.css'

type Clip = {
  filename: string
  final_score: number
  thumbnail_name: string
  face_count: number
  unique_face_count: number
}

const API_BASE = 'http://localhost:8000/api'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  return token ? <>{children}</> : <Navigate to="/login" />
}

function Dashboard() {
  const [files, setFiles] = useState<File[]>([])
  const [jobId, setJobId] = useState<string | null>(() => localStorage.getItem('jobId') || null)
  const [results, setResults] = useState<Clip[]>([])
  const [blurWeight, setBlurWeight] = useState(0.34)
  const [motionWeight, setMotionWeight] = useState(0.33)
  const [faceWeight, setFaceWeight] = useState(0.33)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [pollInterval, setPollInterval] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [downloadCount, setDownloadCount] = useState(5)
  const [previewVideo, setPreviewVideo] = useState<string | null>(null)
  const navigate = useNavigate()

  const totalWeight = useMemo(() => blurWeight + motionWeight + faceWeight, [blurWeight, motionWeight, faceWeight])

  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [pollInterval])

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  async function uploadAndAnalyze(selectedFiles: File[]) {
    try {
      setError(null)
      setIsUploading(true)
      setUploadProgress(0)

      const form = new FormData()
      selectedFiles.forEach(f => form.append('files', f))
      form.append('blur_weight', String(blurWeight))
      form.append('motion_weight', String(motionWeight))
      form.append('face_weight', String(faceWeight))

      form.append('face_weight', String(faceWeight))

      const token = localStorage.getItem('token')
      const xhr = new XMLHttpRequest()
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          setUploadProgress((e.loaded / e.total) * 100)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status === 401) {
          handleLogout()
          return
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          const data = JSON.parse(xhr.responseText)
          setJobId(data.job_id)
          localStorage.setItem('jobId', data.job_id)
          setIsUploading(false)
          setUploadProgress(100)
          pollResults(data.job_id)
        } else {
          setIsUploading(false)
          setError('Upload failed')
        }
      })

      xhr.open('POST', `${API_BASE}/upload-files`)
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      xhr.send(form)
    } catch (err) {
      setIsUploading(false)
      setError('Upload failed')
    }
  }

  async function pollResults(jid: string) {
    setIsAnalyzing(true)
    const intervalId = window.setInterval(async () => {
      try {
        const token = localStorage.getItem('token')
        const res = await fetch(`${API_BASE}/results/${jid}`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        })
        if (res.status === 401) {
          handleLogout()
          return
        }
        if (res.ok) {
          const data = await res.json()
          if (data.results && data.results.length > 0) {
            clearInterval(intervalId)
            setResults(data.results)
            setIsAnalyzing(false)
          }
        }
      } catch (err) {
        console.error(err)
      }
    }, 2000)
    setPollInterval(intervalId)
  }

  const onDownloadTop = async () => {
    if (!jobId || results.length === 0) return
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`${API_BASE}/download-top/${jobId}?k=${downloadCount}`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })
      if (res.status === 401) {
        handleLogout()
        return
      }
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `top_${downloadCount}_clips.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError('Download failed')
    }
  }

  return (
    <div className="app-container">
      <div className="app-header flex justify-between items-center">
        <div>
          <h1 className="app-title">🎬 Video Clip Selection Platform</h1>
          <p className="app-subtitle">AI-Powered Video Quality Analysis & Ranking</p>
        </div>
        <button onClick={handleLogout} className="text-sm bg-red-600 px-3 py-1 rounded hover:bg-red-700">Logout</button>
      </div>

      <div className="card">
        <div
          className={`upload-area ${isDragging ? 'dragover' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setIsDragging(false)
            setFiles(Array.from(e.dataTransfer.files))
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <span className="upload-icon">📁</span>
          <div className="upload-text">Drag & Drop Videos Here</div>
          <input
            ref={fileInputRef}
            type="file"
            className="file-input"
            multiple
            accept="video/*"
            onChange={(e) => e.target.files && setFiles(Array.from(e.target.files))}
          />
        </div>

        {files.length > 0 && (
          <div className="file-list">
            {files.map((f, i) => <div key={i} className="file-item">{f.name}</div>)}
          </div>
        )}

        {isUploading && (
          <div className="upload-progress-container">
            <div className="upload-progress-bar">
              <div className="upload-progress-fill" style={{ width: `${uploadProgress}%` }}></div>
            </div>
          </div>
        )}

        <div className="weight-sliders">
          <WeightSlider label="Sharpness" value={blurWeight} onChange={setBlurWeight} />
          <WeightSlider label="Stability" value={motionWeight} onChange={setMotionWeight} />
          <WeightSlider label="Faces" value={faceWeight} onChange={setFaceWeight} />
        </div>

        <button
          className="btn btn-primary w-full mt-4"
          disabled={files.length === 0 || isAnalyzing || isUploading}
          onClick={() => uploadAndAnalyze(files)}
        >
          {isAnalyzing ? 'Analyzing...' : '🚀 Analyze Videos'}
        </button>
      </div>

      <div className="results-section">
        <div className="results-header flex items-center gap-4">
          <h2 className="results-title">📊 Results</h2>
          <div className="flex items-center gap-2">
            <label>Download Top:</label>
            <input
              type="number"
              min="1"
              max={results.length || 5}
              value={downloadCount}
              onChange={(e) => setDownloadCount(parseInt(e.target.value))}
              className="w-16 p-1 rounded bg-gray-700 border border-gray-600"
            />
            <button className="btn btn-secondary" onClick={onDownloadTop} disabled={!jobId}>
              ⬇️ Download
            </button>
          </div>
        </div>

        <div className="results-grid">
          {results.map((r, idx) => (
            <div key={idx} className="result-card" onClick={() => setPreviewVideo(r.filename)}>
              <img
                src={`${API_BASE}/thumbnail/${jobId}/${r.thumbnail_name}?token=${localStorage.getItem('token')}`}
                className="result-thumbnail cursor-pointer"
                alt={r.filename}
              />
              <div className="result-info">
                <div className="result-filename">{r.filename}</div>
                <div className="result-meta">
                  <span>⭐ {r.final_score.toFixed(2)}</span>
                  <span>👤 {r.face_count} (Unique: {r.unique_face_count})</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {previewVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50" onClick={() => setPreviewVideo(null)}>
          <div className="bg-gray-900 p-4 rounded-lg max-w-4xl w-full" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between mb-2">
              <h3 className="text-xl font-bold">{previewVideo}</h3>
              <button onClick={() => setPreviewVideo(null)}>✕</button>
            </div>
            <div className="aspect-video bg-black flex items-center justify-center">
              <video
                src={`${API_BASE}/video/${jobId}/${previewVideo}?token=${localStorage.getItem('token')}`}
                controls
                autoPlay
                className="w-full h-full"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function WeightSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="weight-slider">
      <div className="weight-slider-label">
        <span>{label}</span>
        <span>{value.toFixed(2)}</span>
      </div>
      <input
        type="range"
        min={0}
        max={1}
        step={0.01}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="weight-slider-input"
      />
    </div>
  )
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      </Routes>
    </Router>
  )
}
