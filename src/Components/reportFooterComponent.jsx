import React from 'react';
import logo from '../Images/FNBlogo.PNG';

const ReportFooterComponent = () => {
    return (
        <div className="p-d-flex p-ai-center p-jc-center" style={{ backgroundColor: "#f8f9fa", padding: '10px' }}>
            <div className="p-d-flex p-ai-center" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <img src={logo} alt="First National Bank, Pennsylvania Logo" style={{ width: '50px', marginRight: '10px' }} />
                <p style={{ margin: 0 }}>First National Bank | Pittsburgh, PA ©{new Date().getFullYear()}</p>
            </div>
        </div>
    );
};

export default ReportFooterComponent;
