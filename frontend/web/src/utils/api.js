const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

/**
 * Fetches the list of people from the backend.
 * 
 * @param {Object} options
 * @param {AbortSignal} [options.signal] - Abort signal for cancelling the request
 * @param {string} [options.sort] - Sort order: 'last_modified' (default) or 'alphabetical'
 * @returns {Promise<Array>} List of person objects
 */
export async function fetchPeople({ signal, sort = 'last_modified' } = {}) {
  const endpoint = `http://192.168.137.1:8000/people?sort=${sort}`
  
  const response = await fetch(endpoint, {
    signal,
    cache: 'no-store'
  })

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }

  const data = await response.json()
  return Array.isArray(data) ? data : data?.results ?? [] 
}

/**
 * Search for users by name.
 * @param {string} query 
 * @param {AbortSignal} [signal]
 */
export async function searchUsers(query, signal) {
  const endpoint = `http://192.168.137.1:8000/searchUser?q=${encodeURIComponent(query)}`
  const response = await fetch(endpoint, { signal })
  if (!response.ok) {
    throw new Error(`Search failed: ${response.status}`)
  }
  const data = await response.json()
  return data.results ?? []
}

/**
 * Semantic search for info/notes.
 * @param {string} query 
 * @param {AbortSignal} [signal]
 */
export async function searchInfo(query, signal) {
  const endpoint = `http://192.168.137.1:8000/searchInfo?q=${encodeURIComponent(query)}`
  const response = await fetch(endpoint, { signal })
  if (!response.ok) {
    throw new Error(`Search failed: ${response.status}`)
  }
  const data = await response.json()
  return data.results ?? []
}
