# Troubles We Went Through

A honest account of every problem hit during development and how we solved it.

---

## 1. `module 'webui' has no attribute 'window'`

**Problem:** The initial import was `import webui` which gave a bare module
with no usable attributes at all — `dir(webui)` returned only dunder fields.

**What we tried:**
- `import webui` → `webui.window()` — AttributeError
- `pip install webui2==2.4.2` → 404, version doesn't exist on PyPI
- Installing from a GitHub release wheel URL → 404

**Solution:** The correct import for webui2 v2.5.7 is:
```python
from webui import webui
window = webui.Window()
```

---

## 2. RPC functions silently failing — "Failed to load"

**Problem:** The tree showed "Failed to load" with no error in the console
and no traceback in the terminal. The RPC calls were firing but returning
nothing useful.

**Root cause:** WebUI2 does not pass a raw string to bound Python functions.
It passes a `webui.event` object. The old code did `json.loads(payload)`
where `payload` was the event object itself — this silently crashed inside
the `try/except` and returned `{"ok": false, "error": "..."}` which the
frontend wasn't surfacing clearly.

**Solution:** Changed all RPC handlers to use `e.get_string()` to extract
the payload from the event object, and `e.return_string()` to send the
response back:
```python
def rpc_create_node(e) -> None:
    data = json.loads(e.get_string())
    e.return_string(_ok(...))
```

---

## 3. `window.show("frontend/index.html")` — "The requested resource is not available"

**Problem:** Even with the correct file path, WebUI2 could not serve the
HTML file from disk. It kept showing a blank "resource not available" page
regardless of whether the path was relative, absolute, or adjusted.

**What we tried:**
- `window.show("frontend/index.html")`
- `window.show("../frontend/index.html")`
- Moving the frontend folder to different locations
- Using an absolute path with `os.path.abspath()`

**Solution:** Embedded the entire HTML as a Python string directly in
`main.py` and passed it to `window.show(HTML)` instead of a file path.
WebUI2 accepts raw HTML strings just as well as file paths, and this
completely bypassed the file-serving issue:
```python
HTML = """<!DOCTYPE html>..."""
window.show(HTML)
```

---

## 4. `webui.wait()` scope confusion

**Problem:** After `from webui import webui`, calling `webui.wait()` was
ambiguous — it wasn't clear if `webui` referred to the module or the class.

**Solution:** Confirmed via `dir(webui)` that `wait` is a method on the
`webui` class itself, so `webui.wait()` after `from webui import webui`
is correct and calls the class-level static method.

---

## Summary

| Problem | Root Cause | Fix |
|---|---|---|
| `no attribute 'window'` | Wrong import style | `from webui import webui` |
| Silent RPC failures | Event object not a string | Use `e.get_string()` and `e.return_string()` |
| Resource not available | WebUI2 can't serve files from disk | Embed HTML as string in `main.py` |
| `webui.wait()` confusion | Import ambiguity | Confirmed `wait` is on the class |