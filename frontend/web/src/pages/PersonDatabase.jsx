import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { people } from '../data/people.js'

const heroImage =
  'https://www.figma.com/api/mcp/asset/55c25fd1-e61b-4263-a50f-2ba9d4e4bc55'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/e1cc52ac-9fe1-43fd-9bcf-79865cf93c24'

function PersonDatabase() {
  const pageSize = 15
  const totalPages = Math.max(1, Math.ceil(people.length / pageSize))
  const [currentPage, setCurrentPage] = useState(1)

  const pageItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return people.slice(start, start + pageSize)
  }, [currentPage])

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
        <img src={heroImage} alt="" />
      </div>

      <main className="home__content person__content">
        <p className="home__greeting">Person Database</p>

        <section className="home__card person__card" aria-label="People">
          <div className="person__card-header">
            <div className="person__filters" aria-label="Filters">
              <label className="person__filter">
                Date Added
                <select className="person__select" defaultValue="recent">
                  <option value="recent">Most recent</option>
                  <option value="oldest">Oldest first</option>
                </select>
              </label>
              <label className="person__filter">
                Alphabetical
                <select className="person__select" defaultValue="az">
                  <option value="az">A to Z</option>
                  <option value="za">Z to A</option>
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

          <div className="home__latest-grid person__grid">
            {pageItems.map((person) => (
              <Link
                className="home__latest-item home__latest-link"
                key={person.id}
                to={`/profile/${person.id}`}
              >
                <img
                  className="home__latest-avatar"
                  src={person.avatar || avatarPlaceholder}
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
