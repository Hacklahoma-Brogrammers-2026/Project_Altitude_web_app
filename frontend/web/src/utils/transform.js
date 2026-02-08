const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export function normalizePerson(person, index = 0) {
  const id = person.contact_id ?? person.id ?? person.user_id ?? `${index}`
  // Handle combined Backend (first/last) vs Mock Data (name)
  const name =
    person.name ??
    `${person.first_name ?? ''} ${person.last_name ?? ''}`.trim()
  
  let avatar = person.photo ?? person.photo_url ?? person.image ?? person.avatar
  
  if (!avatar && person.image_path) {
    // Check if path is absolute (legacy/broken) or relative
    // We assume backend serves images at /images
    // The image_path from backend might be "user_id/file.jpg"
    // We need "http://host:port/images/user_id/file.jpg"
    
    // Clean up potentially absolute paths (fallback)
    const cleanPath = person.image_path.split('data/faces/').pop();
    avatar = `http://192.168.137.1:8000/images/${cleanPath}`
  }

  const relation = person.label ?? person.relation ?? person.group ?? 'Person'
  const summary = person.note ?? person.summary ?? person.content ?? ''

  return {
    id,
    name: name || 'Unknown Person',
    avatar,
    relation,
    summary,
    raw: person,
  }
}
