import { useParams } from 'react-router-dom'
import { people } from '../data/people.js'

const heroImage =
  'https://www.figma.com/api/mcp/asset/55c25fd1-e61b-4263-a50f-2ba9d4e4bc55'
const avatarPlaceholder =
  'https://www.figma.com/api/mcp/asset/e1cc52ac-9fe1-43fd-9bcf-79865cf93c24'

function Profile() {
  const { id } = useParams()
  const personId = Number(id)
  const person = people.find((entry) => entry.id === personId)
  const profile = person ?? {
    id: personId,
    name: 'Unknown Person',
    relation: 'Unknown',
    group: 'Unassigned',
    dateAdded: 'Unknown',
    lastSeen: 'Unknown',
    status: 'Unknown',
    notes: 'No details available yet.',
    avatar: avatarPlaceholder,
  }

  return (
    <div className="home profile">
      <div className="home__bg" aria-hidden="true">
        <img src={heroImage} alt="" />
      </div>

      <main className="home__content profile__content">
        <p className="home__greeting">Profile</p>

        <section className="home__card profile__card" aria-label="Profile">
          <div className="profile__header">
            <div className="profile__avatar" aria-hidden="true">
              <img src={profile.avatar || avatarPlaceholder} alt="" />
            </div>
            <div className="profile__identity">
              <h2 className="profile__name">{profile.name}</h2>
              <p className="profile__meta">
                {profile.relation} • ID {profile.id}
              </p>
            </div>
          </div>

          <div className="profile__details">
            <div className="profile__detail">
              <span className="profile__label">Date Added</span>
              <span className="profile__value">{profile.dateAdded}</span>
            </div>
            <div className="profile__detail">
              <span className="profile__label">Last Seen</span>
              <span className="profile__value">{profile.lastSeen}</span>
            </div>
            <div className="profile__detail">
              <span className="profile__label">Group</span>
              <span className="profile__value">{profile.group}</span>
            </div>
            <div className="profile__detail">
              <span className="profile__label">Status</span>
              <span className="profile__value">{profile.status}</span>
            </div>
          </div>

          <div className="profile__notes">
            <span className="profile__label">Notes</span>
            <p className="profile__note-text">
              {profile.notes}
            </p>
          </div>
        </section>
      </main>
    </div>
  )
}

export default Profile
