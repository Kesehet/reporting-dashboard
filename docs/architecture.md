# System Architecture

## Overview

The eStore Digital Reporting System is a web-based analytics platform that integrates multiple data sources to provide comprehensive reporting and visualization capabilities for financial transactions.

## High-Level Architecture

```mermaid
graph TB
    A[Journey Manager API] --> B[Data Extraction Service]
    C[CSV/Excel Uploads] --> B
    B --> D[ETL Processing]
    D --> E[SQL Server Database]
    E --> F[Flask REST API]
    F --> G[Redis Cache]
    G --> H[React Frontend]
    I[LDAP Server] --> F
    J[Azure MSAL] --> H
```

## Data Flow

### Transaction Data Ingestion

```mermaid
sequenceDiagram
    participant JM as Journey Manager
    participant API as Flask API
    participant DB as SQL Server
    participant Cache as Redis Cache

    API->>JM: Request transaction data
    JM-->>API: XML response
    API->>API: Parse XML to JSON
    API->>DB: Insert into JMExtract table
    API->>Cache: Update cached data
```

### CSV Processing Flow

```mermaid
flowchart TD
    A[File Upload] --> B{File Type?}
    B -->|CSV| C[Detect Encoding]
    B -->|Excel| D[Read Excel]
    C --> E[Parse with pandas]
    D --> E
    E --> F[Data Validation]
    F --> G[Apply Business Rules]
    G --> H[Insert to Database]
    H --> I[Update Metrics]
```

### User Request Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend as React App
    participant API as Flask API
    participant Cache as Redis
    participant DB as SQL Server

    User->>Frontend: Request dashboard
    Frontend->>API: API call with JWT
    API->>API: Verify token
    API->>Cache: Check cache
    alt Cache hit
        Cache-->>API: Return cached data
    else Cache miss
        API->>DB: Query database
        DB-->>API: Return data
        API->>Cache: Store in cache
    end
    API->>API: Apply role filtering
    API-->>Frontend: JSON response
    Frontend-->>User: Render charts
```

## Component Details

### Frontend (React Application)
- **Framework**: React 18.2.0 with hooks
- **UI Library**: PrimeReact components
- **Charts**: Chart.js with react-chartjs-2
- **Authentication**: Azure MSAL Browser
- **State Management**: React state with context

### Backend (Flask API Server)
- **Framework**: Flask 3.0.3 with CORS
- **Authentication**: JWT tokens with LDAP validation
- **Database**: SQL Server via pyodbc
- **Caching**: Redis for performance
- **XML Processing**: lxml library
- **File Processing**: pandas for CSV/Excel

### Database Layer
- **Primary DB**: SQL Server with encrypted connections
- **Tables**:
  - JMExtract: Raw Journey Manager data
  - Transactions: Processed transaction data
  - Users: User management and roles
  - Metrics: System performance data

### Caching Layer
- **Technology**: Redis
- **Purpose**: Cache chart data and API responses
- **Invalidation**: Time-based and manual clearing
- **Pre-generation**: cache_gen.exe for proactive caching

### Executable Components
- **serve.exe**: Main Flask server
- **csvLoader.exe**: Batch CSV processing
- **cache_gen.exe**: Cache pre-generation

## Security Architecture

```mermaid
graph TD
    A[User Login] --> B{LDAP Auth}
    B -->|Success| C[Generate JWT]
    B -->|Fail| D[Access Denied]
    C --> E[API Requests]
    E --> F{Validate JWT}
    F -->|Valid| G[Role-based Filtering]
    F -->|Invalid| D
    G --> H[Data Access]
```

## Deployment Architecture

```mermaid
graph TD
    A[Azure Pipelines] --> B[Build React App]
    A --> C[Build Python Executables]
    B --> D[Deploy Frontend]
    C --> E[Deploy Backend Services]
    F[SQL Server] --> E
    G[Redis] --> E
    H[LDAP] --> E
```

## Performance Considerations

- **Caching Strategy**: Redis cache for frequently accessed data
- **Database Optimization**: Indexed queries and connection pooling
- **File Processing**: Streaming for large CSV files
- **API Rate Limiting**: Built-in request throttling
- **Metrics Collection**: Performance monitoring and alerting

## Scalability

- **Horizontal Scaling**: Multiple API server instances
- **Database Sharding**: Partitioning for large datasets
- **Cache Distribution**: Redis cluster for high availability
- **Load Balancing**: Distribute requests across servers