# API Documentation

## Overview

The eStore API is a Flask-based REST service that provides endpoints for data retrieval, chart generation, authentication, and system management.

## Authentication

The API supports two authentication methods:

1. **JWT Token**: Bearer token in Authorization header
2. **API Key**: `X-API-KEY` header only; URL and JSON body API keys are not accepted. LDAP/MSAL login stays unchanged.

## Endpoints

### Core Data Endpoints

#### GET / - Get Transactions by Date Range
Retrieves all transactions between specified dates.

**Parameters:**
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format

**Authentication:** JWT token required

**Response:** JSON array of transactions filtered by user role

#### GET /charts/{name} - Get Chart Data
Generates and returns chart data for specified chart type.

**Parameters:**
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format
- Additional parameters vary by chart type

**Authentication:** Login token or `X-API-KEY` header

**Response:** JSON object with chart data

### Authentication Endpoints

#### POST /login - User Login
Authenticates user via LDAP and returns JWT token.

**Request Body:**
```json
{
  "email": "user@domain.com",
  "password": "password"
}
```

**Response:**
```json
{
  "token": "jwt_token_here",
  "role": "user_role"
}
```

#### GET /logout - User Logout
Invalidates user session.

#### GET /msalConfig - MSAL Configuration
Returns Azure MSAL configuration for frontend authentication.

### System Management Endpoints

#### GET /generate_cache - Generate Cache
Triggers cache generation for all logged chart URLs.

**Authentication:** Required

#### GET /clear_cache - Clear Cache
Clears all cached data.

**Authentication:** Required

#### GET /refill_database - Refill Database
Reprocesses and reloads data into database.

**Authentication:** Required

#### GET /uptospeed - System Status
Returns system synchronization status.

**Authentication:** Required

#### GET /xml_pull - XML Data Pull
Triggers XML data extraction from Journey Manager.

**Authentication:** Required

### Utility Endpoints

#### POST /query - Custom Query
Executes custom database queries.

**Request Body:**
```json
{
  "query": "SELECT * FROM table",
  "params": {}
}
```

**Authentication:** Required

#### GET /show_metrics - System Metrics
Returns system performance metrics.

**Authentication:** Required

#### GET /cache - Cache Status
Returns cache statistics and contents.

**Authentication:** Required

#### GET /show_logs/{filename} - View Logs
Returns contents of specified log file.

**Parameters:**
- `filename`: Name of log file to retrieve

**Authentication:** Required

### Webhook Endpoints

#### POST /webhook/atomic/non_eca_dds_data - Non-ECA DDS Data Webhook
Receives webhook data for non-ECA DDS processing.

**Request Body:** JSON payload with `ce_id` field

**Response:**
```json
{
  "message": "Data received successfully"
}
```

### Chart Builder Endpoint

#### GET/POST /chart_builder - Chart Builder
Dynamic chart generation endpoint.

**Parameters:** Varies based on chart requirements

**Authentication:** Required

## Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (missing parameters)
- `401`: Unauthorized (invalid credentials)
- `403`: Forbidden (insufficient permissions)
- `500`: Internal Server Error

Error responses include a JSON object with an `error` field containing the error message.

## Rate Limiting

The API implements rate limiting to prevent abuse. Chart endpoints are coordinated to prevent duplicate processing.

## Caching

Most data endpoints utilize Redis caching. Cache keys are generated based on endpoint parameters. Cache can be manually cleared via the `/clear_cache` endpoint.

## Data Formats

- **Dates**: All dates use YYYY-MM-DD format
- **Numbers**: Formatted with commas by default (configurable)
- **Responses**: JSON format for all endpoints
- **File Exports**: CSV format for insight reports

## Security

- All endpoints validate authentication
- Role-based data filtering applied
- SQL injection prevention via parameterized queries
- Input validation on all parameters
- HTTPS recommended for production

## Performance

- Redis caching for frequently accessed data
- Database connection pooling
- Asynchronous chart processing for complex queries
- Metrics collection for monitoring