import time
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from dotenv import load_dotenv, find_dotenv


# credentials
load_dotenv(find_dotenv())
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
WEBSITE = os.getenv('WEBSITE')

REFRESH_INTERVAL = 5


def log_in(user, password, driver):
    """Logs in user in the browser given user, password, and driver

    Parameters:
    user (string): user id

    password (string): password

    driver (WebDriver): an instance of `selenium.webdriver.chrome.webdriver.WebDriver`

    Returns: none

    Raises:
    NoSuchElementException: if elements can't be found by the driver
    """
    try:
        # find elements, and if not found, raise exception (the code will break if you don't do this)
        username_box = driver.find_element(By.ID, 'txtUserName')
        password_box = driver.find_element(By.ID, 'txtPassword')
        sign_in_button = driver.find_element(By.ID, 'cmdLogin')

        # clear boxes before typing (good practice)
        username_box.clear()
        password_box.clear()

        # type in username and password
        username_box.send_keys(user)
        password_box.send_keys(password)

        # press log in button
        sign_in_button.click()

    except NoSuchElementException as e:
        print(e)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    while True:
        # initialize driver
        DRIVER = webdriver.Chrome()
        DRIVER.get(WEBSITE)

        print(type(DRIVER))

        # log in
        log_in(USER, PASSWORD, DRIVER)

        # do stuff
        time.sleep(5)

        # kill driver (logging out is unnecessary with this line
        DRIVER.quit()

        # run the loop every REFRESH_INTERVAL
        time.sleep(REFRESH_INTERVAL)
