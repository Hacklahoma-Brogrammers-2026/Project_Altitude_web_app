import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { normalizePerson } from '../utils/transform'
import { fetchPeople } from '../utils/api'
import { HERO_IMAGE, AVATAR_PLACEHOLDER } from '../utils/constants'

// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '' // Removed, used in api.js

function PersonDatabase() {
  const pageSize = 15
  const [currentPage, setCurrentPage] = useState(1)
  const [people, setPeople] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [sortFilter, setSortFilter] = useState('last_modified')

  const totalPages = Math.max(1, Math.ceil(people.length / pageSize))

  const normalizedPeople = useMemo(() => {
    return people.map(normalizePerson)
  }, [people])

  const pageItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return normalizedPeople.slice(start, start + pageSize)
  }, [currentPage, normalizedPeople])

  useEffect(() => {
    const controller = new AbortController()

    const loadPeople = async () => {
      setIsLoading(true)
      setErrorMessage('')
      try {
        const items = await fetchPeople({ 
            signal: controller.signal, 
            sort: sortFilter 
        })
        setPeople(items)
        setCurrentPage(1)
      } catch (error) {
        if (error.name === 'AbortError' || controller.signal.aborted) {
          return
        }
        setPeople([])
        setErrorMessage('Unable to load people.')
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    loadPeople()

    return () => controller.abort()
  }, [sortFilter])

  const handlePrev = () => {
    setCurrentPage((prev) => Math.max(1, prev - 1))
  }

  const handleNext = () => {
    setCurrentPage((prev) => Math.min(totalPages, prev + 1))
  }

  const handlePageSelect = (page) => {
    setCurrentPage(page)
  }

  return (
    <div className="home person">
      <div className="home__bg" aria-hidden="true">
        <img src={HERO_IMAGE} alt="" />
      </div>

      <main className="home__content person__content">
        <p className="home__greeting">Person Database</p>

        <section className="home__card person__card" aria-label="People">
          <div className="person__card-header">
            <div className="person__filters" aria-label="Filters">
              <label className="person__filter">
                Sort
                <select
                  className="person__select"
                  value={sortFilter}
                  onChange={(event) => setSortFilter(event.target.value)}
                >
                  <option value="last_modified">Last modified</option>
                  <option value="alphabetical">Alphabetical</option>
                </select>
              </label>
              <label className="person__filter">
                Group
                <select className="person__select" defaultValue="all">
                  <option value="all">All</option>
                  <option value="family">Family</option>
                  <option value="friends">Friends</option>
                  <option value="work">Work</option>
                </select>
              </label>
            </div>
            <span className="person__page-count">
              Page {currentPage} of {totalPages}
            </span>
          </div>

          {isLoading ? <p className="home__status">Loading people…</p> : null}
          {!isLoading && errorMessage ? (
            <p className="home__status home__status--error">{errorMessage}</p>
          ) : null}

          <div className="home__latest-grid person__grid">
            {pageItems.map((person) => (
              <Link
                className="home__latest-item home__latest-link"
                key={person.id}
                to={`/profile/${person.id}`}
              >
                <img
                  className="home__latest-avatar"
                  src={person.avatar || AVATAR_PLACEHOLDER}
                  alt=""
                  aria-hidden="true"
                />
                <span className="home__latest-name">{person.name}</span>
              </Link>
            ))}
          </div>

          <div className="person__pagination">
            <button
              className="person__page-button"
              type="button"
              onClick={handlePrev}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <div className="person__page-dots" aria-label="Page selector">
              {Array.from({ length: totalPages }, (_, index) => {
                const page = index + 1
                const isActive = page === currentPage
                return (
                  <button
                    key={page}
                    className={`person__page-dot${isActive ? ' person__page-dot--active' : ''}`}
                    type="button"
                    aria-pressed={isActive}
                    aria-label={`Go to page ${page}`}
                    onClick={() => handlePageSelect(page)}
                  />
                )
              })}
            </div>
            <button
              className="person__page-button"
              type="button"
              onClick={handleNext}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default PersonDatabase
