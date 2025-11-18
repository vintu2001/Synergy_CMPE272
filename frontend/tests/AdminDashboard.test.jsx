import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AdminDashboard from '../src/pages/AdminDashboard';
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

describe('AdminDashboard', () => {
  const mockRequests = [
    {
      request_id: 'REQ001',
      resident_id: 'RES123',
      message_text: 'AC not working',
      category: 'Maintenance',
      urgency: 'High',
      status: 'pending',
      created_at: '2025-11-16T10:00:00Z',
      risk_score: 0.85,
      risk_level: 'high'
    },
    {
      request_id: 'REQ002',
      resident_id: 'RES456',
      message_text: 'Billing question',
      category: 'Billing',
      urgency: 'Low',
      status: 'completed',
      created_at: '2025-11-15T14:30:00Z',
      risk_score: 0.2,
      risk_level: 'low'
    },
    {
      request_id: 'REQ003',
      resident_id: 'RES789',
      message_text: 'Package delivery',
      category: 'Deliveries',
      urgency: 'Medium',
      status: 'in_progress',
      created_at: '2025-11-14T09:15:00Z',
      risk_score: 0.45,
      risk_level: 'medium'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('user', JSON.stringify({ 
      userId: 'ADMIN001', 
      role: 'admin' 
    }));
  });

  it('renders admin dashboard title', () => {
    vi.mocked(api.getAllRequests).mockResolvedValue([]);
    
    renderWithContext(<AdminDashboard />);
    
    expect(screen.getByText(/All Requests/i)).toBeInTheDocument();
  });

  it('fetches and displays all requests', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(api.getAllRequests).toHaveBeenCalled();
    });
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
      expect(screen.getByText(/Billing question/i)).toBeInTheDocument();
      expect(screen.getByText(/Package delivery/i)).toBeInTheDocument();
    });
  });

  it('filters requests by status', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    const statusFilter = screen.getByLabelText(/Status/i);
    fireEvent.change(statusFilter, { target: { value: 'pending' } });
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
      expect(screen.queryByText(/Billing question/i)).not.toBeInTheDocument();
    });
  });

  it('filters requests by urgency', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    const urgencyFilter = screen.getByLabelText(/Urgency/i);
    fireEvent.change(urgencyFilter, { target: { value: 'High' } });
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
      expect(screen.queryByText(/Billing question/i)).not.toBeInTheDocument();
    });
  });

  it('filters requests by category', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    const categoryFilter = screen.getByLabelText(/Category/i);
    fireEvent.change(categoryFilter, { target: { value: 'Maintenance' } });
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
      expect(screen.queryByText(/Billing question/i)).not.toBeInTheDocument();
    });
  });

  it('sorts requests by risk score', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    const sortButton = screen.getByText(/Sort by Risk/i);
    fireEvent.click(sortButton);
    
    await waitFor(() => {
      const requestTexts = screen.getAllByTestId(/request-item/i);
      expect(requestTexts[0]).toHaveTextContent(/AC not working/i);
    });
  });

  it('displays risk levels with badges', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('high')).toBeInTheDocument();
      expect(screen.getByText('low')).toBeInTheDocument();
      expect(screen.getByText('medium')).toBeInTheDocument();
    });
  });

  it('displays request counts by status', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Pending: 1/i)).toBeInTheDocument();
      expect(screen.getByText(/In Progress: 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Completed: 1/i)).toBeInTheDocument();
    });
  });

  it('handles request status update via dropdown', async () => {
    const mockRequestWithDetails = {
      ...mockRequests[0],
      request_id: 'REQ001',
      status: 'Submitted',
      simulated_options: []
    };
    
    vi.mocked(api.getAllRequests).mockResolvedValue([mockRequestWithDetails]);
    vi.mocked(api.updateRequestStatus).mockResolvedValue({ 
      status: 'success',
      message: 'Request status updated to In Progress',
      request_id: 'REQ001'
    });
    
    // Set API key in localStorage
    localStorage.setItem('admin_api_key', 'test-api-key');
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    // Find and click the expand button (ChevronRight icon)
    const expandButtons = screen.getAllByRole('button');
    const expandButton = expandButtons.find(btn => {
      const svg = btn.querySelector('svg');
      return svg && (svg.getAttribute('data-lucide') === 'chevron-right' || svg.classList.contains('lucide-chevron-right'));
    });
    
    if (expandButton) {
      fireEvent.click(expandButton);
    }
    
    // Wait for expanded content and find status dropdown
    await waitFor(() => {
      const statusSelect = screen.getByDisplayValue(/Submitted/i);
      expect(statusSelect).toBeInTheDocument();
      
      // Change status
      fireEvent.change(statusSelect, { target: { value: 'In Progress' } });
    });
    
    // Wait for Update button to appear and click it
    await waitFor(() => {
      const updateButton = screen.getByText(/Update/i);
      expect(updateButton).toBeInTheDocument();
      fireEvent.click(updateButton);
    });
    
    await waitFor(() => {
      expect(api.updateRequestStatus).toHaveBeenCalledWith('REQ001', 'In Progress', 'test-api-key');
    });
  });

  it('handles adding comments to requests', async () => {
    const mockRequestWithDetails = {
      ...mockRequests[0],
      request_id: 'REQ001',
      admin_comments: []
    };
    
    vi.mocked(api.getAllRequests).mockResolvedValue([mockRequestWithDetails]);
    vi.mocked(api.addComment).mockResolvedValue({ 
      status: 'success',
      message: 'Comment added successfully',
      request_id: 'REQ001',
      comment: {
        comment: 'Test comment',
        added_by: 'admin',
        added_at: new Date().toISOString()
      }
    });
    
    // Set API key in localStorage
    localStorage.setItem('admin_api_key', 'test-api-key');
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    // Find and click the expand button
    const expandButtons = screen.getAllByRole('button');
    const expandButton = expandButtons.find(btn => {
      const svg = btn.querySelector('svg');
      return svg && (svg.getAttribute('data-lucide') === 'chevron-right' || svg.classList.contains('lucide-chevron-right'));
    });
    
    if (expandButton) {
      fireEvent.click(expandButton);
    }
    
    // Wait for comment textarea and add comment
    await waitFor(() => {
      const commentTextarea = screen.getByPlaceholderText(/Add a comment for the resident/i);
      expect(commentTextarea).toBeInTheDocument();
      
      fireEvent.change(commentTextarea, { target: { value: 'Test comment' } });
    });
    
    // Wait for Add Comment button and click it
    await waitFor(() => {
      const addButton = screen.getByText(/Add Comment/i);
      expect(addButton).toBeInTheDocument();
      fireEvent.click(addButton);
    });
    
    await waitFor(() => {
      expect(api.addComment).toHaveBeenCalledWith('REQ001', 'Test comment', 'test-api-key');
    });
  });

  it('displays admin comments in expanded view', async () => {
    const mockRequestWithComments = {
      ...mockRequests[0],
      request_id: 'REQ001',
      admin_comments: [
        {
          comment: 'We will send a technician tomorrow',
          added_by: 'admin',
          added_at: '2025-11-16T11:00:00Z'
        }
      ]
    };
    
    vi.mocked(api.getAllRequests).mockResolvedValue([mockRequestWithComments]);
    localStorage.setItem('admin_api_key', 'test-api-key');
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    // Expand the row
    const expandButtons = screen.getAllByRole('button');
    const expandButton = expandButtons.find(btn => {
      const svg = btn.querySelector('svg');
      return svg && (svg.getAttribute('data-lucide') === 'chevron-right' || svg.classList.contains('lucide-chevron-right'));
    });
    
    if (expandButton) {
      fireEvent.click(expandButton);
    }
    
    await waitFor(() => {
      expect(screen.getByText(/Admin Comments/i)).toBeInTheDocument();
      expect(screen.getByText(/We will send a technician tomorrow/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no requests', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue([]);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/No requests found/i)).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    vi.mocked(api.getAllRequests).mockRejectedValue(
      new Error('Failed to fetch')
    );
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Error loading requests/i)).toBeInTheDocument();
    });
  });

  it('refreshes data periodically', async () => {
    vi.useFakeTimers();
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(api.getAllRequests).toHaveBeenCalledTimes(1);
    });
    
    vi.advanceTimersByTime(30000);
    
    await waitFor(() => {
      expect(api.getAllRequests).toHaveBeenCalledTimes(2);
    });
    
    vi.useRealTimers();
  });

  it('exports requests to CSV', async () => {
    vi.mocked(api.getAllRequests).mockResolvedValue(mockRequests);
    const createElementSpy = vi.spyOn(document, 'createElement');
    
    renderWithContext(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    const exportButton = screen.getByText(/Export/i);
    fireEvent.click(exportButton);
    
    expect(createElementSpy).toHaveBeenCalledWith('a');
  });
});
