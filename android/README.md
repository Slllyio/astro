# Kundli — Jyotish Reading (Android app)

A lightweight Android app that opens the B. V. Raman reading engine on your
phone. It is a **WebView wrapper**: the whole reading (chart, classical
narrative, dashboard, daśā, yogas) is produced by the Python backend in this
repository and displayed inside the app.

> **Why a wrapper, not a fully offline app?** The engine is Python + the Swiss
> Ephemeris (`pyswisseph`) plus the encoded Raman compendium. That cannot run
> inside an APK without a large, fragile re-architecture. So the app talks to a
> small backend you host once. The `.apk` then works on any phone **with an
> internet connection**.

There are two pieces: **(1) host the backend**, then **(2) build the `.apk`**.

---

## 1. Host the backend (do this once)

The repo root has a `Dockerfile` and a `render.yaml`. Any Docker host works
(Render, Railway, Fly.io, a VPS). Easiest free option — **Render**:

1. Push this repo to GitHub (already done for this branch).
2. Go to https://render.com → **New → Blueprint** → pick this repo.
   Render reads `render.yaml` and builds the `Dockerfile`.
3. When it finishes you get a URL like `https://kundli-reading.onrender.com`.
   Open `https://<that-url>/reading/v15/` in a browser to confirm the form loads.

(The free plan sleeps when idle and wakes on the next request, so the first
open after a while is slow. Upgrade for always-on.)

**Local test (optional):**
```bash
docker build -t kundli .
docker run -p 8000:8000 kundli
# open http://localhost:8000/reading/v15/
```

---

## 2. Build the `.apk` (no Android Studio needed)

A GitHub Actions workflow builds a shareable **debug** APK for you:

1. In GitHub → **Actions → “Build Android APK” → Run workflow**.
2. Paste your backend URL from step 1 into **backend_url**
   (e.g. `https://kundli-reading.onrender.com`). Leave it blank to have the app
   ask for the address on first launch instead.
3. When the run finishes, open it → **Artifacts → `kundli-reading-apk`** →
   download `app-debug.apk`.

That `app-debug.apk` is the file you share.

**Build locally instead (if you have the Android SDK):**
```bash
cd android
gradle wrapper --gradle-version 8.14.3   # first time only, needs internet
./gradlew :app:assembleDebug -PBACKEND_URL="https://your-backend-url"
# APK: android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 3. Share it on WhatsApp

- Send `app-debug.apk` to anyone as a WhatsApp document.
- On their phone they tap it and confirm **“Install unknown apps”** for
  WhatsApp/Files (Android asks this for any app not from the Play Store — normal
  for shared APKs).
- They open **Kundli — Jyotish Reading**, enter their birth details, and read.

If you did **not** bake the URL at build time, the app asks for the server
address on first launch (they paste your backend URL once). You can change it
later from the ⋮ menu → **Server address**.

---

## Notes & limits

- **Debug APK**: unsigned-for-Play but installable by sideloading — perfect for
  sharing directly. For a Play Store release you would sign a release build
  (`assembleRelease` + a keystore); not needed for WhatsApp sharing.
- **HTTPS only** by default (`usesCleartextTraffic=false`). Render/Railway/Fly
  give you HTTPS automatically. For a plain-HTTP local server, flip that flag in
  `app/src/main/AndroidManifest.xml` while testing.
- **Privacy**: birth data is sent to your backend to compute the reading. Host
  it somewhere you control.
- The app is intentionally thin (`MainActivity.kt` is ~120 lines); all the
  astrology lives in the Python engine, so improving the reading needs no app
  rebuild — only a backend redeploy.
