# MovieBox API

A FastAPI service that turns MovieBox (`moviebox.ph`) into a clean JSON REST API:
catalog rows, search, deep detail trees, direct `MP4`/`HLS`/`DASH` stream URLs and
subtitle tracks — assembled from the upstream API (no HTML scraping, no headless browser).

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](runtime.txt)
[![Vercel](https://img.shields.io/badge/Vercel-deployed-000000?style=flat-square&logo=vercel&logoColor=white)](vercel.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

Live: <https://moviebox-api-steel.vercel.app> (open the root URL for the built-in HTML dashboard that lists every endpoint with a live sample link).

## Endpoints

| Method | Path | Returns |
| --- | --- | --- |
| GET | `/` | HTML dashboard of the whole API |
| GET | `/home` | Home screen as `sections[]`, each with `section`, `count`, `items[]` |
| GET | `/home/categories` | Category list for the home screen |
| GET | `/movies` | Movies listing (flat `items[]`) |
| GET | `/tv-series` | TV series listing |
| GET | `/animation` | Animation listing |
| GET | `/dubbed` | Dubbed titles |
| GET | `/genres` | All genres |
| GET | `/genre/{name}` | Titles in one genre |
| GET | `/ranking` | Ranked / trending list |
| GET | `/top-imdb` | Top IMDb list |
| GET | `/search?q=` | Search results (`items[]`) |
| GET | `/search/suggest?q=` | Type-ahead suggestions |
| GET | `/detail/{slug}` | Deep detail tree — seasons, episodes, languages, resolutions, metadata |
| GET | `/api/stream/{subject_id}` | Playable sources: `resolution`, `hls[]`, `dash[]`, direct MP4 |
| GET | `/api/stream/{subject_id}/captions?detail_path=&se=&ep=` | Subtitle tracks for an episode |

Items carry `name` and `poster_url`, so a client can render a row without a second call.

## How it works

- Talks to the provider's own BFF endpoint (`https://h5-api.aoneroom.com/wefeed-h5api-bff`
  with `host=moviebox.ph`) instead of scraping pages, so responses are already JSON.
- Bootstraps a **guest bearer token** from the `x-user` response header (falling back to
  the `token=` cookie) on first use, caches it in memory, and force-refreshes it once when
  a call is rejected. Acquisition is guarded by an `asyncio.Lock`, so a burst of first
  requests doesn't stampede the upstream.
- Sends the browser-like headers the upstream expects (User-Agent, `Referer`, `Origin`,
  `X-Client-Info`) and resolves playback against the CDN domain handed back by the
  upstream (defaults to `netfilm.world`).
- Normalization happens once per shape, which is why every endpoint returns the same
  field names.

## Quick start

```bash
git clone https://github.com/SagorT3K/moviebox-api.git
cd moviebox-api
pip install -r requirements.txt

uvicorn api:app --host 0.0.0.0 --port 8000 --reload
# or: python api.py
```

Then open <http://localhost:8000> for the dashboard, and in a second shell:

```bash
python verify.py
```

`verify.py` walks `/`, `/home`, `/movies`, `/tv-series`, `/animation` and
`/search?q=attack` and prints per-section counts plus how many items actually have a
`name` and a `poster_url` — a quick "is the upstream still shaped the way we expect?" check.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_KEY` | *(unset)* | Optional shared secret. When set, every request must send `X-API-Key: <value>` (or `?api_key=`) or it is answered with `401`. Unset ⇒ the API stays open, as before. |
| `PORT` | `8000` | Port used by the `python api.py` entry point. |


## Deployment

**Vercel** — `vercel.json` builds `api/index.py` with `@vercel/python` and rewrites both
`/api/(.*)` and `/(.*)` to it; `api/index.py` puts the repository root on `sys.path` and
re-exports `app` from `api.py`, so one FastAPI app serves every route. `runtime.txt` pins
Python 3.11.4.

1. Import this repository on vercel.com (framework preset: **Other**).
2. Add the `API_KEY` environment variable if you want the API locked down.
3. Deploy, then open `https://<project>.vercel.app/` for the dashboard.

**Any host that runs Python** — `Procfile` runs gunicorn with uvicorn workers:
`web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app`

## CORS and access control

- The CORS allowlist is deliberately short (currently `hdmoviebox.fly.dev`,
  `localhost:7860`, `127.0.0.1:7860` and `localhost:3000`) and `GET`-only. CORS is
  browser-enforced, so server-to-server callers such as the MovieBox front end are not
  affected — it is not an access-control mechanism.
- The real access control is the optional `API_KEY` guard above. Both halves must match:
  `API_KEY` here, `MOVIEBOX_API_KEY` in the front end.

## Project structure

```
moviebox-api/
├── api.py            FastAPI app: token bootstrap, upstream client, all routes, HTML dashboard
├── api/index.py      Vercel entry point (re-exports `app` from ../api.py)
├── verify.py         end-to-end smoke test against a running instance
├── requirements.txt  fastapi, uvicorn, gunicorn, httpx, beautifulsoup4
├── runtime.txt       python-3.11.4 (Vercel)
├── vercel.json       @vercel/python build + route rewrites
├── Procfile          gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app
├── CONTRIBUTING.md
└── LICENSE           MIT
```

## Notes and caveats

- **No caching and no persistence.** The guest token lives in process memory only, so
  every cold serverless start fetches a fresh one.
- Stream URLs are resolved live and are normally short-lived signed URLs — re-resolve on
  each play instead of storing them.
- The upstream service is unofficial and can change shape without notice; running
  `verify.py` is the quickest way to notice. Responses here are only as stable as it is.
- No media is hosted in this repository, and nothing is parsed out of HTML pages.

## Credits

Original project and MIT copyright: [walterwhite-69/Moviebox-API](https://github.com/walterwhite-69/Moviebox-API).
This repository is the fork maintained for the [MovieBox](https://github.com/SagorT3K/moviebox)
front end. See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow and [LICENSE](LICENSE) for terms.
