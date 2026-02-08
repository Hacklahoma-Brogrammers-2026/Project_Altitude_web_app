export function normalizePerson(person, index = 0) {
  const id = person.contact_id ?? person.id ?? person.user_id ?? `${index}`
  // Handle combined Backend (first/last) vs Mock Data (name)
  const name =
    person.name ??
    `${person.first_name ?? ''} ${person.last_name ?? ''}`.trim()
  const avatar =
    person.photo ?? person.photo_url ?? person.image ?? person.avatar
  const relation = person.relation ?? person.group ?? 'Person'
  const summary = person.note ?? person.summary ?? ''

  return {
    id,
    name: name || 'Unknown Person',
    avatar,
    relation,
    summary,
    raw: person,
  }
}
