import { Calendar } from 'primereact/calendar';

import '../Styles/analyticsRep.css';
import '../Styles/header.css';
import { Dropdown } from 'primereact/dropdown';

const ReportHeaderComponent = ( dates, setDates, CorBFilter, setCorBFilter, setPage ) => {
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
                    label: 'Transaction Logger',
                    icon: 'pi pi-search',
                    command: ()=>{
                        setPage('Transaction Logger')
                    },
                    section: "Basic"
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
                    label: 'Business Deposits and Loans Report',
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
                    label: 'PennState University Banking Reports',
                    icon: 'pi pi-building',
                    command: () => {
                        setPage('PennState University Banking Reports');
                    },
                    section: "Reports",
                },
                
                {
                    label: 'Bot Generated Reports',
                    icon: 'pi pi-android',
                    command: () => {
                        setPage('Bot Generated Reports');
                    },
                    section: "Reports",
                },
                // Business Account Summary
                {
                    label: 'Business Accounts Summary',
                    icon: 'pi pi-briefcase',
                    command: () => {
                        setPage('Business Accounts Summary');
                    },
                    section: "Reports",
                },
                {
                    label: "Payment Switch Reports",
                    icon: 'pi pi-credit-card',
                    command: () => {
                        setPage('Payment Switch Reports');
                    },
                    section: "Loans & Deposits Reports",
                },
                {
                     label: 'Spot And Current Balance Amounts',
                    icon: 'pi pi-download',
                    command: () => {
                        setPage('Spot And Current Balance Amounts');
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
                    label: 'Direct Deposit Switch',
                    icon: 'pi pi-credit-card',
                    command: () => {
                        setPage('Direct Deposit Switch');
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
                    label: 'Business String Decryption',
                    icon: 'pi pi-lock',
                    command: () => setPage('Business String Decryption'),
                    section: "Tools",
                },
                {
                    label: 'Crypto & Key Rotation',
                    icon: 'pi pi-lock',
                    command: () => setPage('Crypto & Key Rotation'),
                    section: 'Administration',
                },
                {
                    label: 'CSV Loader Reports',
                    icon: 'pi pi-file-excel',
                    command: () => {
                        setPage('CSV Loader Reports');
                    },
                    section: "Reports",
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
                    label: 'E-Delivery Report',
                    icon: 'pi pi-user-minus',
                    command: () => {
                        setPage('E-Delivery Report');
                    },
                    section: "Reports",
                },
                {
                    label: 'E Delivery Report LOB',
                    icon: 'pi pi-user-minus',
                    command: () => {
                        setPage('E Delivery Report LOB');
                    },
                    section: "Reports",
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
                    label : 'Cross Sell Reports',
                    icon: 'pi pi-th-large',
                    command: ()=>{
                        setPage('Cross Sell Reports')
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
                    label: 'Student Checking Report',
                    icon: 'pi pi-user',
                    command: () => {
                        setPage('Student Checking Report');
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
    ];

    return items;
};

export default ReportHeaderComponent;


