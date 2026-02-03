from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import httpx


API_BASE_URL = "https://api.kinopoisk.dev/v1.4"
DEFAULT_TIMEOUT = httpx.Timeout(40.0, read=40.0)
DEFAULT_RETRIES = 2
logger = logging.getLogger(__name__)


@dataclass
class MovieSummary:
    movie_id: int
    name: str
    description: str
    rating: Optional[float]
    poster_url: Optional[str]
    year: Optional[int]


@dataclass
class MovieDetails:
    movie_id: int
    name: str
    actors: List[str]
    directors: List[str]
    duration_minutes: Optional[int]


class KinopoiskClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"X-API-KEY": self._api_key}
        async with httpx.AsyncClient(
            base_url=API_BASE_URL, headers=headers, timeout=DEFAULT_TIMEOUT
        ) as client:
            last_error: Optional[Exception] = None
            for attempt in range(DEFAULT_RETRIES + 1):
                try:
                    response = await client.get(path, params=params)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as exc:
                    logger.exception(
                        "Kinopoisk API HTTP error: %s %s params=%s status=%s body=%s",
                        exc.request.method,
                        exc.request.url,
                        params,
                        exc.response.status_code,
                        exc.response.text,
                    )
                    raise
                except httpx.ReadTimeout as exc:
                    last_error = exc
                    logger.warning(
                        "Kinopoisk API read timeout: %s %s params=%s attempt=%s",
                        exc.request.method if exc.request else "GET",
                        exc.request.url if exc.request else path,
                        params,
                        attempt + 1,
                    )
                    continue
                except httpx.HTTPError as exc:
                    logger.exception(
                        "Kinopoisk API request error: %s %s params=%s error=%s",
                        exc.request.method if exc.request else "GET",
                        exc.request.url if exc.request else path,
                        params,
                        exc,
                    )
                    raise
            if last_error:
                raise last_error
            raise httpx.HTTPError("Kinopoisk API request failed")

    def _map_summary(self, item: Dict[str, Any]) -> Optional[MovieSummary]:
        movie_id = item.get("id")
        if not movie_id:
            return None
        name = item.get("name") or item.get("alternativeName") or "Без названия"
        description = item.get("shortDescription") or item.get("description") or "Описание отсутствует."
        rating = None
        rating_data = item.get("rating") or {}
        if isinstance(rating_data, dict):
            rating = rating_data.get("kp") or rating_data.get("imdb")
        poster_url = None
        poster_data = item.get("poster") or {}
        if isinstance(poster_data, dict):
            poster_url = poster_data.get("url") or poster_data.get("previewUrl")
        year = item.get("year")
        return MovieSummary(
            movie_id=movie_id,
            name=name,
            description=description,
            rating=rating,
            poster_url=poster_url,
            year=year,
        )

    _ACTOR_KEYS = frozenset({"actor", "актер", "актёр", "актеры", "актриса"})
    _DIRECTOR_KEYS = frozenset({"director", "режиссер", "режиссёр", "режиссеры"})

    def _normalize_profession(self, role: Any) -> Optional[str]:
        if role is None:
            return None
        if isinstance(role, list):
            role = role[0] if role else None
        if isinstance(role, dict):
            role = role.get("value") or role.get("name")
        if role is None:
            return None
        s = (role if isinstance(role, str) else str(role)).strip().lower()
        return s if s else None

    def _extract_persons(
        self,
        persons: Iterable[Dict[str, Any]],
        profession: str,
        allowed_values: frozenset[str],
    ) -> List[str]:
        result: List[str] = []
        for person in persons:
            role = self._normalize_profession(
                person.get("enProfession") or person.get("profession")
            )
            if not role or role not in allowed_values:
                continue
            name = person.get("name") or person.get("enName")
            if name:
                result.append(name)
        return result

    async def get_movies_by_genre(self, genre: str, limit: int = 3) -> List[MovieSummary]:
        params = {
            "page": 1,
            "limit": 20,
            "type": "movie",
            "genres.name": genre,
            "sortField": "rating.kp",
            "sortType": "-1",
            "notNullFields": ["poster.url", "name"],
        }
        data = await self._request("/movie", params=params)
        docs = data.get("docs") or []
        movies = [movie for item in docs if (movie := self._map_summary(item))]
        return movies[:limit]

    async def get_random_movie(self) -> Optional[MovieSummary]:
        data = await self._request("/movie/random", params={"notNullFields": ["poster.url", "name"]})
        return self._map_summary(data)

    async def search_movies_by_name(self, query: str, limit: int = 3) -> List[MovieSummary]:
        params = {"query": query, "page": 1, "limit": limit}
        data = await self._request("/movie/search", params=params)
        docs = data.get("docs") or []
        movies = [movie for item in docs if (movie := self._map_summary(item))]
        return movies[:limit]

    async def get_movie_details(self, movie_id: int) -> Optional[MovieDetails]:
        data = await self._request(f"/movie/{movie_id}")
        name = data.get("name") or data.get("alternativeName") or "Без названия"
        persons = data.get("persons") or []
        actors = self._extract_persons(persons, "actor", self._ACTOR_KEYS)[:5]
        directors = self._extract_persons(persons, "director", self._DIRECTOR_KEYS)[:3]
        duration = data.get("movieLength")
        return MovieDetails(
            movie_id=movie_id,
            name=name,
            actors=actors,
            directors=directors,
            duration_minutes=duration,
        )
