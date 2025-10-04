# Frontend Improvements - Developer Guide

This document explains the recent improvements to the Frontend codebase and how to use the new utilities.

---

## New Modules

### 1. `exceptions.py` - Custom Exception Hierarchy

Use these exceptions for better error handling:

```python
from exceptions import APIConnectionError, APITimeoutError, ValidationError

# Raise specific exceptions
raise APIConnectionError("Failed to connect to API")
raise ValidationError("Invalid server name", details={'name': name})
```

**Available Exceptions:**
- `DashboardException` - Base exception
- `APIException` - Base for API errors
- `APIConnectionError` - Connection failures
- `APITimeoutError` - Request timeouts
- `APIResponseError` - HTTP error responses
- `APIDataError` - Invalid response data
- `DataProcessingError` - Data processing failures
- `ValidationError` - Input validation failures
- `ConfigurationError` - Configuration errors

---

### 2. `cache_utils.py` - Caching System

**Using the cache decorator:**

```python
from cache_utils import cached

@cached(ttl_seconds=900, key_prefix="mydata_")
def get_expensive_data(param1, param2):
    # This function's result will be cached for 15 minutes
    return fetch_data_from_api(param1, param2)
```

**Manual cache management:**

```python
from cache_utils import get_cache, invalidate_cache_pattern

# Get cache instance
cache = get_cache()

# Manually set cache
cache.set("my_key", {"data": "value"}, ttl_seconds=600)

# Get from cache
data = cache.get("my_key")

# Invalidate specific key
cache.invalidate("my_key")

# Invalidate by pattern
invalidate_cache_pattern("server_")  # Invalidates all keys containing "server_"

# Clear all cache
cache.clear()

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")
```

---

### 3. `validation.py` - Input Validation

**Validating inputs:**

```python
from validation import (
    validate_percentage, validate_server_name,
    validate_timestamp, safe_get
)

# Validate percentage (0-100)
cpu_usage = validate_percentage(data['cpu'], 'cpu_usage')

# Validate server name
server = validate_server_name(user_input)

# Parse timestamp (multiple formats supported)
dt = validate_timestamp("2025-10-01T12:30:45")

# Safe dictionary access with validation
value = safe_get(
    dictionary=data,
    key='cpu_load',
    default=0.0,
    validator=lambda x: float(x)
)
```

**Validating structures:**

```python
from validation import validate_server_metrics, validate_user_data

# Validate entire metrics dictionary
metrics = validate_server_metrics(raw_metrics)

# Validate user data
user = validate_user_data(raw_user_data)
```

---

### 4. `data_processing.py` - DataFrame Utilities

**Safe DataFrame creation:**

```python
from data_processing import safe_create_dataframe, prepare_historical_dataframe

# Create DataFrame with error handling
df = safe_create_dataframe(data_list, name="server_metrics")

# Prepare historical data (timestamps, numeric conversion, validation)
df = prepare_historical_dataframe(historical_data, "Server1")
```

**Data processing utilities:**

```python
from data_processing import (
    parse_dataframe_timestamps,
    convert_numeric_columns,
    filter_recent_data,
    aggregate_metrics
)

# Parse timestamps
df = parse_dataframe_timestamps(df, column='timestamp')

# Convert to numeric
df = convert_numeric_columns(df, ['cpu', 'memory', 'disk'], fillna=0.0)

# Filter to last 24 hours
df = filter_recent_data(df, timestamp_column='timestamp', hours=24)

# Aggregate across servers
avg_metrics = aggregate_metrics(metrics_list, operation='mean')
```

**Trend analysis:**

```python
from data_processing import calculate_trends, detect_anomalies

# Calculate trend direction
trend = calculate_trends(df, column='cpu_load', window=5)
print(f"Trend: {trend}")  # 'increasing', 'decreasing', or 'stable'

# Detect anomalies (3 std deviations)
anomalies = detect_anomalies(df, column='memory_usage', threshold_std=3.0)
anomaly_count = anomalies.sum()
```

---

## Updated Modules

### `api_client.py` - Enhanced API Client

**All API functions now:**
- Automatically retry on failure (3 attempts with exponential backoff)
- Cache results for 15 minutes
- Validate inputs
- Return empty list/dict on error (never None)
- Log detailed error information

**Manual cache control:**

```python
from api_client import invalidate_all_caches, get_cache_stats

# Invalidate all API caches (on manual refresh)
invalidate_all_caches()

# Get cache performance stats
stats = get_cache_stats()
```

---

### `utils.py` - Enhanced Utilities

**Improved functions:**

```python
from utils import safe_float, determine_server_status, format_uptime

# Safe float conversion with default
value = safe_float(raw_value, default=0.0)

# Status determination (now with validation)
status = determine_server_status(metrics_dict)  # 'online', 'warning', 'offline'

# Format uptime (multiple timestamp formats supported)
uptime_str = format_uptime(boot_time)
```

---

## Error Handling Patterns

### API Calls

```python
from api_client import get_latest_server_metrics
import logging

logger = logging.getLogger(__name__)

# API calls handle errors internally, just check for empty results
metrics = get_latest_server_metrics()

if not metrics:
    logger.warning("No server metrics available")
    # Handle empty case
else:
    # Process metrics
    pass
```

