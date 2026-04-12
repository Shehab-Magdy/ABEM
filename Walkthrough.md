Running the Backend
I have successfully started the backend for you.

When attempting to build the Docker image, the Docker VM ran out of disk space (a common issue on Mac). To work around this without requiring complex Docker disk management, I started the database and Redis services via Docker, and then ran the Django backend locally on your machine.

Here are the steps to run it yourself in the future:

1. Start the Database and Redis
First, ensure that PostgreSQL and Redis are running in the background. Navigate to the project root and run:

bash
docker compose up -d db redis
2. Start the Backend Server
Then, use your local Python environment to start the backend. Navigate to the backend directory, activate the virtual environment, and run the server:

bash
cd backend
source .venv/bin/activate

# Optional: pip install -r requirements/development.txt

# Optional: python manage.py migrate

python manage.py runserver
Server Endpoints
The Django API is running at: <http://127.0.0.1:8000/api/v1/>
Interactive Swagger UI: <http://127.0.0.1:8000/api/docs/>
You can stop the backend server by pressing Ctrl+C in your terminal. You can stop the database and Redis services by running docker compose down inside the project root directory.

Running the Frontend
I have successfully started the frontend for you as well. It connects directly to your local backend.

Here are the steps to run it yourself in the future:

Start the Frontend Server
Navigate to the frontend directory, install dependencies, and start the development server:

bash
cd frontend
npm install
npm run dev
Server Endpoint
The React application is running at: <http://localhost:5173/>
You can stop the frontend server by pressing Ctrl+C in your terminal.
