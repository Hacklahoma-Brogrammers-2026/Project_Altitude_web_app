import { Link, useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

const heroImage =
  'https://www.figma.com/api/mcp/asset/55c25fd1-e61b-4263-a50f-2ba9d4e4bc55'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/e1cc52ac-9fe1-43fd-9bcf-79865cf93c24'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

function Home() {
  const [query, setQuery] = useState('')
  const [people, setPeople] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [searchMode, setSearchMode] = useState('users')
  const navigate = useNavigate()

  const latestPeople = useMemo(() => {
    return people.map((person, index) => {
      const id = person.contact_id ?? person.id ?? `${index}`
      const name = `${person.first_name ?? ''} ${person.last_name ?? ''}`.trim()
      return {
        id,
        name: name || 'Unknown Person',
        avatar: person.photo ?? person.photo_url ?? person.image ?? person.avatar,
      }
    })
  }, [people])

  useEffect(() => {
    const controller = new AbortController()
    const endpoint = `${API_BASE_URL}/api/getPeople?sort=last_modified`

    const loadPeople = async () => {
      setIsLoading(true)
      setErrorMessage('')
      try {
        const response = await fetch(endpoint, { signal: controller.signal })
        if (!response.ok) {
          throw new Error('Request failed')
        }
        const data = await response.json()
        const items = Array.isArray(data) ? data : data?.results ?? []
        setPeople(items)
      } catch (error) {
        if (error.name === 'AbortError') {
          return
        }
        setPeople([])
        setErrorMessage('Unable to load people.')
      } finally {
        setIsLoading(false)
      }
    }

    loadPeople()

    return () => controller.abort()
  }, [])

  const handleSubmit = (event) => {
    event.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) {
      return
    }
    navigate(
      `/search?q=${encodeURIComponent(trimmed)}&mode=${encodeURIComponent(
        searchMode,
      )}`,
    )
  }

  return (
    <div className="home">
      <div className="home__bg" aria-hidden="true">
        <img src={heroImage} alt="" />
      </div>

      <main className="home__content home__content--center">
        <div className="home__header-row">
          <p className="home__greeting">Hi, Ashley!</p>
          <div className="home__toggle-group">
            <span className="home__toggle-label">Search mode</span>
            <div className="home__toggle" role="group" aria-label="Search mode">
            <button
              className={`home__toggle-button${
                searchMode === 'users' ? ' home__toggle-button--active' : ''
              }`}
              type="button"
              aria-pressed={searchMode === 'users'}
              onClick={() => setSearchMode('users')}
            >
              Users
            </button>
            <button
              className={`home__toggle-button${
                searchMode === 'info' ? ' home__toggle-button--active' : ''
              }`}
              type="button"
              aria-pressed={searchMode === 'info'}
              onClick={() => setSearchMode('info')}
            >
              Notes
            </button>
            </div>
          </div>
        </div>

        <form className="home__search" onSubmit={handleSubmit}>
          <input
            className="home__search-input"
            type="text"
            name="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Look up people, dates, and other information!"
            aria-label="Search"
          />
          <button className="home__search-button" type="submit">
            &gt;
          </button>
        </form>

        <section className="home__card" aria-label="Latest Data">
          <div className="home__card-header">
            <h2 className="home__card-title">Latest Data</h2>
            <Link className="home__see-all home__see-all-link" to="/people">
              See all
            </Link>
          </div>

          {isLoading ? <p className="home__status">Loading people…</p> : null}
          {!isLoading && errorMessage ? (
            <p className="home__status home__status--error">{errorMessage}</p>
          ) : null}

          <div className="home__latest-grid">
            {latestPeople.map((row) => (
              <Link
                className="home__latest-item home__latest-link"
                key={row.id}
                to={`/profile/${row.id}`}
              >
                <img
                  className="home__latest-avatar"
                  src={row.avatar || avatarPlaceholder}
                  alt=""
                  aria-hidden="true"
                />
                <span className="home__latest-name">{row.name}</span>
              </Link>
            ))}
          </div>
        </section>

        <section className="home__card" aria-label="Don’t Forget">
          <h2 className="home__card-title">Don’t Forget...</h2>

          <div className="home__chips">
            <button className="home__chip" type="button">
              Birthdays
            </button>
            <button className="home__chip" type="button">
              Colleagues
            </button>
            <button className="home__chip" type="button">
              Add More +
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default Home
