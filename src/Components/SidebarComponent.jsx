import React, { useEffect, useState } from 'react';
import FnbLogo from '../Images/FNBlogo-long.png';
import MetricsCard from './MetricsCard';

const SidebarLayout = ({ items, mainContent, pageToShow }) => {
  const [isNarrow, setIsNarrow] = useState(() => typeof window !== 'undefined' && window.innerWidth < 800);
  const [collapsed, setCollapsed] = useState(() => typeof window !== 'undefined' && window.innerWidth < 800);
  useEffect(() => {
    const resize = () => {
      const narrow = window.innerWidth < 800;
      setIsNarrow(narrow);
      if (narrow) setCollapsed(true);
    };
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);
  const [activeItem, setActiveItem] = useState(pageToShow);

  const toggleSidebar = () => setCollapsed(prev => !prev);

  // Normalize items
  const normalizedItems = items.map(item => {
    
    if (typeof item.template === 'function' && item.template) {
      return { ...item, render: true };
    }
    return { ...item, render: null };
  });

  const topBarItems = normalizedItems.slice(-4);
  const sideBarItems = normalizedItems.slice(0, normalizedItems.length-4);

  // Group sidebar items by section
  const groupedItems = sideBarItems.reduce((acc, item) => {
    const section = item.section || 'Uncategorized';
    if (!acc[section]) acc[section] = [];
    acc[section].push(item);
    return acc;
  }, {});

  return (
    <>
      {/* Sidebar */}
      <div
        className="w3-sidebar w3-bar-block w3-light-grey report-sidebar"
        style={{
          width: collapsed ? '60px' : '250px',
          transition: 'width 0.3s ease',
          height: '100vh',
          overflowX: 'hidden',
          position: 'fixed',
          top: 0,
          left: 0,
          paddingTop: '1rem',
          zIndex: 1002,
        }}
      >
        
        <button
          className="w3-button w3-light-grey w3-hover-grey"
          aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          aria-expanded={!collapsed}
          onClick={toggleSidebar}
          style={{ marginBottom: '1rem', width: '100%' }}
        >
          <i aria-hidden="true" className={`pi ${collapsed ? 'pi-chevron-right' : 'pi-chevron-left'}`}></i>
        </button>

        {!collapsed && (
          <div style={{ overflowY: 'auto', maxHeight: '70vh', paddingBottom: '500px' }}>
            {Object.entries(groupedItems).map(([section, items]) => (
              <div key={section} className="w3-container w3-padding-small">
                <h6 className="w3-text-grey w3-border-bottom">{section}</h6>
                {items.map((item, idx) => {
                  if (item.items){
                    return (
                      <select
                        className={`w3-bar-item w3-button w3-hover-light-grey ${activeItem === item.label ? 'w3-light-grey' : ''}`}
                        onChange={(e) => {
                          const selectedItem = item.items.find(subItem => subItem.label === e.target.value);
                          if (selectedItem && selectedItem.command) {
                            selectedItem.command();
                          }
                        }}
                      >
                        <option value="" disabled selected hidden>Profile</option>
                        {item.items.map((subItem) => (
                          <option key={subItem.label} value={subItem.label}>
                            {subItem.label}
                          </option>
                        ))}
                      </select>
                    )
                  }
                  
                  
                  return (
                    <button
                      key={idx}
                      className={`w3-bar-item w3-button w3-hover-light-grey ${item.label} ${activeItem === item.label ? 'w3-white' : ''}`}
                      onClick={() => {
                        setActiveItem(item.label);
                        if (item.command) item.command();
                        if (isNarrow) setCollapsed(true);
                      }}
                      style={{ textAlign: 'left', padding: '12px 16px', fontSize: '14px' }}
                    >
                      {item.icon && <i aria-hidden="true" aria-hidden="true"
 className={`pi ${item.icon}`} style={{ marginRight: '8px' }}></i>}
                      {item.render ? item.template() : item.label}
                    </button>
                  )}
                )}
              </div>
            ))}
          </div>
        )}

        {!collapsed && !isNarrow && !window.location.href.includes('prd01') && <MetricsCard />}
      </div>

      {/* Top Bar */}
      <div
  className="w3-bar w3-light-grey report-topbar"
  style={{
    marginLeft: isNarrow ? '60px' : (collapsed ? '60px' : '250px'),
    transition: 'margin-left 0.3s ease',
    padding: '1rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '78px',
  }}
>
  <div style={{ display: 'flex', alignItems: 'center', position: 'relative', width: '100%', justifyContent: 'space-between' }}>
    <img
      src={FnbLogo}
      alt="eSTORE® COMMON APP REPORTING DASHBOARD"
      style={{
        height: collapsed ? '76px' : '40px',
        padding: collapsed ? '2px' : '0px',
        width: collapsed ? '800px' : '400px',
        transition: 'width 0.3s ease, height 0.6s ease',
      }}
    />
    
      <h1
        style={{
          fontSize: '1.5rem',
          textAlign: 'center',
          fontWeight: 'bold',
          opacity: collapsed ? '0': '1',
          fontSize: collapsed ? '0px': 'inherit',
          width:  collapsed ? '0px': 'auto',
          transition: 'fontSize 0.6s ease, opacity 0.6s ease, width 0.5s ease',
        }}
        className='w3-animate-top'
      >
        eSTORE® COMMON APP REPORTING DASHBOARD
      </h1>
    <div style={{   display:'flex', width:'30%'    }}>
      {topBarItems.map((item, idx) => (
        <button
          key={idx}
          className="w3-button w3-hover-light-grey"
          onClick={() => {
            if (item.command) item.command();
          }}
          style={{
            marginLeft: '1rem',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          {item.icon && (
            <i
              aria-hidden="true"

              className={`pi ${item.icon}`}
              style={{ marginRight: '6px' }}
            ></i>
          )}
          {item.render ? item.template() : item.label}
        </button>
      ))}
    </div> 
     <div style={{   display:'flex', width:  collapsed ? '0px': '5%', transition: 'width 0.5s ease'   }}></div>
  </div>
</div>

      {/* Main Content */}
      <div
        style={{
          marginLeft: isNarrow ? '60px' : (collapsed ? '60px' : '250px'),
          marginTop: '78px',
          transition: 'margin-left 0.3s ease',
          padding: isNarrow ? '12px' : '2rem',
        }}
      >
        {mainContent}
      </div>
    </>
  );
};

export default SidebarLayout;