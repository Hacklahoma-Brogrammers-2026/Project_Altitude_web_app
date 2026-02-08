import { NavLink, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useState } from 'react'
import './App.css'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import PersonDatabase from './pages/PersonDatabase.jsx'
import Profile from './pages/Profile.jsx'
import SearchQuery from './pages/SearchQuery.jsx'
import SignUp from './pages/SignUp.jsx'
import VideoProcessing from './pages/VideoProcessing.jsx'

function AppLayout() {
  const [navOpen, setNavOpen] = useState(false)

  const handleToggle = () => {
    setNavOpen((prev) => !prev)
  }

  const handleNavClick = () => {
    setNavOpen(false)
  }

  return (
    <div className="app-shell">
      <aside
        className={`app-nav${navOpen ? ' app-nav--open' : ''}`}
        aria-label="Primary"
      >
        <div className="app-nav__top">
          <NavLink className="app-nav__brand" to="/home" onClick={handleNavClick}>
            Altitude
          </NavLink>
          <button
            className="app-nav__toggle"
            type="button"
            onClick={handleToggle}
            aria-expanded={navOpen}
            aria-controls="primary-navigation"
            aria-label="Toggle navigation"
          >
            <span className="app-nav__toggle-line" />
            <span className="app-nav__toggle-line" />
            <span className="app-nav__toggle-line" />
          </button>
        </div>
        <nav className="app-nav__links" id="primary-navigation">
          <NavLink className="app-nav__link" to="/home" onClick={handleNavClick}>
            Home
          </NavLink>
          <NavLink
            className="app-nav__link"
            to="/people"
            onClick={handleNavClick}
          >
            Person Database
          </NavLink>
          <NavLink
            className="app-nav__link"
            to="/video-processing"
            onClick={handleNavClick}
          >
            Video Processing
          </NavLink>
        </nav>
        <div className="app-nav__footer">
          <NavLink
            className="app-nav__link app-nav__logout"
            to="/login"
            onClick={handleNavClick}
          >
            Log out
          </NavLink>
        </div>
      </aside>

      <div className="app-main">
        <Outlet />
      </div>
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<SignUp />} />
      <Route element={<AppLayout />}>
        <Route path="/home" element={<Home />} />
        <Route path="/people" element={<PersonDatabase />} />
        <Route path="/profile/:id" element={<Profile />} />
        <Route path="/search" element={<SearchQuery />} />
        <Route path="/video-processing" element={<VideoProcessing />} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
