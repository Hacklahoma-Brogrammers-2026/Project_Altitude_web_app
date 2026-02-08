const heroImage =
  'https://www.figma.com/api/mcp/asset/55c25fd1-e61b-4263-a50f-2ba9d4e4bc55'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/e1cc52ac-9fe1-43fd-9bcf-79865cf93c24'

const people = Array.from({ length: 24 }, (_, index) => ({
  id: index + 1,
  name: 'First Last',
}))

function PersonDatabase() {
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
            <span className="person__page-count">Page 1 of 4</span>
          </div>

          <div className="home__latest-grid person__grid">
            {people.map((person) => (
              <div className="home__latest-item" key={person.id}>
                <img
                  className="home__latest-avatar"
                  src={avatarPlaceholder}
                  alt=""
                  aria-hidden="true"
                />
                <span className="home__latest-name">{person.name}</span>
              </div>
            ))}
          </div>

          <div className="person__pagination">
            <button className="person__page-button" type="button" disabled>
              Previous
            </button>
            <div className="person__page-dots" aria-hidden="true">
              <span className="person__page-dot person__page-dot--active" />
              <span className="person__page-dot" />
              <span className="person__page-dot" />
              <span className="person__page-dot" />
            </div>
            <button className="person__page-button" type="button">
              Next
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default PersonDatabase
