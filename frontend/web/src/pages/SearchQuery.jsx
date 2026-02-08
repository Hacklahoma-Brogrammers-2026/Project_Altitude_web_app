import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

const heroImage =
  'https://www.figma.com/api/mcp/asset/5209dc40-ce81-4fc3-9083-2774e5934491'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/b0db9ac1-bd8f-4d55-97c9-c6dce409929a'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const SEARCH_USER_ENDPOINT = `${API_BASE_URL}/api/searchUser`
const SEARCH_INFO_ENDPOINT = `${API_BASE_URL}/api/searchInfo`

function SearchQuery() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState([])
  const [errorMessage, setErrorMessage] = useState('')
  const queryParam = searchParams.get('q') ?? ''
  const modeParam = searchParams.get('mode') ?? 'users'
  const searchMode = modeParam === 'info' ? 'info' : 'users'

  const normalizedResults = useMemo(() => {
    return results.map((row, index) => {
      const name = row.name ?? row.fullName ?? 'Unknown'
      const relation = row.label ?? row.relation ?? row.group ?? 'Person'
      const id = row.id ?? row.personId ?? `${name}-${index}`
      return {
        id,
        name,
        relation,
        avatar: row.avatar,
      }
    })
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
        const endpoint =
          searchMode === 'info' ? SEARCH_INFO_ENDPOINT : SEARCH_USER_ENDPOINT
        const response = await fetch(
          `${endpoint}?q=${encodeURIComponent(trimmed)}`,
          { signal: controller.signal }
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
  }, [queryParam, searchMode])

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
                  src={row.avatar || avatarPlaceholder}
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
