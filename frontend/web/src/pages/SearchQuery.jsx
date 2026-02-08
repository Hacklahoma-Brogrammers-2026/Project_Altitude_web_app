import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useLayoutEffect, useMemo, useState } from 'react'
import { normalizePerson } from '../utils/transform'
import { HERO_IMAGE, AVATAR_PLACEHOLDER } from '../utils/constants'
import { searchUsers, searchInfo } from '../utils/api'

function SearchQuery() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const queryParam = searchParams.get('q') ?? ''
  const modeParam = searchParams.get('mode') ?? 'users'
  const searchMode = modeParam === 'info' ? 'info' : 'users'
  
  const [query, setQuery] = useState('')
  // Initialize isSearching to true if there's a query param, so it shows immediately on mount
  const [isSearching, setIsSearching] = useState(!!queryParam)
  const [results, setResults] = useState(null) // Initialize as null to indicate "not fetched"
  const [errorMessage, setErrorMessage] = useState('')

  const normalizedResults = useMemo(() => {
    return (results || []).map(normalizePerson)
  }, [results])

  // Ensure loading state is active immediately when constraints change
  // This prevents a "flash" of empty state before the fetch effect kicks in
  useLayoutEffect(() => {
    if (queryParam.trim()) {
      setIsSearching(true)
      // When query changes, reset results to null to prevent "No results" from showing based on old data
      // or during the loading phase.
      if (queryParam !== query) { 
         setResults(null)
      }
    }
  }, [queryParam, searchMode])

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
        const items =
          searchMode === 'info'
            ? await searchInfo(trimmed, controller.signal)
            : await searchUsers(trimmed, controller.signal)

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

          {isSearching ? (
            <div
              className="home__results-progress"
              role="progressbar"
              aria-label="Searching"
              aria-busy="true"
            />
          ) : null}
          {errorMessage ? (
            <p className="home__status home__status--error">{errorMessage}</p>
          ) : null}
          {!errorMessage && !isSearching && results !== null && queryParam.trim() &&
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
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span className="home__row-relation">{row.relation}</span>
                  {row.summary ? (
                    <span className="home__row-summary">{row.summary}</span>
                  ) : null}
                </div>
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
