---
# eStore - Digital Reporting System

The application source was refreshed from the supplied ZIP on October 16, 2026.
See [snapshot import notes](docs/snapshot-import.md) for the import scope,
configuration setup, and validation results. Copy `.env.example` to `.env`
and configure it locally before starting the backend.

See [Business String Decryption](docs/business-string-decryption.md) for the privileged operator tool, AES-GCM format, deployment configuration, and regression tests.

## Overview

eStore is a comprehensive digital reporting and analytics platform designed for financial institutions to manage, visualize, and report on loan commitments and related transactions. The system integrates with Journey Manager APIs to extract transaction data, processes CSV/Excel uploads, and provides interactive dashboards with charts and export capabilities.

## Architecture

The application consists of:
- **Frontend**: React-based web application with Chart.js for data visualization
- **Backend**: Flask REST API server with SQL Server database
- **Authentication**: LDAP integration with JWT tokens and Azure MSAL
- **Data Processing**: Automated ETL processes for transaction data
- **Caching**: Redis-based caching system for performance optimization

## Core Processes

### 1. Data Extraction and Loading
- **Journey Manager Integration**: Pulls transaction data via REST API calls to Journey Manager
- **XML Processing**: Parses form XML data and stores in JMExtract table
- **CSV/Excel Upload**: Processes uploaded files with automatic encoding detection and data validation
- **Transaction Processing**: Applies business rules and post-processing to transaction data

### 2. Data Storage and Management
- **SQL Server Database**: Stores processed transactions, user data, and metadata
- **Caching Layer**: Redis cache for frequently accessed chart data and reports
- **Metrics Tracking**: System performance and usage metrics collection

### 3. Reporting and Visualization
- **Dynamic Chart Generation**: Automatic chart type inference based on data structure
- **Interactive Dashboards**: Web-based interface for data exploration
- **Export Functionality**: CSV export for reports and insights

### 4. Security and Access Control
- **LDAP Authentication**: User authentication against corporate directory
- **Role-Based Access**: Filtered data access based on user roles
- **JWT Tokens**: Secure API authentication

## Executable Components

The system includes standalone executables for key processes:

### cache_gen.exe
- **Purpose**: Pre-generates cache for chart data to improve application performance
- **Function**: Reads logged chart URLs and pings API endpoints to populate cache
- **Usage**: Run periodically or before peak usage times

### csvLoader.exe
- **Purpose**: Processes CSV/Excel files uploaded to the system
- **Function**: Validates, transforms, and loads transaction data into database
- **Usage**: Triggered by file uploads or scheduled batch processing

### serve.exe
- **Purpose**: Runs the Flask API server
- **Function**: Serves REST API endpoints for frontend and external integrations
- **Usage**: Main application server, runs continuously

## How It Works

1. **Data Ingestion**:
   - System polls Journey Manager API for new transactions
   - XML data is parsed and stored in staging tables
   - CSV files are uploaded and processed through ETL pipeline

2. **Data Processing**:
   - Business rules applied to normalize and validate data
   - Account numbers, product IDs, and branch codes are processed
   - Metrics and audit logs are generated

3. **User Interaction**:
   - Users authenticate via LDAP/Azure MSAL
   - Frontend requests data through cached API calls
   - Charts are dynamically generated based on data types
   - Reports can be exported to CSV format

4. **Caching and Performance**:
   - Frequently accessed data is cached in Redis
   - Cache generation can be run as background process
   - Metrics help monitor system performance

## Technology Stack

### Frontend
- React 18.2.0
- Chart.js 4.4.2
- PrimeReact 10.6.4
- Azure MSAL for authentication

### Backend
- Python 3.x
- Flask 3.0.3
- SQL Server with pyodbc
- Redis for caching
- LDAP3 for authentication

### Infrastructure
- Azure Pipelines for CI/CD
- Docker for containerization
- PyInstaller for executable generation

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 19.x
- SQL Server database
- Redis cache server
- Journey Manager API access

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd eStore
   ```

2. **Backend Setup**
   ```bash
   cd api-server
   pip install -r ../requirements.txt
   # Configure environment variables in .env file
   ```

3. **Frontend Setup**
   ```bash
   npm install
   npm run build
   ```

4. **Database Setup**
   - Ensure SQL Server is running
   - Run database migrations if available
   - Configure connection strings in environment

### Running the Application

1. **Start Backend Server**
   ```bash
   python api-server/serve.py
   # or use serve.exe
   ```

2. **Start Frontend**
   ```bash
   npm start
   ```

3. **Build Executables** (optional)
   ```bash
   # Use PyInstaller or provided build scripts
   ./py_build.sh
   ```

## Configuration

Key environment variables:
- `REACT_APP_API_SERVER_BASE_URL`: Backend API URL
- `SQL_HOST`, `SQL_DATABASE`: Database connection
- `REACT_APP_JOURNEY_MANAGER_USER`: JM API credentials
- `RELAY_SERVER_SECRET`: JWT secret key

## Documentation

Detailed documentation is available in the `docs/` folder:
- [System Architecture](docs/architecture.md) - Complete system overview and data flows
- [API Documentation](docs/api-docs.md) - REST API endpoints and usage
- [Database Schema](docs/database-schema.md) - ER diagrams and table structures  
- [Deployment Guide](docs/deployment.md) - Installation and configuration
- [User Guide](docs/user-guide.md) - Usage instructions and best practices

## Development

### Running Tests
```bash
npm run test
```

### Building for Production
```bash
npm run build
```

### CI/CD
The project uses Azure Pipelines for automated builds and deployments. See `azure-pipelines.yml` for pipeline configuration.

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new features
3. Update documentation as needed
4. Ensure all CI checks pass

## License

[Add license information here]

---

**Note**: This application has hardcoded staging URL values in `api-server/application.py` that should be updated for production use.


### Authentication (restored)

The dashboard again provides the original **LDAP username/password** and **Microsoft SSO** options. LDAP creates short-lived JWTs using `RELAY_SERVER_SECRET`; Microsoft MSAL validates signed ID tokens using Azure's published signing keys and the configured tenant/client ID. Chart endpoints require either a valid sign-in token (`Authorization`) or the existing `ALL_FILTERS_CHART_API_KEY`, sent in the `X-API-KEY` header only. Daily API keys are signed from the UTC date and private `ALL_FILTERS_CHART_API_KEY` secret, changing at 00:00 UTC. Signed-in users can copy the current key from the API Key tab. The secret itself is no longer an API credential. URL and JSON body `api_key` parameters no longer authenticate requests. The cache generator uses the header rather than exposing the key in URLs. Configuration stays in the deployed `.env` file; no live credentials are included in Git. Set `REACT_APP_AZURE_CLIENT_ID`, `REACT_APP_AZURE_TENANT_ID`, and `REACT_APP_FE_SERVER_BASE_URL` for Microsoft login. LDAP retains the original MYFNB directory defaults, overridable with `LDAP_SERVER_URL`, `LDAP_DOMAIN`, and `LDAP_SEARCH_BASE`. Deploy from a trusted environment and verify both providers against real services before enabling production access.
