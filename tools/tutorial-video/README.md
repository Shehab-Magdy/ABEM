# Tutorial videos (عِمارة.كوم)

Builds the two landing-page walkthroughs (building admin, unit owner) from the real app:
narration with **edge-tts** (`ar-EG-ShakirNeural`), screen capture with **Playwright**,
captions burned in (white text, black outline), final mux with ffmpeg.

```
scenes_ar.py   narration + caption text (edit here)
tts.py         one MP3 per scene + durations.json
record.py      drives the app, paced to the narration; writes raw.webm + marks.json
compose.py     speed ramps, audio mix, caption PNGs (rsvg-convert), mp4 + vtt + poster
demo.py        cursor/highlight/email-overlay helpers
```

## Prerequisites
- `brew install librsvg` (caption rendering) and the Cairo + Inter fonts installed locally.
- `python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/playwright install chromium`
- A **demo stack on a throw-away database** (never record against your dev data):
  ```bash
  docker compose exec db psql -U abem_user -d postgres -c "CREATE DATABASE abem_demo;"
  docker compose run -d --name abem-demo-backend --no-deps -p 8001:8000 -e POSTGRES_DB=abem_demo backend \
    sh -c "python manage.py migrate --noinput && python manage.py seed_demo_data && python manage.py runserver 0.0.0.0:8000"
  # Arabic names/data and Arabic language for the demo users were set in that DB (see git history of this README);
  cd frontend && VITE_GOOGLE_CLIENT_ID=123456789012-demo.apps.googleusercontent.com \
    VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1 npm run dev -- --port 5174 --host 127.0.0.1
  ```
  Sign-in codes are read from the demo API's console email (`DEMO_LOGS`, default `docker logs abem-demo-backend --since 40s`).
  The dummy `VITE_GOOGLE_CLIENT_ID` only makes the Google button render for the owner video.

## Build
```bash
for v in admin owner; do
  .venv/bin/python tts.py $v
  .venv/bin/python record.py $v
  .venv/bin/python compose.py $v --dest ../../frontend/public/videos
done
```
Scenes can be re-recorded selectively: `record.py admin a05,a08` (then compose uses the partial marks, so re-run all scenes before publishing).

## English version
Add `scenes_en.py` (same scene ids), pick an English voice (e.g. `en-US-GuyNeural`), translate the UI strings
used by `record.py` (button labels) or run it with the app in English, and add `"en"` to `VIDEO_LANGS` in
`frontend/src/pages/landing/TutorialVideos.jsx`.
