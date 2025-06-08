# Lab Equipment Reservation System

A full-stack web application for managing laboratory equipment reservations. This system allows students to reserve equipment and administrators to manage reservations, equipment, and laboratories.

## Features

### Student Features
- View available laboratory equipment
- Make equipment reservations with quantity selection
- View reservation history and status
- Receive notifications for reservation updates
- Filter equipment by laboratory
- Search functionality for equipment

### Admin Features
- Manage laboratory equipment and quantities
- Approve/reject reservation requests
- Track equipment returns
- View reservation history
- Manage laboratories
- Search and filter reservations
- View admin action history

## Tech Stack

### Frontend
- React 19
- TypeScript
- Material-UI (MUI)
- React Router
- Axios
- React Toastify
- MUI Date Pickers

### Backend
- Python Flask
- SQLAlchemy
- PostgreSQL
- JWT Authentication
- Flask-CORS

## Prerequisites

- Node.js (v16 or higher)
- Python 3.8 or higher
- PostgreSQL
- npm or yarn

## Installation

### Frontend Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lab-reservation-system.git
cd lab-reservation-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the frontend directory:
```env
REACT_APP_API_URL=http://localhost:5000/api
```

4. Start the development server:
```bash
npm start
```



5. Run the Flask application:
```bash
python app.py
```

The backend server will start at http://localhost:5000

## Database Schema

### Users
- UserID (Primary Key)
- Username
- Password (hashed)
- Role (student/admin)
- Email
- Department

### Laboratories
- LabID (Primary Key)
- LabName
- Location
- Capacity
- Description

### Equipment
- EquipmentID (Primary Key)
- Name
- Description
- TotalUnits
- AvailableUnits
- LaboratoryID (Foreign Key)
- Status

### Reservations
- ReservationID (Primary Key)
- UserID (Foreign Key)
- EquipmentID (Foreign Key)
- StartTime
- EndTime
- Status
- Quantity
- Reason
- AdminNotes
- ReturnTimestamp

## API Endpoints

### Authentication
- POST /api/auth/login
- POST /api/auth/register

### Equipment
- GET /api/equipment
- GET /api/equipment/<id>
- POST /api/equipment (admin only)
- PUT /api/equipment/<id> (admin only)
- DELETE /api/equipment/<id> (admin only)

### Reservations
- GET /api/reservations
- GET /api/reservations/<id>
- POST /api/reservations
- PUT /api/reservations/<id>
- GET /api/users/<user_id>/reservations

### Laboratories
- GET /api/laboratories
- POST /api/laboratories (admin only)
- PUT /api/laboratories/<id> (admin only)
- DELETE /api/laboratories/<id> (admin only)

## Customization

### Adding New Features
1. Frontend:
   - Create new components in `src/components`
   - Add new routes in `src/App.tsx`
   - Update API calls in `src/api/api.ts`

2. Backend:
   - Add new models in `models.py`
   - Create new routes in `app.py`
   - Update database migrations

### Styling
- Theme customization in `src/theme.ts`
- Component styling in respective component files
- Global styles in `src/index.css`

## Contributing

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Commit your changes: `git commit -m 'Add some feature'`
5. Push to the branch: `git push origin feature/your-feature-name`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- Material-UI for the component library
- Flask for the backend framework
- React for the frontend framework
