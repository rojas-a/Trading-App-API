# Trading App API

## Overview
This Flask-based trading application allows users to register, log in, and manage a virtual stock portfolio. Users can add stocks using ticker symbols, fetch real-time prices with the Alpha Vantage API, buy and sell shares, and calculate the total value of their holdings. Flask-Login is used for session management, and SQLAlchemy handles database interactions.

---

## Running the App

```bash
cd trading
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The server runs at `http://localhost:5000`.

---

## Demo Walkthrough

The full flow below can be run in a terminal with `curl`. Cookies are saved to `cookies.txt` so the session persists across requests.

**1. Health check**
```bash
curl http://localhost:5000/api/health
```

**2. Create a user**
```bash
curl -X PUT http://localhost:5000/api/create-user \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'
```

**3. Log in**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}' \
  -c cookies.txt
```

**4. Add a stock to the system**
```bash
curl -X POST http://localhost:5000/api/create-stock \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}' \
  -b cookies.txt
```

**5. Check the current price**
```bash
curl http://localhost:5000/api/stock-price/AAPL \
  -b cookies.txt
```

**6. Buy shares**
```bash
curl -X POST http://localhost:5000/api/portfolio/buy \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "shares": 5}' \
  -b cookies.txt
```

**7. View portfolio**
```bash
curl http://localhost:5000/api/portfolio/details \
  -b cookies.txt
```

**8. Check total portfolio value**
```bash
curl http://localhost:5000/api/portfolio/value \
  -b cookies.txt
```

**9. Sell some shares**
```bash
curl -X POST http://localhost:5000/api/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "shares": 2}' \
  -b cookies.txt
```

**10. Log out**
```bash
curl -X POST http://localhost:5000/api/logout \
  -b cookies.txt
```

> **Note:** Portfolio holdings are stored in memory and reset when the server restarts. Persisting them to the database is a known next step.

---

### Route: `/api/health`
- **Request Type**: GET  
- **Purpose**: Confirms that the service is running.  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "message": "Service is running" }
    ```

---

### Route: `/api/create-user`
- **Request Type**: PUT  
- **Purpose**: Creates a new user account.  
- **Request Body**:  
  - `username` (String): Desired username.  
  - `password` (String): Desired password.  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "message": "User 'username' created successfully" }
    ```  
- **Example Request**:  
    ```json
    { "username": "newuser", "password": "secure123" }
    ```  
- **Example Response**:  
    ```json
    { "status": "success", "message": "User 'newuser' created successfully" }
    ```

---

### Route: `/api/login`
- **Request Type**: POST  
- **Purpose**: Logs in a registered user.  
- **Request Body**:  
  - `username` (String)  
  - `password` (String)  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "message": "User 'username' logged in successfully" }
    ```  
- **Example Request**:  
    ```json
    { "username": "newuser", "password": "secure123" }
    ```

---

### Route: `/api/logout`
- **Request Type**: POST  
- **Purpose**: Logs out the current user.  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "message": "User logged out successfully" }
    ```

---

### Route: `/api/change-password`
- **Request Type**: POST  
- **Purpose**: Changes the password for the current user.  
- **Request Body**:  
  - `new_password` (String)  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "message": "Password changed successfully" }
    ```

---

### Route: `/api/reset-users`
- **Request Type**: DELETE  
- **Purpose**: Deletes all users and recreates the users table.  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "message": "Users table recreated successfully" }
    ```

---

### Route: `/api/stock-price/<ticker>`
- **Request Type**: GET  
- **Purpose**: Retrieves the current stock price from the API.  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "ticker": "AAPL", "current_price": 174.35 }
    ```

---

### Route: `/api/create-stock`
- **Request Type**: POST  
- **Purpose**: Adds a new stock to the database.  
- **Request Body**:  
  - `ticker` (String)  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "message": "Stock 'AAPL' created successfully" }
    ```  
- **Example Request**:  
    ```json
    { "ticker": "AAPL" }
    ```

---

### Route: `/api/delete-stock/<stock_id>`
- **Request Type**: DELETE  
- **Purpose**: Deletes a stock by its ID.  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "message": "Stock with ID 1 deleted successfully" }
    ```

---

### Route: `/api/portfolio/buy`
- **Request Type**: POST  
- **Purpose**: Buys a specified number of shares for the user.  
- **Request Body**:  
  - `ticker` (String)  
  - `shares` (Float or Integer)  
- **Response Format**: JSON  
  - Content:  
    ```json
    {
      "status": "success",
      "transaction": {
        "transaction_type": "BUY",
        "stock_symbol": "AAPL",
        "shares": 5,
        "price_per_share": 174.35,
        "total_cost": 871.75,
        "timestamp": 1714587812.785
      }
    }
    ```

---

### Route: `/api/portfolio/sell`
- **Request Type**: POST  
- **Purpose**: Sells a specified number of shares from the user’s portfolio.  
- **Request Body**:  
  - `ticker` (String)  
  - `shares` (Float or Integer)  
- **Response Format**: JSON  
  - Content:  
    ```json
    {
      "status": "success",
      "transaction": {
        "transaction_type": "SELL",
        "stock_symbol": "AAPL",
        "shares": 3,
        "price_per_share": 174.35,
        "total_proceeds": 523.05,
        "timestamp": 1714587900.441
      }
    }
    ```

---

### Route: `/api/portfolio/value`
- **Request Type**: GET  
- **Purpose**: Returns the total value of the user’s portfolio.  
- **Response Format**: JSON  
  - Content:  
    ```json
    { "status": "success", "portfolio_value": 2167.45 }
    ```
