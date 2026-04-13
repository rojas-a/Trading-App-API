import requests


def run_smoketest():
    base_url = "http://localhost:5000/api"
    username = "smoketest_user"
    password = "smoketest_pass"

    # Health check
    health_response = requests.get(f"{base_url}/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "success"
    print("Health check passed")

    # Reset users table for a clean slate
    reset_response = requests.delete(f"{base_url}/reset-users")
    assert reset_response.status_code == 200
    assert reset_response.json()["status"] == "success"
    print("Reset users successful")

    # Create a user
    create_user_response = requests.put(f"{base_url}/create-user", json={
        "username": username,
        "password": password
    })
    assert create_user_response.status_code == 201
    assert create_user_response.json()["status"] == "success"
    print("User creation successful")

    # Use a session so cookies persist (Flask-Login)
    session = requests.Session()

    # Log in
    login_resp = session.post(f"{base_url}/login", json={
        "username": username,
        "password": password
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["status"] == "success"
    print("Login successful")

    # Create a stock
    create_stock_resp = session.post(f"{base_url}/create-stock", json={"ticker": "AAPL"})
    assert create_stock_resp.status_code == 201
    assert create_stock_resp.json()["status"] == "success"
    print("Stock creation successful")

    # Fetch stock price
    price_resp = session.get(f"{base_url}/stock-price/AAPL")
    assert price_resp.status_code == 200
    assert price_resp.json()["status"] == "success"
    print(f"Stock price fetched: ${price_resp.json()['current_price']}")

    # Buy shares
    buy_resp = session.post(f"{base_url}/portfolio/buy", json={
        "ticker": "AAPL",
        "shares": 5
    })
    assert buy_resp.status_code == 200
    assert buy_resp.json()["status"] == "success"
    print(f"Buy successful: {buy_resp.json()['transaction']}")

    # Check portfolio value
    value_resp = session.get(f"{base_url}/portfolio/value")
    assert value_resp.status_code == 200
    assert value_resp.json()["status"] == "success"
    print(f"Portfolio value: ${value_resp.json()['portfolio_value']}")

    # View portfolio details
    details_resp = session.get(f"{base_url}/portfolio/details")
    assert details_resp.status_code == 200
    assert details_resp.json()["status"] == "success"
    print(f"Portfolio details: {details_resp.json()['portfolio']}")

    # Change password
    change_password_resp = session.post(f"{base_url}/change-password", json={
        "new_password": "new_smoketest_pass"
    })
    assert change_password_resp.status_code == 200
    assert change_password_resp.json()["status"] == "success"
    print("Password change successful")

    # Sell shares
    sell_resp = session.post(f"{base_url}/portfolio/sell", json={
        "ticker": "AAPL",
        "shares": 2
    })
    assert sell_resp.status_code == 200
    assert sell_resp.json()["status"] == "success"
    print(f"Sell successful: {sell_resp.json()['transaction']}")

    # Log out
    logout_resp = session.post(f"{base_url}/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "success"
    print("Logout successful")

    # Confirm protected routes reject unauthenticated requests
    unauth_resp = session.get(f"{base_url}/portfolio/value")
    assert unauth_resp.status_code == 401
    assert unauth_resp.json()["status"] == "error"
    print("Unauthenticated request correctly rejected")

    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    run_smoketest()
