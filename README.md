🎤 Voice Banking System

An intelligent, voice‑activated banking web app that lets users check balances, transfer funds, and review transactions using natural language commands — just like talking to a real bank assistant.

Built with FastAPI, React, JWT authentication, SQLAlchemy, and browser speech recognition, this project demonstrates a complete, secure, and modern full‑stack application.
✨ Features

Secure authentication

    JWT‑based login, registration, and logout

    Password hashing with bcrypt and strong validation rules

    Forgot password & reset password flows

    Smart voice banking

Check balance with commands like

        “What is my balance?”

        “Show my account balance”

 Transfer funds with natural phrases:

        “Transfer 100 to ACC1234567890”

        “Send 50 to user alice”

Request transaction history:

         “Show my transactions”

         “Show last 5 transactions”

  Automatic listening → stop → process cycle (no extra button needed)

    Traditional banking UI

        Beautiful dashboard with:

            Current balance and account number

            Recent transactions with type, amount, date, and recipient

        Fund transfer form with:

            Account validation

            Search by username/account

            Recent recipients list

    Test‑friendly tools

        “Create Test Users” panel to quickly generate multiple demo accounts

        Copy‑to‑clipboard for account numbers & usernames

        Each new user starts with an initial balance for easy demo transfers

    Clean architecture

        Backend: layered services (AuthService, BankingService, VoiceService)

        Frontend: modular React components (Dashboard, VoiceCommand, FundTransfer, CreateUser, etc.)

        API‑first design with auto‑generated docs

🏗 Tech Stack

Backend

    FastAPI (Python)

    SQLAlchemy ORM

    PostgreSQL / SQLite (configurable)

    JWT (python‑jose)

    Passlib + bcrypt for password hashing

Frontend

    React (CRA / Vite, depending on your setup)

    Axios for API calls

    Browser Speech Recognition (react-speech-recognition / Web Speech API)

    Modern, responsive CSS


1. Clone the repository

git clone https://github.com/your-username/voice-banking-system.git
cd voice-banking-system

2. Backend setup

cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

pip install -r requirements.txt

3. Configure environment variables (create .env in backend/app):

SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./voice_banking.db  # or your Postgres URL


4. Run database migrations / create tables (depending on your setup), then start the API:

bash
uvicorn app.main:app --reload

The API will be available at:

    Swagger UI: http://localhost:8000/docs

    OpenAPI JSON: http://localhost:8000/openapi.json

5. Frontend setup

bash
cd frontend
npm install
npm start

The frontend will run at:

    http://localhost:3000

Make sure your frontend API base URL points to http://localhost:8000.

Enjoy Voice Banking!!!

