---
name: subscription-error-fallback
description: Pattern for graceful error fallback in BASE64-subscription endpoints — cache last successful response and inject placeholder+error entries on failure
source: auto-skill
extracted_at: '2026-06-13T10:57:12.008Z'
---

# Subscription error fallback with last-known-good config

When a subscription endpoint (v2ray/VLESS/trojan BASE64 format) fails to fetch from upstream, instead of returning a hard error, serve the last successfully received config with injected placeholder entries and an error notification.

## When to use

- You have a Flask/similar proxy that serves a subscription (BASE64-encoded list of proxy URIs)
- You want clients to continue working with the last known config during upstream outages
- You want the client to visually see an error notification among the server entries

## Procedure

### 1. Add config toggle

Add a boolean field (e.g. `error_fallback: false`) to the project's config file, disabled by default.

In the auto-generation code that creates a default config, include the new field:

```python
yaml.dump({..., "error_fallback": False}, f)
```

### 2. Create helper functions

Two internal functions in the API module:

**`_get_error_fallback_enabled()`** — reads the toggle from config, safely falls back to `False` on any error:

```python
def _get_error_fallback_enabled() -> bool:
    try:
        if os.path.exists("config.yaml"):
            with open("config.yaml") as f:
                config = yaml.safe_load(f)
                if isinstance(config, dict):
                    return config.get("error_fallback", False)
    except Exception:
        pass
    return False
```

**`_build_fallback_response(saved_b64, error_msg)`** — decodes the saved BASE64, appends 3 dummy entries (dash, error comment, dash), re-encodes:

```python
def _build_fallback_response(saved_b64: str, error_msg: str) -> str:
    try:
        decoded = base64.b64decode(saved_b64).decode("utf-8")
    except Exception:
        return saved_b64  # degraded: return raw data if corrupted

    lines = decoded.strip().split("\n")
    error_lines = [
        "-",
        f"# subscription error: {error_msg}",
        "-",
    ]
    new_config = "\n".join(lines + [""] + error_lines)
    return base64.b64encode(new_config.encode("utf-8")).decode("utf-8")
```

### 3. Modify the fetch function

In the main `get_servers()` or equivalent:

- On **success**: if the toggle is on, write `response.text` to a temp file (e.g. `.last_config.b64`)
- On **failure**: if toggle is on AND temp file exists, call `_build_fallback_response()`
- Otherwise: return the error message as before

```python
def get_servers() -> str:
    error_fallback = _get_error_fallback_enabled()
    try:
        response = requests.get(SUBSCRIPTION_URL, headers=headers)
        response.raise_for_status()
        if error_fallback:
            with open(LAST_CONFIG_PATH, "w") as f:
                f.write(response.text)
        return response.text
    except requests.exceptions.RequestException as e:
        if error_fallback and os.path.exists(LAST_CONFIG_PATH):
            try:
                with open(LAST_CONFIG_PATH) as f:
                    saved_b64 = f.read()
                return _build_fallback_response(saved_b64, str(e))
            except Exception:
                pass
        return f"Ошибка при выполнении запроса: {e}"
```

### 4. Ignore the temp file

Add `.last_config.b64` (or whatever path chosen) to `.gitignore`.

### 5. Test

- Verify BASE64 round-trip: encode → decode → modify → re-encode → decode matches expected
- Test with a mock server: first request succeeds (config saved), second request fails (fallback served)
- Verify the fallback response is valid BASE64 and contains original entries + 3 new entries (dash, error, dash)

## Edge cases handled

- **Config file missing or malformed**: toggle defaults to `False` (safe fallback)
- **No saved config yet on first error**: returns error message as before
- **Saved BASE64 data corrupted**: returns raw saved data unchanged
- **File write failure**: silently ignored, subsequent requests will fail normally
