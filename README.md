# CS50 Python Platform

A modern web application built with FastAPI and React, designed to provide an interactive platform for CS50 course content.

## Project Overview

This project consists of a full-stack web application with a Python-based backend API and a React-based frontend. It's designed to create an interactive and user-friendly platform for CS50 course content delivery and execution.

## Project Structure

```
.
├── backend/
│   ├── backend.py
│   ├── executor_simple.py
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.css
        ├── App.jsx
        ├── index.css
        └── main.jsx
```

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs with Python
- **Uvicorn**: Lightning-fast ASGI server implementation
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **Python-Jose**: JavaScript Object Signing and Encryption implementation
- **Passlib**: Password hashing library
- **BCrypt**: Password hashing function

### Frontend
- **React 19**: JavaScript library for building user interfaces
- **Vite**: Next-generation frontend tooling
- **React Router DOM**: Declarative routing for React applications
- **Axios**: Promise-based HTTP client
- **Lucide React**: Beautiful and consistent icons
- **ESLint**: Code linting and formatting

## Setup and Installation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Available Scripts

### Frontend

- `npm run dev`: Starts the development server
- `npm run build`: Builds the app for production
- `npm run lint`: Lints the codebase
- `npm run preview`: Preview the production build locally

## Features

- Modern and responsive user interface
- Fast and efficient API backend
- Secure authentication system
- Interactive code execution environment
- Real-time feedback and validation
- Modular and maintainable codebase

## Development

### Code Style and Quality

- Backend follows PEP 8 style guide
- Frontend uses ESLint for code quality
- Type hints and validation using Pydantic
- Modern React practices with hooks and functional components

### Security Features

- BCrypt password hashing
- JWT-based authentication
- Secure session management
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- CS50 team for inspiration and guidance
- FastAPI and React communities for excellent documentation and support
