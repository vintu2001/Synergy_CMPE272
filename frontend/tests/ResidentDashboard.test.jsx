import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ResidentDashboard from '../src/pages/ResidentDashboard';
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

describe('ResidentDashboard', () => {
  const mockRequests = [
    {
      request_id: 'REQ001',
      message_text: 'AC not working',
      category: 'Maintenance',
      urgency: 'High',
      status: 'pending',
      created_at: '2025-11-16T10:00:00Z',
      admin_comments: [
        {
          comment: 'We will send a technician tomorrow',
          added_by: 'admin',
          added_at: '2025-11-16T11:00:00Z'
        }
      ]
    },
    {
      request_id: 'REQ002',
      message_text: 'Billing question',
      category: 'Billing',
      urgency: 'Low',
      status: 'completed',
      created_at: '2025-11-15T14:30:00Z',
      admin_comments: []
    },
    {
      request_id: 'REQ003',
      message_text: 'Package delivery',
      category: 'Deliveries',
      urgency: 'Medium',
      status: 'in_progress',
      created_at: '2025-11-14T09:15:00Z',
      admin_comments: null
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('user', JSON.stringify({ 
      residentId: 'RES123', 
      role: 'resident' 
    }));
  });

  it('renders dashboard title', () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue([]);
    
    renderWithContext(<ResidentDashboard />);
    
    expect(screen.getByText(/My Requests/i)).toBeInTheDocument();
  });

  it('displays loading state', () => {
    vi.mocked(api.getResidentRequests).mockImplementation(
      () => new Promise(() => {})
    );
    
    renderWithContext(<ResidentDashboard />);
    
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  it('fetches and displays resident requests', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(api.getResidentRequests).toHaveBeenCalledWith('RES123');
    });
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
      expect(screen.getByText(/Billing question/i)).toBeInTheDocument();
      expect(screen.getByText(/Package delivery/i)).toBeInTheDocument();
    });
  });

  it('displays request status badges', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('pending')).toBeInTheDocument();
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('in_progress')).toBeInTheDocument();
    });
  });

  it('displays urgency levels', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('High')).toBeInTheDocument();
      expect(screen.getByText('Low')).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
    });
  });

  it('shows empty state when no requests', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue([]);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/No requests found/i)).toBeInTheDocument();
    });
  });

  it('handles API error', async () => {
    vi.mocked(api.getResidentRequests).mockRejectedValue(
      new Error('Failed to fetch')
    );
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Error loading requests/i)).toBeInTheDocument();
    });
  });

  it('displays categories correctly', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Maintenance')).toBeInTheDocument();
      expect(screen.getByText('Billing')).toBeInTheDocument();
      expect(screen.getByText('Deliveries')).toBeInTheDocument();
    });
  });

  it('formats dates correctly', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      const dateElements = screen.getAllByText(/Nov|2025/i);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  it('refreshes data on mount', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    const { unmount } = renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(api.getResidentRequests).toHaveBeenCalledTimes(1);
    });
    
    unmount();
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(api.getResidentRequests).toHaveBeenCalledTimes(2);
    });
  });

  it('displays admin comments when available', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(screen.getByText(/We will send a technician tomorrow/i)).toBeInTheDocument();
      expect(screen.getByText(/Admin Comments/i)).toBeInTheDocument();
    });
  });

  it('shows comment count badge when comments exist', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/AC not working/i)).toBeInTheDocument();
    });
    
    await waitFor(() => {
      // Should show comment count badge with title attribute
      const commentBadge = screen.getByTitle(/1 admin comment/i);
      expect(commentBadge).toBeInTheDocument();
    });
  });

  it('does not show comment badge when no comments exist', async () => {
    vi.mocked(api.getResidentRequests).mockResolvedValue(mockRequests);
    
    renderWithContext(<ResidentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Billing question/i)).toBeInTheDocument();
    });
    
    // REQ002 has empty admin_comments array, so no badge should appear
    const commentBadges = screen.queryAllByTitle(/admin comment/i);
    const billingBadge = commentBadges.find(badge => 
      badge.closest('tr')?.textContent?.includes('Billing question')
    );
    expect(billingBadge).toBeUndefined();
  });
});
