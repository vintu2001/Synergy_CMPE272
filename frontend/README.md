# Agentic Apartment Manager - Frontend

React + Vite frontend application for the Agentic Apartment Manager system.

## Tech Stack

- **Framework**: React 19 with Vite 7
- **Styling**: Tailwind CSS v4
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form
- **Icons**: Lucide React

## Features

### 1. Resident Submission Page (`/`)
- **Smart AI-Powered Form**: Real-time message analysis with debounced classification
- **AI Suggestions Panel**: Shows detected category, urgency, intent, and confidence score
- **Override Controls**: Manual category, urgency, and intent selection
- **Input Validation**: Minimum 10 characters required
- **Character Counter**: Real-time feedback on message length
- **Responsive Design**: Works on mobile, tablet, and desktop

### 2. Resident Dashboard (`/dashboard`)
- **Request History**: View all requests for the current resident
- **Status Tracking**: Color-coded status badges (Submitted, Processing, Resolved, etc.)
- **Filtering**: Filter by request status
- **Refresh**: Manual refresh to get latest data
- **Resident ID Switcher**: Change resident ID to view different user's requests
- **Responsive Table**: Adaptive layout for different screen sizes

### 3. Admin Dashboard (`/admin`)
- **API Key Authentication**: Secure access with admin API key stored in localStorage
- **Search Functionality**: Search by request ID, resident ID, or message text
- **Advanced Filtering**: Filter by category, urgency, and status
- **Sortable Columns**: Sort by created_at, updated_at, category, urgency, status
- **Comprehensive View**: See all requests across all residents
- **Export-Ready**: Table format ready for CSV export (future enhancement)

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── LoadingSpinner.jsx
│   │   └── StatusBadge.jsx
│   ├── pages/               # Page components
│   │   ├── ResidentSubmission.jsx
│   │   ├── ResidentDashboard.jsx
│   │   └── AdminDashboard.jsx
│   ├── services/            # API integration
│   │   └── api.js
│   ├── context/             # React Context
│   │   └── UserContext.jsx
│   ├── App.jsx              # Root component with routing
│   ├── main.jsx             # Entry point
│   └── index.css            # Tailwind directives
├── public/
├── .env                     # Environment variables (not committed)
├── package.json
├── vite.config.js
├── postcss.config.js
└── README.md
```

## Setup Instructions

### Prerequisites
- Node.js 18+ and npm 9+
- Backend server running on `http://localhost:8000`

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create environment file**
   ```bash
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173`

## Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## API Integration

The frontend communicates with the backend via the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/classify` | POST | Classify resident message in real-time |
| `/api/v1/get-requests/{resident_id}` | GET | Get all requests for a specific resident |
| `/api/v1/admin/all-requests` | GET | Get all requests (requires X-API-Key header) |

### Example API Calls

**Classify Message:**
```javascript
import { classifyMessage } from './services/api';

const result = await classifyMessage('RES_1001', 'My AC is broken');
// Returns: { category, urgency, intent, confidence }
```

**Get Resident Requests:**
```javascript
import { getResidentRequests } from './services/api';

const requests = await getResidentRequests('RES_1001');
// Returns: Array of ResidentRequest objects
```

**Get All Requests (Admin):**
```javascript
import { getAllRequests } from './services/api';

const data = await getAllRequests('your-admin-api-key');
// Returns: { requests: [...], total_count: number }
```

## User Context

The app uses React Context to manage the current `resident_id`:

```javascript
import { useUser } from './context/UserContext';

function MyComponent() {
  const { residentId, setResidentId } = useUser();
  
  return (
    <input 
      value={residentId} 
      onChange={(e) => setResidentId(e.target.value)} 
    />
  );
}
```

The `resident_id` is persisted in `localStorage` and defaults to `RES_1001`.

## Usage Guide

### For Residents

1. **Submit a Request**:
   - Navigate to the home page (`/`)
   - Type your issue in the message box
   - Wait 500ms for AI analysis (automatic)
   - Review AI suggestions in the right panel
   - Override category/urgency if needed
   - Click "Submit" (currently shows alert - backend integration pending)

2. **View Your Requests**:
   - Navigate to Dashboard (`/dashboard`)
   - See all your requests in a table
   - Filter by status (All, Submitted, Processing, etc.)
   - Click "Refresh" to reload data

### For Admins

1. **Access Admin Dashboard**:
   - Navigate to Admin (`/admin`)
   - Enter your admin API key (from backend `.env`)
   - Click "Save" to persist the key

2. **View and Filter Requests**:
   - Search by ID, resident, or message text
   - Filter by category, urgency, status
   - Sort by any column (asc/desc)
   - Click "Refresh" to reload data

