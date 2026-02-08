import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { people } from '../data/people.js'

const heroImage =
  'https://www.figma.com/api/mcp/asset/55c25fd1-e61b-4263-a50f-2ba9d4e4bc55'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/e1cc52ac-9fe1-43fd-9bcf-79865cf93c24'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

function Profile() {
  const { id } = useParams()
  const personId = Number(id)
  const [openField, setOpenField] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchError, setSearchError] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const person = people.find((entry) => entry.id === personId)
  const profile = person ?? {
    id: personId,
    name: 'Unknown Person',
    relation: 'Unknown',
    group: 'Unassigned',
    dateAdded: 'Unknown',
    lastSeen: 'Unknown',
    status: 'Unknown',
    notes: 'No details available yet.',
    avatar: avatarPlaceholder,
  }

  const fields = useMemo(
    () => [
      { label: 'Date Added', value: profile.dateAdded },
      { label: 'Last Seen', value: profile.lastSeen },
      { label: 'Group', value: profile.group },
      { label: 'Status', value: profile.status },
      { label: 'Notes', value: profile.notes },
    ],
    [profile],
  )

  const normalizedResults = useMemo(() => {
    return searchResults.map((result, index) => {
      const label = result.label ?? result.field ?? 'Result'
      const value = result.value ?? result.summary ?? ''
      const key = result.id ?? `${label}-${index}`
      return {
        key,
        label,
        value,
      }
    })
  }, [searchResults])

  useEffect(() => {
    const trimmed = searchQuery.trim()
    if (!trimmed || Number.isNaN(personId)) {
      setSearchResults([])
      setSearchError('')
      setIsSearching(false)
      return
    }

    const controller = new AbortController()
    const endpoint = `${API_BASE_URL}/api/profile/${personId}/search`

    const runSearch = async () => {
      setIsSearching(true)
      setSearchError('')
      try {
        const response = await fetch(
          `${endpoint}?q=${encodeURIComponent(trimmed)}`,
          { signal: controller.signal },
        )
        if (!response.ok) {
          throw new Error('Search request failed.')
        }
        const data = await response.json()
        const items = Array.isArray(data) ? data : data?.results ?? []
        setSearchResults(items)
      } catch (error) {
        if (error.name === 'AbortError') {
          return
        }
        setSearchResults([])
        setSearchError('No data')
      } finally {
        setIsSearching(false)
      }
    }

    runSearch()

    return () => controller.abort()
  }, [personId, searchQuery])

  return (
    <div className="home profile">
      <div className="home__bg" aria-hidden="true">
        <img src={heroImage} alt="" />
      </div>

      <main className="home__content profile__content">
        <p className="home__greeting">Profile</p>

        <section className="home__card profile__card" aria-label="Profile">
          <div className="profile__header">
            <div className="profile__avatar" aria-hidden="true">
              <img src={profile.avatar || avatarPlaceholder} alt="" />
            </div>
            <div className="profile__identity">
              <h2 className="profile__name">{profile.name}</h2>
              <p className="profile__meta">
                {profile.relation} • ID {profile.id}
              </p>
            </div>
          </div>
          <div className="profile__search" aria-label="Profile search">
            <label className="profile__search-label" htmlFor="profileSearch">
              Search profile data
            </label>
            <form
              className="home__search profile__search-bar"
              onSubmit={(event) => event.preventDefault()}
            >
              <input
                className="home__search-input"
                id="profileSearch"
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search labels or context"
              />
              <button className="home__search-button" type="submit">
                &gt;
              </button>
            </form>
          </div>

          {searchQuery ? (
            <div className="profile__chat profile__chat--inline">
              {!isSearching && (searchError || normalizedResults.length === 0) ? (
                <div className="profile__chat-bubble profile__chat-bubble--system">
                  No data.
                </div>
              ) : null}
              {normalizedResults.map((result) => (
                <div className="profile__chat-bubble" key={result.key}>
                  <span className="profile__chat-label">{result.label}</span>
                  <span className="profile__chat-text">{result.value}</span>
                </div>
              ))}
            </div>
          ) : null}

          <div className="profile__accordions" aria-label="Profile details">
            {fields.map((field) => {
              const isOpen = openField === field.label
              return (
                <button
                  key={field.label}
                  className={`profile__accordion${isOpen ? ' profile__accordion--open' : ''}`}
                  type="button"
                  onClick={() => setOpenField(isOpen ? null : field.label)}
                  aria-expanded={isOpen}
                >
                  <span className="profile__accordion-label">{field.label}</span>
                  <span className="profile__accordion-icon">+</span>
                  {isOpen ? (
                    <span className="profile__accordion-content">
                      {field.value}
                    </span>
                  ) : null}
                </button>
              )
            })}
          </div>
        </section>
      </main>
    </div>
  )
}

export default Profile
