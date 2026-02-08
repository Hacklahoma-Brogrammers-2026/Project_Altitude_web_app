import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { normalizePerson } from '../utils/transform'
import { HERO_IMAGE, AVATAR_PLACEHOLDER } from '../utils/constants'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const SEARCH_ENDPOINT = `${API_BASE_URL}/api/search`

function SearchQuery() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState([])
  const [errorMessage, setErrorMessage] = useState('')
  const queryParam = searchParams.get('q') ?? ''

  const normalizedResults = useMemo(() => {
    return results.map(normalizePerson)
  }, [results])

  useEffect(() => {
    setQuery(queryParam)
  }, [queryParam])

  useEffect(() => {
    const trimmed = queryParam.trim()
    if (!trimmed) {
      setResults([])
      setErrorMessage('')
      setIsSearching(false)
      return
    }

    const controller = new AbortController()

    const runSearch = async () => {
      setIsSearching(true)
      setErrorMessage('')
      try {
        const response = await fetch(
          `${SEARCH_ENDPOINT}?q=${encodeURIComponent(trimmed)}`,
          {
            signal: controller.signal,
          }
        )
        if (!response.ok) {
          throw new Error('Search request failed.')
        }
        const data = await response.json()
        const items = Array.isArray(data) ? data : data?.results ?? []
        setResults(items)
      } catch (error) {
        if (error.name === 'AbortError') {
          return
        }
        setResults([])
        setErrorMessage('Unable to fetch results. Please try again.')
      } finally {
        setIsSearching(false)
      }
    }

    runSearch()

    return () => controller.abort()
  }, [queryParam])

  const handleSubmit = (event) => {
    event.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) {
      return
    }
    navigate(`/search?q=${encodeURIComponent(trimmed)}`)
  }

  return (
    <div className="home">
      <div className="home__bg" aria-hidden="true">
        <img src={HERO_IMAGE} alt="" />
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

          {errorMessage ? (
            <p className="home__status home__status--error">{errorMessage}</p>
          ) : null}
          {!errorMessage && !isSearching && queryParam.trim() &&
          normalizedResults.length === 0 ? (
            <p className="home__status">No results found.</p>
          ) : null}

          <div className="home__rows">
            {normalizedResults.map((row) => (
              <Link
                className="home__row home__row-link"
                key={row.id}
                to={`/profile/${row.id}`}
              >
                <img
                  className="home__avatar"
                  src={row.avatar || AVATAR_PLACEHOLDER}
                  alt=""
                  aria-hidden="true"
                />
                <span className="home__row-name">{row.name}</span>
                <span className="home__row-relation">{row.relation}</span>
                <span className="home__row-more">More +</span>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default SearchQuery
