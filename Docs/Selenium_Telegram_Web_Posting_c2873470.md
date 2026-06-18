# Selenium Telegram Web Posting

## Task 1: Install dependencies

- Add `selenium`, `webdriver-manager`, and `pyperclip` to `requirements.txt`
- Run `pip install selenium webdriver-manager pyperclip`

## Task 2: Create `telegram_news_bot/services/telegram_web.py`

New Selenium-based service with these functions:

**`send_via_telegram_web(message: str, channel_name: str) -> bool`**
- Launches Chrome with a persistent user data directory (`telegram_news_bot/.chrome_profile/`) so Telegram Web login persists
- Uses `webdriver-manager` for automatic ChromeDriver matching
- Runs Chrome in **visible mode** (window always shown during normal operation)
- Navigates to `https://web.telegram.org/a/` (Telegram Web K version)
- Calls `_search_and_open_channel(channel_name)` then `_type_and_send(message)`
- Returns True on success, False on any failure

**`_search_and_open_channel(driver, channel_name: str) -> bool`**
- Clicks the search bar at the top (CSS: `.icon-search` or `[data-testid="search"]`)
- Types the channel name (e.g. "Tech News")
- Waits for search results to appear (WebDriverWait)
- Clicks the first result matching the channel name
- Waits for the chat view to load

**`_type_and_send(driver, message: str) -> bool`**
- Finds the message input box (`[contenteditable="true"]` at bottom of chat)
- Uses **clipboard paste** to preserve formatting (bold text, links):
  - Copies the HTML message to clipboard via `pyperclip` or JS `navigator.clipboard`
  - Focuses the input box, then simulates Ctrl+V to paste
  - Telegram Web's `contenteditable` editor renders HTML paste natively (bold stays bold)
- Presses Enter to send
- Verifies the message appeared in the chat (checks for new message bubble)

**Formatting preserved:** The same HTML output from `format_message` (bold title, summary, "Click here" link) is pasted directly. Telegram Web's editor handles HTML clipboard content and preserves bold/link formatting -- no format conversion needed.

## Task 3: Add config to `telegram_news_bot/utils/config.py`

- Add `TELEGRAM_WEB_ENABLED = os.getenv("TELEGRAM_WEB_ENABLED", "true").lower() == "true"`
- Add `CHROME_PROFILE_DIR` pointing to `PROJECT_ROOT / "telegram_news_bot" / ".chrome_profile"`
- Chrome always runs in visible mode (no headless config needed)

## Task 4: Update `dispatcher.py` -- `post_to_telegram` function

Current flow:
```
asyncio.run(_send_telegram()) -> if fails -> _try_http_fallback()
```

New flow:
```
if TELEGRAM_WEB_ENABLED:
    try send_via_telegram_web(message, channel_name)
    if success -> return success
    if fails -> fall through to Bot API

Bot API: asyncio.run(_send_telegram()) -> if fails -> _try_http_fallback()
```

Key change: `post_to_telegram` needs the **channel name** in addition to `chat_id`. Update the call site in `dispatch_all` (line 299) to pass `channel['name']` alongside `chat_id`.

## Task 5: Update `dispatch_all` call to pass channel name

Change line 299 from:
```python
result = post_to_telegram(message, chat_id)
```
to:
```python
result = post_to_telegram(message, chat_id, channel_name=channel.get('name', ''))
```

## Task 6: First-run manual login

Chrome always opens visibly, so the first-run login is seamless:
1. Selenium opens Chrome (visible window)
2. Navigates to web.telegram.org
3. User scans QR code to log in
4. Session saved to `.chrome_profile/`
5. On subsequent runs, Chrome opens already logged in (no QR needed)

Add a `--login-telegram` CLI flag to `run.py` that launches Chrome and waits for the user to complete login before proceeding.

## Task 7: Update `.gitignore`

- Add `.chrome_profile/` to avoid committing browser session data

## Files Modified

| File | Change |
|---|---|
| `requirements.txt` | Add selenium, webdriver-manager, pyperclip |
| `telegram_news_bot/services/telegram_web.py` | NEW -- Selenium automation |
| `telegram_news_bot/utils/config.py` | Add TELEGRAM_WEB_ENABLED, CHROME_PROFILE_DIR |
| `telegram_news_bot/services/dispatcher.py` | Update post_to_telegram, dispatch_all |
| `run.py` | Add --login-telegram flag |
| `.gitignore` | Add .chrome_profile/ |

## Fallback Chain (after changes)

```
1. Selenium + Telegram Web (primary, visible Chrome)
   -> fail
2. Bot API direct connection
   -> fail
3. Bot API via SOCKS5 proxy
   -> fail
4. Bot API via HTTP proxy
   -> fail
5. Bot API raw HTTP requests.post (last resort)
```
