def movie_to_dict(movie):
    return {
        "id": movie.id,
        "title": movie.title,
        "year": movie.year,
        "genre": movie.genre,
        "director": movie.director,
        "rating": movie.rating,
    }