# Nephele Troubleshooting Guide

This guide helps administrators debug common operational issues when deploying or running Nephele.

---

## 1. Database Issues

### Error: `OperationalError: connection to server at "db" failed`
- **Cause**: The API container started before the PostgreSQL database container was fully ready.
- **Fix**: Docker Compose handles this via `depends_on: { condition: service_healthy }`. Ensure Postgres has a working healthcheck configured.
- **Manual Command**: Restart the api container:
  ```bash
  docker compose restart app
  ```

### Database Schema Out of Sync
- **Cause**: Unapplied database revisions or modified SQLAlchemy models.
- **Fix**: Run Alembic migrations:
  ```bash
  alembic upgrade head
  ```

---

## 2. Vector Store (ChromaDB) Issues

### Error: `chromadb.errors.InvalidCollectionException`
- **Cause**: Chroma collection folders are corrupt or collection mismatch.
- **Fix**: Delete the local persistence directory to let Chroma regenerate collections automatically:
  ```bash
  rm -rf chroma_test_data/
  ```

### Chroma Timeout or Heartbeat Failure
- **Cause**: Under-resourced container or network socket lock.
- **Fix**: Scale container memory. Check status endpoint `/api/health/chroma` to confirm node socket state.

---

## 3. Audio & Sensor Hardware Issues

### Error: `PortAudio library not found`
- **Cause**: PyAudio or sounddevice is attempting to run on a headless server without physical audio devices.
- **Fix**: Nephele handles this automatically. If PortAudio is missing, the STT/TTS modules degrade to **Mock/Offline Dry-Run Modes**, preventing runtime crashes.

---

## 4. API Key & Provider Failures

### Error: `AuthenticationError` / `Missing credentials`
- **Cause**: Provider tokens (Gemini, Groq) are empty or expired.
- **Fix**: Verify your `.env` settings. The health endpoint `/api/health/provider` lists which keys are active.
- **Fallback**: If all keys are absent, Nephele defaults to local rubric-based evaluation.
