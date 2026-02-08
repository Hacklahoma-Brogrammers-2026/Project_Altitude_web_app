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
  const endpoint = `${API_BASE_URL}/people?sort=${sort}`
  
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
