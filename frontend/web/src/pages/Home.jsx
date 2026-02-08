import { Link, useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'

const heroImage =
  'https://www.figma.com/api/mcp/asset/55c25fd1-e61b-4263-a50f-2ba9d4e4bc55'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/e1cc52ac-9fe1-43fd-9bcf-79865cf93c24'

const latestRows = [
  { id: 1, name: 'First Last' },
  { id: 2, name: 'First Last' },
  { id: 3, name: 'First Last' },
  { id: 4, name: 'First Last' },
  { id: 5, name: 'First Last' },
  { id: 6, name: 'First Last' },
]

function Home() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const navigate = useNavigate()
  const timeoutRef = useRef(0)

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  const handleSubmit = (event) => {
    event.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) {
      return
    }
    setIsSearching(true)
    timeoutRef.current = window.setTimeout(() => {
      setIsSearching(false)
      navigate(`/search?q=${encodeURIComponent(trimmed)}`)
    }, 700)
  }

  return (
    <div className="home">
      <div className="home__bg" aria-hidden="true">
        <img src={heroImage} alt="" />
      </div>

      <main className="home__content home__content--center">
        <p className="home__greeting">Hi, Ashley!</p>

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
          {isSearching ? <span className="home__search-progress" /> : null}
        </form>

        <section className="home__card" aria-label="Latest Data">
          <div className="home__card-header">
            <h2 className="home__card-title">Latest Data</h2>
            <Link className="home__see-all home__see-all-link" to="/people">
              See all
            </Link>
          </div>

          <div className="home__latest-grid">
            {latestRows.map((row) => (
              <div className="home__latest-item" key={row.id}>
                <img
                  className="home__latest-avatar"
                  src={avatarPlaceholder}
                  alt=""
                  aria-hidden="true"
                />
                <span className="home__latest-name">{row.name}</span>
              </div>
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
