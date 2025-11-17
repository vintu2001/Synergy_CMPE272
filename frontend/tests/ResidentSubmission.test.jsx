import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ResidentSubmission from '../src/pages/ResidentSubmission';
import { UserProvider } from '../src/context/UserContext';
import * as api from '../src/services/api';

vi.mock('../src/services/api');

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const renderWithContext = (component) => {
  return render(
    <UserProvider>{component}</UserProvider>
  );
};

describe('ResidentSubmission', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('user', JSON.stringify({ 
      residentId: 'RES123', 
      role: 'resident' 
    }));
  });

  it('renders submission form', () => {
    renderWithContext(<ResidentSubmission />);
    
    expect(screen.getByText(/Submit a Request/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Describe your issue/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Submit Request/i })).toBeInTheDocument();
  });

  it('submits request successfully', async () => {
    const mockResponse = {
      status: 'submitted',
      request_id: 'REQ123',
      classification: {
        category: 'Maintenance',
        urgency: 'High'
      }
    };
    
    vi.mocked(api.submitRequest).mockResolvedValue(mockResponse);
    
    renderWithContext(<ResidentSubmission />);
    
    const textarea = screen.getByPlaceholderText(/Describe your issue/i);
    fireEvent.change(textarea, { 
      target: { value: 'My AC is not working' } 
    });
    
    const submitButton = screen.getByRole('button', { name: /Submit Request/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(api.submitRequest).toHaveBeenCalledWith({
        resident_id: 'RES123',
        message_text: 'My AC is not working'
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText(/Request Submitted Successfully/i)).toBeInTheDocument();
    });
  });

  it('shows validation error for empty message', async () => {
    renderWithContext(<ResidentSubmission />);
    
    const submitButton = screen.getByRole('button', { name: /Submit Request/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Please describe your issue/i)).toBeInTheDocument();
    });
    
    expect(api.submitRequest).not.toHaveBeenCalled();
  });

  it('handles API error gracefully', async () => {
    vi.mocked(api.submitRequest).mockRejectedValue(
      new Error('Service unavailable')
    );
    
    renderWithContext(<ResidentSubmission />);
    
    const textarea = screen.getByPlaceholderText(/Describe your issue/i);
    fireEvent.change(textarea, { 
      target: { value: 'Water leak' } 
    });
    
    const submitButton = screen.getByRole('button', { name: /Submit Request/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to submit request/i)).toBeInTheDocument();
    });
  });

  it('displays classification results', async () => {
    const mockResponse = {
      status: 'submitted',
      request_id: 'REQ123',
      classification: {
        category: 'Maintenance',
        urgency: 'High',
        confidence: 0.95
      },
      simulated_options: [
        { option_id: 'OPT1', action: 'Dispatch technician' }
      ]
    };
    
    vi.mocked(api.submitRequest).mockResolvedValue(mockResponse);
    
    renderWithContext(<ResidentSubmission />);
    
    const textarea = screen.getByPlaceholderText(/Describe your issue/i);
    fireEvent.change(textarea, { target: { value: 'AC broken' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Submit Request/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/Category.*Maintenance/i)).toBeInTheDocument();
      expect(screen.getByText(/Urgency.*High/i)).toBeInTheDocument();
    });
  });

  it('disables submit button while loading', async () => {
    vi.mocked(api.submitRequest).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );
    
    renderWithContext(<ResidentSubmission />);
    
    const textarea = screen.getByPlaceholderText(/Describe your issue/i);
    fireEvent.change(textarea, { target: { value: 'Test' } });
    
    const submitButton = screen.getByRole('button', { name: /Submit Request/i });
    fireEvent.click(submitButton);
    
    expect(submitButton).toBeDisabled();
    expect(screen.getByText(/Submitting/i)).toBeInTheDocument();
  });

  it('clears form after successful submission', async () => {
    const mockResponse = {
      status: 'submitted',
      request_id: 'REQ123',
      classification: { category: 'Maintenance', urgency: 'High' }
    };
    
    vi.mocked(api.submitRequest).mockResolvedValue(mockResponse);
    
    renderWithContext(<ResidentSubmission />);
    
    const textarea = screen.getByPlaceholderText(/Describe your issue/i);
    fireEvent.change(textarea, { target: { value: 'Test issue' } });
    
    expect(textarea.value).toBe('Test issue');
    
    fireEvent.click(screen.getByRole('button', { name: /Submit Request/i }));
    
    await waitFor(() => {
      expect(textarea.value).toBe('');
    });
  });
});
