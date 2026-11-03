const API_BASE_URL = "http://localhost:5000/api" 
// const API_BASE_URL = "https://movie-manager-rb8r.onrender.com/api"

function getToken() {
  return localStorage.getItem("movie_token");
}

function saveToken(token) {
  localStorage.setItem("movie_token", token);
}

function removeToken() {
  localStorage.removeItem("movie_token");
}

async function apiRequest(endpoint, options = {}) {
  const headers = new Headers(options.headers || {});

  const token = getToken();


  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Do not set Content-Type for FormData.
  // The browser generates multipart/form-data and its boundary.
  const isFormData = options.body instanceof FormData;

  if (isFormData) {
    headers.delete("Content-Type");
  } else if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  let data = null;

  try {
    data = await response.json();
  } catch (error) {
    //
  }

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
    }

    throw new Error(data?.error || data?.message || "Something went wrong");
  }

  return data;
}

function uploadUrl(relativeFilename) {
  if (!relativeFilename) {
    return null;
  }

  const encodedPath = relativeFilename
    .split("/")
    .map(encodeURIComponent)
    .join("/");

  return `${API_BASE_URL}/uploads/${encodedPath}`;
}2