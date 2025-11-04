# API Documentation

**Schema Version:** 1.0.0  
**Generated:** 2025-11-05T00:11:46.315719  

This documentation is auto-generated from `schema/metrics_schema.yaml`.

---

## Base URL

```
http://localhost:5000
```

## Endpoints

### `GET /api/servers/metrics/latest`

Get latest metrics for all servers

---

### `GET /api/servers/<server_name>/metrics/historical/<hours>`

Get historical metrics for specific server

---

### `GET /api/servers/<server_name>/status`

Get current status of specific server

---

### `GET /api/servers/list`

List all available servers

---

### `GET /api/users/top`

Get top users across all servers

---

### `GET /api/users/top/<server_name>`

Get top users for specific server

---

### `GET /api/system/overview`

Real-time system statistics and trends

---

### `GET /api/health`

API health check

---