### Data Processing

```python
from data_processing import safe_create_dataframe
from validation import validate_timestamp

# Always use safe utilities
df = safe_create_dataframe(data, name="my_data")

if df.empty:
    logger.warning("Failed to create DataFrame")
    return html.Div("No data available")

# Validate individual values
try:
    dt = validate_timestamp(timestamp_str)
except ValidationError as e:
    logger.error(f"Invalid timestamp: {e}")
    dt = datetime.now()  # Use fallback
```

### Component Rendering

```python
def create_my_component():
    """Create component with error handling"""
    try:
        # Fetch data
        data = get_data_from_api()

        if not data:
            return html.Div("No data available",
                          style={'padding': '20px', 'textAlign': 'center'})

        # Process data
        df = prepare_dataframe(data)

        # Render component
        return html.Div([
            # Component content
        ])

    except Exception as e:
        logger.error(f"Error creating component: {e}", exc_info=True)
        return html.Div(
            "An error occurred while loading this component",
            style={'color': 'red', 'padding': '20px'}
        )
```

---

## Best Practices

### 1. Always Use Validation

```python
# ❌ Bad - No validation
cpu = float(data['cpu'])

# ✅ Good - With validation
from validation import safe_get
cpu = safe_get(data, 'cpu', default=0.0, validator=float)
```

### 2. Use Type Hints

```python
# ❌ Bad - No type hints
def process_data(data):
    return data

# ✅ Good - With type hints
from typing import List, Dict

def process_data(data: List[Dict]) -> pd.DataFrame:
    return pd.DataFrame(data)
```

### 3. Log Errors Appropriately

```python
import logging
logger = logging.getLogger(__name__)

# ❌ Bad - Silent failure
try:
    result = risky_operation()
except:
    pass

# ✅ Good - Logged with context
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    result = fallback_value
```

### 4. Use Safe DataFrame Operations

```python
# ❌ Bad - No error handling
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['cpu'] = df['cpu'].astype(float)

# ✅ Good - With error handling
from data_processing import safe_create_dataframe, parse_dataframe_timestamps, convert_numeric_columns

df = safe_create_dataframe(data, name="metrics")
df = parse_dataframe_timestamps(df, 'timestamp')
df = convert_numeric_columns(df, ['cpu', 'memory'], fillna=0.0)
```

### 5. Cache Expensive Operations

```python
# ❌ Bad - No caching
def get_heavy_computation(param):
    # Expensive operation
    return result

# ✅ Good - With caching
from cache_utils import cached

@cached(ttl_seconds=600)
def get_heavy_computation(param):
    # Expensive operation
    return result
```

---

## Configuration

### Cache Settings

Edit `api_client.py`:
```python
CACHE_TTL = 900  # 15 minutes
```

### Retry Settings

Edit `api_client.py`:
```python
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2
```

### Timeout Settings

Edit `api_client.py`:
```python
DEFAULT_TIMEOUT = 10  # seconds
```

---

## Debugging

### Enable Debug Logging

```python
import logging

# Set to DEBUG level
logging.basicConfig(level=logging.DEBUG)
```

### View Cache Statistics

```python
from api_client import get_cache_stats

stats = get_cache_stats()
print(f"""
Cache Statistics:
- Hits: {stats['hits']}
- Misses: {stats['misses']}
- Hit Rate: {stats['hit_rate']:.1f}%
- Cached Items: {stats['cached_items']}
""")
```

### Manual Cache Inspection

```python
from cache_utils import get_cache

cache = get_cache()
print(f"Cached items: {len(cache._cache)}")

# List all keys
for key in cache._cache.keys():
    entry = cache._cache[key]
    print(f"Key: {key}, Age: {entry.get_age():.1f}s, Expired: {entry.is_expired()}")
```

---

## Migration Guide

### Updating Existing Code

**Before:**
```python
def get_data():
    try:
        response = requests.get(url)
        return response.json()
    except:
        return []
```

**After:**
```python
from api_client import get_latest_server_metrics

def get_data():
    # Error handling and caching built-in
    return get_latest_server_metrics()
```

**Before:**
```python
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
```

**After:**
```python
from data_processing import safe_create_dataframe, parse_dataframe_timestamps

df = safe_create_dataframe(data, name="my_data")
df = parse_dataframe_timestamps(df, 'timestamp')
```

---

## Common Issues

### Issue: Cache not invalidating
**Solution:** Call `invalidate_all_caches()` on manual refresh

### Issue: Timestamp parsing fails
**Solution:** Use `validate_timestamp()` which supports multiple formats

### Issue: DataFrame empty after processing
**Solution:** Check logs for specific error, use `safe_create_dataframe()`

### Issue: API calls timing out
**Solution:** Increase `DEFAULT_TIMEOUT` or check network connectivity

---

For questions or issues, check:
1. FRONTEND_IMPROVEMENTS_SUMMARY.md
2. FRONTEND_IMPROVEMENT_PLAN.md
3. Module docstrings
4. Application logs

---

**Last Updated:** 2025-10-01
