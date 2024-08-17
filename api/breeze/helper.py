
import os
from dotenv import load_dotenv
import pyotp
from breeze_connect import BreezeConnect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize SDK
breeze = BreezeConnect(api_key=os.getenv('BREEZE_API_KEY'))

class BreezeSessionLogin:

    def __init__(self):
        pass

    def get_totp_code(self):
        # The secret key should be stored securely, preferably in an environment variable
        totp_secret = os.getenv('ICICI_TOTP_SECRET')
        totp = pyotp.TOTP(totp_secret)
        return totp.now()

    def login_with_totp(self, driver, username, password, api_key):
        login_url = f"https://api.icicidirect.com/apiuser/login?api_key={api_key}"
        driver.get(login_url)

        # Wait for and fill in the username
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)

        # Fill in the password
        driver.find_element(By.ID, "password").send_keys(password)

        # Click the login button
        driver.find_element(By.ID, "loginBtn").click()

        # Wait for TOTP input field
        totp_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "totp_input_id"))  # Replace with actual ID
        )

        # Generate and enter TOTP
        totp_code = self.get_totp_code()
        totp_input.send_keys(totp_code)

        # Submit TOTP
        driver.find_element(By.ID, "submit_totp_button_id").click()  # Replace with actual ID

        # Wait for and extract session token
        session_token = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "session_token"))  # Replace with actual ID
        ).text

        return session_token

    def get_session_token(self):
        driver = webdriver.Chrome()  # Make sure you have chromedriver installed and in PATH
        try:
            username = os.getenv('BREEZE_USERNAME')
            password = os.getenv('BREEZE_PASSWORD')
            api_key = os.getenv('BREEZE_API_KEY')
            print(f"{username}")
            print(f"{password}")
            print(f"{api_key}")
            return self.login_with_totp(driver, username, password, api_key)
        finally:
            driver.quit()



# sl_obj = BreezeSessionLogin()

# # Use the function to get the session token
# session_token = sl_obj.get_session_token()
# print(f"{session_token = }")

# # Generate Session
# breeze.generate_session(api_secret=os.getenv('BREEZE_API_SECRET'),
#                         session_token=session_token)
