import { useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'

const heroImage =
  'https://www.figma.com/api/mcp/asset/5209dc40-ce81-4fc3-9083-2774e5934491'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/b0db9ac1-bd8f-4d55-97c9-c6dce409929a'

const results = [
  { id: 1, name: 'First Last', relation: 'Relationship' },
  { id: 2, name: 'First Last', relation: 'Relationship' },
  { id: 3, name: 'First Last', relation: 'Relationship' },
  { id: 4, name: 'First Last', relation: 'Relationship' },
  { id: 5, name: 'First Last', relation: 'Relationship' },
  { id: 6, name: 'First Last', relation: 'Relationship' },
]

function SearchQuery() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const timeoutRef = useRef(0)

  useEffect(() => {
    setQuery(searchParams.get('q') ?? '')
  }, [searchParams])

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

      <main className="home__content">
        <p className="home__greeting">Search Results</p>

        <form
          className="home__search"
          aria-label="Search Query"
          onSubmit={handleSubmit}
        >
          <input
            className="home__search-input"
            type="text"
            name="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search people, dates, and more"
            aria-label="Search"
          />
          <button className="home__search-button" type="submit">
            &gt;
          </button>
          {isSearching ? <span className="home__search-progress" /> : null}
        </form>

        <section className="home__card" aria-label="People">
          <h2 className="home__card-title">People</h2>

          <div className="home__rows">
            {results.map((row) => (
              <div className="home__row" key={row.id}>
                <img
                  className="home__avatar"
                  src={avatarPlaceholder}
                  alt=""
                  aria-hidden="true"
                />
                <span className="home__row-name">{row.name}</span>
                <span className="home__row-relation">{row.relation}</span>
                <button className="home__row-more" type="button">
                  More +
                </button>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default SearchQuery
