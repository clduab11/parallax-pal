# Parallax Pal Frontend

The web interface for Parallax Pal, providing a modern, responsive interface for research and analytics integration.

## Features

- Real-time research progress tracking
- Interactive research task management
- Responsive design for all devices
- Secure authentication
- Analytics dashboard
- Research result visualization

## Prerequisites

- Node.js (v14 or later)
- npm (v6 or later)
- A running instance of the Parallax Pal backend API

## Setup

1. Navigate to the frontend directory:
```bash
cd src/frontend
```

2. Make the initialization script executable:
```bash
chmod +x init.sh
```

3. Run the initialization script:
```bash
./init.sh
```

This script will:
- Install all required dependencies
- Set up TypeScript configuration
- Configure Tailwind CSS
- Create necessary directory structure
- Initialize environment variables
- Build the project

## Development

To start the development server:

```bash
npm start
```

The application will be available at `http://localhost:3000`

## Building for Production

To create an optimized production build:

```bash
npm run build
```

The built files will be in the `build` directory.

## Environment Configuration

Create a `.env` file in the root directory with the following variables:

```
REACT_APP_API_URL=http://localhost:8000  # URL of your backend API
```

For production, update the API URL to your production backend endpoint.

## Project Structure

```
src/
├── components/      # Reusable UI components
├── contexts/        # React context providers
├── pages/          # Page components
├── services/       # API and utility services
├── styles/         # Global styles and Tailwind CSS
└── utils/          # Helper functions and constants
```

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Create production build
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.