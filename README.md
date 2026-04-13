# Trading App API

## Overview
This Flask-based trading application allows users to register, log in, and manage a virtual stock portfolio. Users can add stocks by ticker symbol, fetch real-time prices via the Alpha Vantage API, buy and sell shares, and calculate the total value of their holdings. Flask-Login handles session management, and SQLAlchemy handles database interactions.

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

The full flow below can be run in PowerShell. The `$session` variable carries the login cookie across requests.

**1. Health check**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/health"
```

**2. Create a user**
```powershell
Invoke-RestMethod -Method PUT -Uri "http://localhost:5000/api/create-user" -ContentType "application/json" -Body '{"username": "alice", "password": "secret123"}'
```

**3. Log in**
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:5000/api/login" -ContentType "application/json" -Body '{"username": "alice", "password": "secret123"}' -SessionVariable session
```

**4. Add a stock to the system**
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:5000/api/create-stock" -ContentType "application/json" -Body '{"ticker": "AAPL"}' -WebSession $session
```

**5. Check the current price**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/stock-price/AAPL" -WebSession $session
```

**6. Buy shares**
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:5000/api/portfolio/buy" -ContentType "application/json" -Body '{"ticker": "AAPL", "shares": 5}' -WebSession $session
```

**7. View portfolio**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/portfolio/details" -WebSession $session
```

**8. Check total portfolio value**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/portfolio/value" -WebSession $session
```

**9. Sell some shares**
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:5000/api/portfolio/sell" -ContentType "application/json" -Body '{"ticker": "AAPL", "shares": 2}' -WebSession $session
```

**10. Log out**
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:5000/api/logout" -WebSession $session
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
