import { Calendar } from 'primereact/calendar';
import AuthorizationService from '../Services/AuthorizationService';

import '../Styles/analyticsRep.css';
import '../Styles/header.css';
import { Dropdown } from 'primereact/dropdown';

const ReportHeaderComponent = ( dates, setDates, CorBFilter, setCorBFilter, setPage ) => {
    
    const authService = new AuthorizationService();

    const items = [
                {
                    label : 'All Filters Table',
                    icon: 'pi pi-search',
                    command: ()=>{
                        setPage('All Filters Table')
                    },
                    section: "Basic",
                },
                {
                    label: 'All Transactions',
                    icon: 'pi pi-table',
                    command: () => {
                        setPage('All Transactions');
                    },
                    section: "Basic",
                },
                {
                    label: 'In_Branch Originated Report',
                    icon: 'pi pi-building',
                    command: () => {
                        setPage('BOR');
                    },
                    section: "Reports",
                },
                {
                    label: 'Business Deposits Report',
                    icon: 'pi pi-briefcase',
                    command: () => {
                        setPage('Business Deposit Reports');
                    },
                    section: "Reports",
                },
                {
                    label: 'Abandonment Report',
                    icon: 'pi pi-ban',
                    command: () => {
                        setPage('Abandonment Report');
                    },
                    section: "Reports",
                },
                {
                     label: 'Spot & Current Balance Amounts',
                    icon: 'pi pi-download',
                    command: () => {
                        setPage('Spot & Current Balance Amounts');
                    },
                    section: "Loans & Deposits Reports",
                },
                {
                    label: 'Loan Commitments',
                    icon: 'pi pi-credit-card',
                    command: () => {
                        setPage('Loan Commitments');
                    },
                    section: "Loans & Deposits Reports",
                },
                {
                    
                    label: 'Customer Document Center',
                    icon: 'pi pi-file',
                    command: () => {
                        setPage('Customer Document Center');
                    },
                    section: "Document Center",
                },
                {
                    label: 'Analytics',
                    icon: 'pi pi-chart-line',
                    command: () => {
                        setPage('Graphs');
                    },
                    section: "YTD & Quarterly Analytics",
                },
                {
                    label: 'Declined Report',
                    icon: 'pi pi-times',
                    command: () => {
                        setPage('Declined Report');
                    },
                    section: "Customer & Product Reports",
                },   
                
                {
                    label: 'New vs Existing Customers',
                    icon: 'pi pi-user-plus',
                    command: () => {
                        setPage('New vs Exisitng Customers');
                    },
                    section: "Customer & Product Reports",
                },
                {
                    label: 'Monthly Report',
                    icon: 'pi pi-calendar',
                    command: () => {
                        setPage('Monthly Report');
                    },
                    section: "Reports",
                },                
                {
                    label : 'Multi Product Reports',
                    icon: 'pi pi-th-large',
                    command: ()=>{
                        setPage('Multi Product Reports')
                    },
                    section: "Customer & Product Reports",
                },
                {
                    label: 'Funding Type Report',
                    icon: 'pi pi-dollar',
                    command: () => {
                        setPage('Funding Type Report');
                    },
                    section: "Customer & Product Reports",
                },
                {
                    label: 'Lending & Deposit Control Report',
                    icon: 'pi pi-book',
                    command: () => {
                        setPage('Lending & Deposit Control Report');
                    },
                    section: "Customer & Product Reports",
                },
                
                {
                template: () => (
                    <Calendar 
                        value={dates} 
                        onChange={(e) => setDates(e.value)} 
                        selectionMode="range" 
                        readOnlyInput 
                        hideOnRangeSelection
                        showIcon 
                        showButtonBar 
                        placeholder="Select dates" 
                        style={{ width: '200px' }}
                        className="align-right p-button-text" 
                    />
                ),
            },
            {
                template: () => (
                    <Dropdown
                            value={CorBFilter}
                            options={[
                                { label: 'All', value: 'All' },
                                { label: 'Consumer', value: 'Consumer' },
                                { label: 'Business', value: 'Business' }
                            ]}
                            onChange={(e) => setCorBFilter(e.value)}
                            placeholder="Select Consumer or Business Filter"
                            className="align-right p-button-text"
                            onSelect={(e) => setCorBFilter(e.value)}
                        />
                ),
            },
            {
                    label: 'Profile'+ (localStorage.getItem("display_name") == "" ? "": ": "+localStorage.getItem("display_name")),
                    icon: 'pi pi-user',
                    section: "Basic",
                },
            {
                        label: 'Sign Out',
                        icon: 'pi pi-sign-out',
                        command: () => {
                            authService.logout();
                        },
                    },
    ];

    return items;
};

export default ReportHeaderComponent;


