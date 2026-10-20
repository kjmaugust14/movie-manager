requireAuthentication();

let movies = [];
let editingMovieId = null;
let searchTimeout = null;

/*
=========================================================
DOM ELEMENTS
=========================================================
*/

const movieGrid = document.getElementById("movieGrid");

const loadingState = document.getElementById("loadingState");

const emptyState = document.getElementById("emptyState");

const errorState = document.getElementById("errorState");

const errorMessage = document.getElementById("errorMessage");

const searchInput = document.getElementById("searchInput");

const genreFilter = document.getElementById("genreFilter");

const movieCount = document.getElementById("movieCount");

const totalMovies = document.getElementById("totalMovies");

const averageRating = document.getElementById("averageRating");

const totalGenres = document.getElementById("totalGenres");

const movieModal = document.getElementById("movieModal");

const movieForm = document.getElementById("movieForm");

const modalTitle = document.getElementById("modalTitle");

const movieIdInput = document.getElementById("movieId");

const addMovieButton = document.getElementById("addMovieButton");

const closeModalButton = document.getElementById("closeModalButton");

const cancelButton = document.getElementById("cancelButton");

const retryButton = document.getElementById("retryButton");

const logoutButton = document.getElementById("logoutButton");

const welcomeUser = document.getElementById("welcomeUser");

/*
=========================================================
INITIALIZATION
=========================================================
*/

document.addEventListener("DOMContentLoaded", async function () {
  await loadCurrentUser();

  await loadMovies();
});

/*
=========================================================
CURRENT USER
=========================================================
*/

async function loadCurrentUser() {
  try {
    const data = await apiRequest("/auth/me");

    welcomeUser.textContent = `Hi, ${data.user.username}`;
  } catch (error) {
    logout();
  }
}

/*
=========================================================
GET MOVIES
=========================================================
*/

async function loadMovies() {
  showLoading();

  try {
    const search = searchInput.value.trim();

    const genre = genreFilter.value;

    const params = new URLSearchParams();

    if (search) {
      params.append("search", search);
    }

    if (genre) {
      params.append("genre", genre);
    }

    const query = params.toString();

    const endpoint = query ? `/movies?${query}` : "/movies";

    movies = await apiRequest(endpoint);

    renderMovies();

    updateStatistics();

    populateGenres();
  } catch (error) {
    showError(error.message);
  }
}

/*
=========================================================
RENDER MOVIES
=========================================================
*/

function renderMovies() {
  movieGrid.innerHTML = "";

  if (movies.length === 0) {
    movieGrid.classList.add("hidden");

    emptyState.classList.remove("hidden");

    movieCount.textContent = "0 movies";

    return;
  }

  emptyState.classList.add("hidden");

  loadingState.classList.add("hidden");

  movieGrid.classList.remove("hidden");

  movieCount.textContent = `${movies.length} ${
    movies.length === 1 ? "movie" : "movies"
  }`;

  movies.forEach((movie) => {
    const card = createMovieCard(movie);

    movieGrid.appendChild(card);
  });
}

/*
=========================================================
CREATE MOVIE CARD
=========================================================
*/

function createMovieCard(movie) {
  const card = document.createElement("article");

  card.className = "movie-card";

  const rating = Number(movie.rating).toFixed(1);

  card.innerHTML = `
        <div class="movie-poster">
            <span class="poster-number">
                ${movie.id}
            </span>

            <div class="poster-icon">
                🎬
            </div>

            <span class="poster-year">
                ${movie.year}
            </span>
        </div>

        <div class="movie-info">

            <div class="movie-top">

                <span class="genre-badge">
                    ${escapeHTML(movie.genre)}
                </span>

                <span class="rating">
                    ⭐ ${rating}
                </span>

            </div>

            <h3>
                ${escapeHTML(movie.title)}
            </h3>

            <p class="director">
                Directed by
                <strong>
                    ${escapeHTML(movie.director)}
                </strong>
            </p>

            <div class="movie-actions">

                <button
                    class="btn btn-small btn-outline edit-button"
                    data-id="${movie.id}"
                >
                    Edit
                </button>

                <button
                    class="btn btn-small btn-danger delete-button"
                    data-id="${movie.id}"
                >
                    Delete
                </button>

            </div>

        </div>
    `;

  return card;
}

/*
=========================================================
SECURITY
=========================================================
*/

function escapeHTML(value) {
  const div = document.createElement("div");

  div.textContent = value;

  return div.innerHTML;
}

/*
=========================================================
STATISTICS
=========================================================
*/

function updateStatistics() {
  totalMovies.textContent = movies.length;

  if (movies.length === 0) {
    averageRating.textContent = "0.0";

    totalGenres.textContent = "0";

    return;
  }

  const totalRating = movies.reduce(
    (sum, movie) => sum + Number(movie.rating),
    0,
  );

  const average = totalRating / movies.length;

  averageRating.textContent = average.toFixed(1);

  const genres = new Set(movies.map((movie) => movie.genre.toLowerCase()));

  totalGenres.textContent = genres.size;
}

