import React from 'react';
import { render, screen } from '@testing-library/react';
import ReportFooterComponent from '../../Components/reportFooterComponent';

describe('ReportFooterComponent', () => {
  
  it('should render successfully', () => {
      render(<ReportFooterComponent />);
      // Here If render throws an error, the test will naturally fail
  });

  it('should render one logo image', () => {
    render(<ReportFooterComponent />);
    const logoImage = screen.getByAltText(/Logo/i);
    expect(logoImage).toBeInTheDocument(); // Assert that the image is present
  });  
  
});
