# Owlet Polling Fix

## Problem
The Owlet device polling was failing with the following issues:

1. **Django ORM in Async Context Error**: The main issue was that Django ORM operations (like `account.save()`) were being called directly from within an async context, which Django doesn't allow.

2. **Unclosed aiohttp Sessions**: The `OwletAPI` class was creating aiohttp sessions but not properly cleaning them up, leading to resource leaks and warnings.

3. **Silent Exception Handling**: Exceptions were being caught and silently ignored, making it impossible to diagnose the actual problem.

## Solution

### 1. Fixed Django ORM Async Context Issue
**File**: [`babybuddy/services/owlet_client.py`](babybuddy/services/owlet_client.py)

- Added `from asgiref.sync import sync_to_async` import
- Wrapped the `account.save()` call with `sync_to_async()`:
  ```python
  await sync_to_async(self.account.save)(update_fields=[
      "refresh_token_encrypted",
      "last_auth_at",
  ])
  ```

This allows Django ORM operations to be safely called from async code.

### 2. Fixed aiohttp Session Cleanup
**File**: [`pyowletapi/src/pyowletapi/api.py`](pyowletapi/src/pyowletapi/api.py)

- Added `_session_provided` flag to track whether the session was provided externally or created internally
- Modified `close()` method to only close sessions that were created internally:
  ```python
  async def close(self) -> None:
      """Closes the aiohttp ClientSession only if we created it."""
      if self.session and not self._session_provided:
          await self.session.close()
          # Give the underlying connections time to close
          await asyncio.sleep(0.25)
  ```

This prevents closing sessions that are managed externally and adds a small delay to allow connections to properly close.

### 3. Added Error Logging
**File**: [`babybuddy/services/owlet_poll.py`](babybuddy/services/owlet_poll.py)

- Added logging import
- Changed silent exception handling to log errors:
  ```python
  except Exception as e:
      logger.error(f"Error polling Owlet account {account.id}: {e}", exc_info=True)
      continue
  ```

This makes it much easier to diagnose issues in the future.

## Results

After the fix:
- ✅ Polling endpoint returns: `{"accounts":1,"devices":1,"readings":0}`
- ✅ Device is successfully discovered and stored in the database
- ✅ No more worker timeouts
- ✅ No more unclosed session warnings
- ✅ Errors are properly logged for debugging

## Next Steps

To see readings (not just devices), you need to:
1. Navigate to the Owlet settings page: http://localhost:8001/owlet/settings/account/1/devices
2. Map the discovered device to a child
3. Run the poll again - readings will then be captured

The reason readings are 0 is that the code only creates readings for devices that have been mapped to a child (see line 221-223 in [`owlet_poll.py`](babybuddy/services/owlet_poll.py:221)).
