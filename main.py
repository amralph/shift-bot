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

REFRESH_INTERVAL = 100
logged_in = False


def log_in(user, password, driver):
    global logged_in

    try:
        # find elements, if not found, raise exception (the code will break if you don't do this)
        username_box = driver.find_element(By.ID, 'txtUserName')
        password_box = driver.find_element(By.ID, 'txtPassword')
        sign_in_button = driver.find_element(By.ID, 'cmdLogin')

        # clear boxes (good practice)
        username_box.clear()
        password_box.clear()

        # type in username and password
        username_box.send_keys(user)
        password_box.send_keys(password)

        # press log in button
        sign_in_button.click()

        # need to verify that user is actually logged in!!!

        # set logged_in to true
        logged_in = True

    except NoSuchElementException:
        print("Element not found")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    DRIVER = webdriver.Chrome()
    DRIVER.get(WEBSITE)

    if not logged_in:
        log_in(USER, PASSWORD, DRIVER)

    while True:
        # run the loop every REFRESH_INTERVAL
        time.sleep(REFRESH_INTERVAL)