/*
=========================================================
GENRE FILTER
=========================================================
*/

function populateGenres() {
  const currentGenre = genreFilter.value;

  const genres = [...new Set(movies.map((movie) => movie.genre))].sort();

  genreFilter.innerHTML = `
        <option value="">
            All Genres
        </option>
    `;

  genres.forEach((genre) => {
    const option = document.createElement("option");

    option.value = genre;
    option.textContent = genre;

    genreFilter.appendChild(option);
  });

  genreFilter.value = genres.includes(currentGenre) ? currentGenre : "";
}

/*
=========================================================
SEARCH
=========================================================
*/

searchInput.addEventListener("input", function () {
  clearTimeout(searchTimeout);

  searchTimeout = setTimeout(() => loadMovies(), 400);
});

genreFilter.addEventListener("change", loadMovies);

/*
=========================================================
MOVIE MODAL
=========================================================
*/

addMovieButton.addEventListener("click", openAddModal);

closeModalButton.addEventListener("click", closeModal);

cancelButton.addEventListener("click", closeModal);

document.querySelector(".modal-overlay").addEventListener("click", closeModal);

function openAddModal() {
  editingMovieId = null;

  movieForm.reset();

  movieIdInput.value = "";

  modalTitle.textContent = "Add Movie";

  movieModal.classList.remove("hidden");
}

function openEditModal(movie) {
  editingMovieId = movie.id;

  movieIdInput.value = movie.id;

  document.getElementById("title").value = movie.title;

  document.getElementById("year").value = movie.year;

  document.getElementById("genre").value = movie.genre;

  document.getElementById("director").value = movie.director;

  document.getElementById("rating").value = movie.rating;

  modalTitle.textContent = "Edit Movie";

  movieModal.classList.remove("hidden");
}

function closeModal() {
  movieModal.classList.add("hidden");

  editingMovieId = null;

  movieForm.reset();
}

/*
=========================================================
CREATE / UPDATE MOVIE
=========================================================
*/

movieForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const movie = {
    title: document.getElementById("title").value.trim(),

    year: Number(document.getElementById("year").value),

    genre: document.getElementById("genre").value.trim(),

    director: document.getElementById("director").value.trim(),

    rating: Number(document.getElementById("rating").value),
  };

  const button = document.getElementById("saveMovieButton");

  try {
    button.disabled = true;

    button.textContent = editingMovieId ? "Updating..." : "Saving...";

    if (editingMovieId) {
      await apiRequest(`/movies/${editingMovieId}`, {
        method: "PUT",

        body: JSON.stringify(movie),
      });

      showToast("Movie updated successfully");
    } else {
      await apiRequest("/movies", {
        method: "POST",

        body: JSON.stringify(movie),
      });

      showToast("Movie added successfully");
    }

    closeModal();

    await loadMovies();
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    button.disabled = false;

    button.textContent = "Save Movie";
  }
});

/*
=========================================================
EDIT / DELETE BUTTONS
=========================================================
*/

movieGrid.addEventListener("click", async function (event) {
  const editButton = event.target.closest(".edit-button");

  const deleteButton = event.target.closest(".delete-button");

  if (editButton) {
    const id = Number(editButton.dataset.id);

    const movie = movies.find((movie) => movie.id === id);

    if (movie) {
      openEditModal(movie);
    }
  }

  if (deleteButton) {
    const id = Number(deleteButton.dataset.id);

    await deleteMovie(id);
  }
});

/*
=========================================================
DELETE
=========================================================
*/

async function deleteMovie(id) {
  const movie = movies.find((movie) => movie.id === id);

  if (!movie) {
    return;
  }

  const confirmed = window.confirm(`Delete "${movie.title}"?`);

  if (!confirmed) {
    return;
  }

  try {
    await apiRequest(`/movies/${id}`, {
      method: "DELETE",
    });

    showToast("Movie deleted successfully");

    await loadMovies();
  } catch (error) {
    showToast(error.message, "error");
  }
}

/*
=========================================================
LOGOUT
=========================================================
*/

logoutButton.addEventListener("click", logout);

/*
=========================================================
UI STATES
=========================================================
*/

function showLoading() {
  loadingState.classList.remove("hidden");

  errorState.classList.add("hidden");

  emptyState.classList.add("hidden");

  movieGrid.classList.add("hidden");
}

function showError(message) {
  loadingState.classList.add("hidden");

  movieGrid.classList.add("hidden");

  emptyState.classList.add("hidden");

  errorState.classList.remove("hidden");

  errorMessage.textContent = message;
}

retryButton.addEventListener("click", loadMovies);

/*
=========================================================
TOAST
=========================================================
*/

let toastTimeout;

function showToast(message, type = "success") {
  const toast = document.getElementById("toast");

  toast.textContent = message;

  toast.className = `toast show ${type}`;

  clearTimeout(toastTimeout);

  toastTimeout = setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}