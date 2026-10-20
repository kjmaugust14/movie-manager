// const API_BASE_URL = "http://localhost:5000/api"
const API_BASE_URL = "https://movie-manager-rb8r.onrender.com/api"

function getToken() {
    return localStorage.getItem("movie_token")
}

function saveToken(token) {
    localStorage.setItem("movie_token", token)
}

function removeToken() {
    localStorage.removeItem("movie_token")
}

function isLoggedIn() {
    return Boolean(getToken())
}

async function apiRequest(endpoint, options = {}) {
    const token = getToken()
    const headers = {
        ...(options.headers || {})
    }

    if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json"
    }

    if (token) {
        headers["Authorization"] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    })

    let data = null

    try {
        data = await response.json()
    } catch (error) {
        // Response does not contain JSON
    }

    if (!response.ok) {
        if (response.status === 401) {
            removeToken()
        }

        throw new Error(data?.error || data?.message || "Something went wrong")
    }

    return data
}

