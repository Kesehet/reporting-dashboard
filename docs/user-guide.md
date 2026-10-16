# User Guide

## Overview

eStore is a web-based digital reporting platform designed for financial institutions to manage, analyze, and visualize loan commitment data and related transactions.

## Getting Started

### System Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- Valid user credentials

### Accessing the Application

1. Open your web browser
2. Navigate to the eStore application URL
3. Click "Sign In" to authenticate
4. Enter your corporate credentials
5. Select your authentication method (if prompted)

## User Interface Overview

### Main Dashboard
The dashboard provides an overview of key metrics and recent activity:
- **Transaction Summary**: Total transactions by status
- **Recent Activity**: Latest application submissions
- **Performance Metrics**: System health indicators

### Navigation Menu
- **Dashboard**: Main overview page
- **Reports**: Access to various report types
- **Charts**: Interactive data visualizations
- **Data Upload**: CSV/Excel file upload interface
- **Settings**: User preferences and configuration

## Working with Reports

### Generating Reports

1. Navigate to the Reports section
2. Select a report type from the dropdown
3. Set date range filters
4. Apply additional filters as needed
5. Click "Generate Report"

### Report Types

#### Transaction Reports
- **Application Status Report**: Shows applications by current status
- **Branch Performance Report**: Performance metrics by branch
- **Product Analysis Report**: Analysis by product types

#### Financial Reports
- **Funding Summary**: Total funding amounts by period
- **Approval Rates**: Application approval statistics
- **Decline Analysis**: Reasons for application declines

### Exporting Reports

1. Generate the desired report
2. Click the "Export" button
3. Select export format (CSV or PDF)
4. Choose download location
5. Click "Download"

## Data Visualization

### Chart Types

#### Bar Charts
- Compare values across categories
- Show trends over time
- Display frequency distributions

#### Line Charts
- Track changes over time
- Show trends and patterns
- Compare multiple series

#### Pie Charts
- Show proportional data
- Display category breakdowns
- Illustrate composition

### Interacting with Charts

#### Filtering Data
- Use date range selectors
- Apply category filters
- Drill down into specific segments

#### Zooming and Panning
- Use mouse wheel to zoom
- Drag to pan across time periods
- Double-click to reset zoom

#### Exporting Charts
- Click "Export" button on chart
- Choose image format (PNG, JPEG, PDF)
- Set resolution and dimensions

## Data Upload

### Supported File Formats
- **CSV**: Comma-separated values
- **Excel**: .xlsx and .xls formats
- **Text**: Tab-delimited files

### Upload Process

1. Navigate to Data Upload section
2. Click "Choose File" or drag and drop files
3. Select file encoding if prompted
4. Review column mappings
5. Click "Upload" to process

### Data Validation

The system automatically validates uploaded data:
- **Required Fields**: Ensures mandatory columns are present
- **Data Types**: Validates data formats (dates, numbers, etc.)
- **Business Rules**: Applies business logic validation
- **Duplicate Detection**: Identifies potential duplicate records

### Upload Status

Monitor upload progress:
- **Processing**: File is being validated and parsed
- **Validating**: Business rules are being applied
- **Loading**: Data is being inserted into database
- **Complete**: Upload finished successfully
- **Error**: Issues encountered during upload

## User Management

### Profile Settings

#### Updating Profile
1. Click your name in the top-right corner
2. Select "Profile"
3. Update personal information
4. Save changes

#### Changing Password
1. Go to Profile settings
2. Click "Change Password"
3. Enter current and new passwords
4. Confirm changes

### Role-Based Access

Access levels determine what data and features are available:

#### Viewer Role
- View reports and charts
- Export data
- Basic dashboard access

#### Analyst Role
- All Viewer permissions
- Advanced filtering options
- Custom report creation

#### Administrator Role
- All Analyst permissions
- User management
- System configuration
- Data upload capabilities

## Advanced Features

### Custom Queries

For advanced users, custom SQL queries can be executed:

1. Navigate to Advanced > Query Builder
2. Select data source
3. Write or select predefined queries
4. Execute and view results
5. Export query results

### API Access

#### API Key Generation
1. Go to Settings > API Access
2. Click "Generate API Key"
3. Copy and securely store the key
4. Use key for programmatic access

#### API Documentation
- Access API docs at `/api/docs`
- View available endpoints
- Test API calls interactively

### Scheduled Reports

#### Setting Up Schedules
1. Create a report template
2. Go to Settings > Scheduled Reports
3. Select report and frequency
4. Set delivery options (email, file share)
5. Save schedule

#### Managing Schedules
- View active schedules
- Edit schedule parameters
- Pause/resume schedules
- Delete unused schedules

## Troubleshooting

### Common Issues

#### Login Problems
- **Invalid Credentials**: Verify username and password
- **Account Locked**: Contact system administrator
- **Network Issues**: Check internet connection

#### Report Generation Issues
- **No Data**: Check date range and filters
- **Timeout**: Reduce date range or apply more filters
- **Permission Denied**: Verify user role permissions

#### Upload Issues
- **File Format**: Ensure supported file type
- **Encoding**: Try different file encodings
- **Size Limits**: Check file size restrictions

### Getting Help

#### Self-Service Resources
- **Help Center**: Access built-in help documentation
- **Video Tutorials**: Watch guided walkthroughs
- **FAQ**: Search common questions and answers

#### Contacting Support
- **Email**: support@estore.com
- **Phone**: 1-800-ESTORE
- **Chat**: Live chat available during business hours

## Best Practices

### Data Management
- Regularly review and clean up old data
- Use consistent naming conventions
- Validate data before uploading
- Archive completed transactions

### Performance Optimization
- Use date filters to limit data volume
- Schedule heavy reports during off-peak hours
- Clear browser cache regularly
- Use export features for large datasets

### Security Practices
- Never share login credentials
- Log out when not using the system
- Use strong, unique passwords
- Report suspicious activity immediately

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+F | Search within current page |
| Ctrl+R | Refresh current page |
| Esc | Close modal dialogs |
| Alt+H | Open help menu |
| Ctrl+E | Export current view |

## Glossary

### Common Terms

- **eCA**: Electronic Customer Application
- **JM**: Journey Manager (external system)
- **DDS**: Direct Deposit Switch
- **NMLS**: Nationwide Mortgage Licensing System
- **SSN**: Social Security Number
- **CSV**: Comma-Separated Values
- **API**: Application Programming Interface

### Status Definitions

- **Submitted**: Application submitted for processing
- **Under Review**: Application being reviewed
- **Approved**: Application approved for funding
- **Declined**: Application declined
- **Funded**: Application fully funded

## Release Notes

### Version 2.0
- Enhanced chart visualization
- Improved data upload performance
- New API endpoints
- Security enhancements

### Version 1.5
- Role-based access control
- Scheduled reporting
- Mobile responsiveness
- Performance optimizations

### Version 1.0
- Initial release
- Basic reporting functionality
- User authentication
- Data visualization