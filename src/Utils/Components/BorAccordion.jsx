import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const BorAccordion = ({ tab, show, hardShow }) => {
    const [isVisible, setIsVisible] = useState(show);

    useEffect(() => {
        
        if(hardShow) {
            setIsVisible(true);
        } else {
            setIsVisible(show);
        }
    }, [show]);

    return (
        <div className="p-accordion">
            <div className="p-accordion-tab">
                <div
                    className="p-accordion-header"
                    onClick={() => setIsVisible((prev) => !prev)}
                    style={{
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        padding: '10px',
                        border: '1px solid var(--surface-border)',
                        borderRadius: '5px',
                        backgroundColor: 'var(--surface-a)',
                        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                    }}
                >
                    <span>{tab.header}</span>
                    <i className={`pi ${isVisible ? 'pi-chevron-up' : 'pi-chevron-down'}`} style={{ marginLeft: 'auto' }}></i>
                </div>
                {(isVisible || hardShow) && (
                    <div className="p-accordion-content">
                        {tab.content}
                    </div>
                )}
            </div>
        </div>
    );
};

BorAccordion.propTypes = {
    tab: PropTypes.shape({
        header: PropTypes.string.isRequired,
        content: PropTypes.node.isRequired,
    }).isRequired,
    show: PropTypes.bool, // Whether to show or hide the content
};

BorAccordion.defaultProps = {
    show: false, // Default to hidden
};

export default BorAccordion;
