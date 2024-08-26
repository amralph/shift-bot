import time
import os
from datetime import datetime, date, timezone

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


def pick_up_shifts(driver):
    # first verify we're on the correct page by checking if current date is in the calendar
    current_date = datetime.now().strftime("%Y%m%d")

    try:
        driver.find_element(By.ID, current_date)
        # if no error from this, we are on the correct calendar page.

        # now that we know we're on the correct page, we need to check every monday, tuesday and wednesday possible
        # which comes on or after our current date

        # so first, for each day we check, first check if we don;t have a shift for this day

    except NoSuchElementException as e:
        print(e)
        print("Date not found. Probably on the wrong calendar page.")


if __name__ == '__main__':

    while True:
        # initialize driver
        DRIVER = webdriver.Chrome()
        DRIVER.get(WEBSITE)

        # log in
        log_in(USER, PASSWORD, DRIVER)

        # iterate over dates... how can we do this? Monday will always be first in a week row, and so on
        # we could also verify with a calendar library function

        # find_shifts()

        # do stuff
        time.sleep(5)

        # check date, if no shifts on that date (determined by "You have no shifts on this day") then press Find Extra Shifts
        # if extra shifts available, pick up shift
        # repeat this for all days...


        # get current date
        # check monday, tuesday, wednesday that comes after current date
        # the html has a box with seven days for each week

        # gonna develop code while assuming the page that shows up will always be the second page, and
        # also assume that the current week is always the middle week on the second page, and also going to assume that
        # there will always be 1 week after on the same page, then another week after that on the next page...

        pick_up_shifts(DRIVER)



        # kill driver (logging out is unnecessary with this line)
        DRIVER.quit()

        # run the loop every REFRESH_INTERVAL
        time.sleep(REFRESH_INTERVAL)
