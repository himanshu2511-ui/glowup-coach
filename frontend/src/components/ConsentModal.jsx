import { useEffect, useState } from 'react'
import './ConsentModal.css'

export default function ConsentModal({ onAccept }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const consented = sessionStorage.getItem('glowup_consented')
    if (!consented) {
      // Small delay for dramatic entrance
      setTimeout(() => setVisible(true), 300)
    } else {
      onAccept()
    }
  }, [onAccept])

  const accept = () => {
    sessionStorage.setItem('glowup_consented', '1')
    setVisible(false)
    setTimeout(onAccept, 300)
  }

  if (!visible) return null

  return (
    <div className="consent-overlay" id="consent-modal">
      <div className="consent-card glass-card animate-fade-up">
        <div className="consent-icon">🔒</div>
        <h2 className="consent-title">Biometric Data Consent</h2>
        <p className="consent-lead">
          Before we begin, please read and agree to the following:
        </p>

        <div className="consent-items">
          {[
            { icon: '📷', title: 'Camera Access', text: 'We will access your camera to capture frames during the 30-second scan.' },
            { icon: '🔢', title: 'Data Minimization', text: 'Only numeric facial geometry metrics are stored — never your photos or video.' },
            { icon: '🗑️', title: 'No Raw Images Saved', text: 'Frames are processed in-memory and immediately discarded. We hold zero images of you.' },
            { icon: '⚕️', title: 'Not Medical Advice', text: 'Glowup Coach provides cosmetic guidance only. Always consult a qualified professional before any medical decisions.' },
            { icon: '⚧', title: 'Gender Override', text: 'You can change your gender setting at any time to apply different scoring weights.' },
          ].map((item, i) => (
            <div key={i} className="consent-item">
              <span className="consent-item-icon">{item.icon}</span>
              <div>
                <div className="consent-item-title">{item.title}</div>
                <div className="consent-item-text">{item.text}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="disclaimer-box" style={{ marginTop: 16 }}>
          By clicking "I Agree", you consent to biometric scanning of your face for aesthetic analysis purposes only. You may revoke this consent at any time by logging out.
        </div>

        <div className="consent-actions">
          <button id="btn-consent-accept" className="btn btn-primary btn-full" onClick={accept}>
            ✓ I Agree — Start Scan
          </button>
          <button
            className="btn btn-ghost"
            style={{ width: '100%' }}
            onClick={() => window.history.back()}
          >
            ✗ Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
