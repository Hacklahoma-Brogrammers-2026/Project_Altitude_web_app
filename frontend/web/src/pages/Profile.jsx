import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { normalizePerson } from '../utils/transform'
import { HERO_IMAGE, AVATAR_PLACEHOLDER } from '../utils/constants'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const fallbackProfile = {
  contact_id: 'demo-001',
  first_name: 'Ashley',
  last_name: 'Carter',
  note: 'Friendly and easy to recognize. Prefers afternoon updates.',
  photo: AVATAR_PLACEHOLDER,
  notes: [
    {
      label: 'Last Seen',
      content: 'Today, 3:12 PM',
    },
    {
      label: 'Group',
      content: 'Family',
    },
    {
      label: 'Status',
      content: 'Active',
    },
  ],
}

function Profile() {
  const { id } = useParams()
  const personId = Number(id)
  const [openField, setOpenField] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchError, setSearchError] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [profileData, setProfileData] = useState(null)
  const [isProfileLoading, setIsProfileLoading] = useState(false)
  const [profileError, setProfileError] = useState('')

  const profile = useMemo(() => {
    if (!profileData) {
      return null
    }
    const normalized = normalizePerson(profileData, personId)
    // Ensure avatar uses placeholder if missing, though normalizePerson handles it if passed null,
    // we want to ensure fallback to constant if null in normalized.
    // Actually normalizePerson returns whatever is in the properties.
    // Let's rely on normalizePerson and then apply fallback if needed, or pass fallback logic to normalizePerson?
    // The previous code had complex fallback chain culminating in avatarPlaceholder.
    // normalizePerson: person.photo ?? person.photo_url ?? person.image ?? person.avatar
    // If all null, it returns undefined/null.
    return {
      ...normalized,
      avatar: normalized.avatar ?? AVATAR_PLACEHOLDER,
    }
  }, [profileData, personId])

  const fields = useMemo(() => {
    const data = profileData ?? {}
    const notes =
      data.notes ??
      data.contact_notes ??
      data.contactNotes ??
      data.note_entries ??
      []

    if (Array.isArray(notes) && notes.length > 0) {
      return notes.map((note, index) => ({
        label: note.label ?? `Note ${index + 1}`,
        value: note.content ?? note.note ?? '',
      }))
    }

    return []
  }, [profileData])

  useEffect(() => {
    if (Number.isNaN(personId)) {
      setProfileData(null)
      setProfileError('Invalid profile id.')
      setIsProfileLoading(false)
      return
    }

    const controller = new AbortController()
    const endpoint = `${API_BASE_URL}/api/getPerson/${personId}`

    const loadProfile = async () => {
      setIsProfileLoading(true)
      setProfileError('')
      try {
        const response = await fetch(endpoint, { signal: controller.signal })
        if (!response.ok) {
          throw new Error('Profile request failed.')
        }
        const data = await response.json()
        setProfileData(data)
      } catch (error) {
        if (error.name === 'AbortError') {
          return
        }
        setProfileData(fallbackProfile)
        setProfileError('')
      } finally {
        setIsProfileLoading(false)
      }
    }

    loadProfile()

    return () => controller.abort()
  }, [personId])

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
        <img src={HERO_IMAGE} alt="" />
      </div>

      <main className="home__content profile__content">
        <p className="home__greeting">Profile</p>

        <section className="home__card profile__card" aria-label="Profile">
          {isProfileLoading ? (
            <p className="home__status">Loading profile…</p>
          ) : null}
          {!isProfileLoading && profileError ? (
            <p className="home__status home__status--error">{profileError}</p>
          ) : null}

          {!isProfileLoading && !profileError && profile ? (
            <>
              <div className="profile__header">
                <div className="profile__avatar" aria-hidden="true">
                  <img src={profile.avatar || avatarPlaceholder} alt="" />
                </div>
                <div className="profile__identity">
                  <h2 className="profile__name">{profile.name}</h2>
                  <p className="profile__meta">
                    ID {profile.id}
                  </p>
                  {profile.summary ? (
                    <p className="profile__summary">{profile.summary}</p>
                  ) : null}
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
            </>
          ) : null}
        </section>
      </main>
    </div>
  )
}

export default Profile
