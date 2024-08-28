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

REFRESH_INTERVAL = 2


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


def check_weeks(weeks, driver):
    for week in weeks:
        days = week.find_elements(By.CLASS_NAME, 'dayContainer')
        # then remove the last 4 days, we only care about mon, tues, wed
        #del days[3:]

        # now for each day in days, check if it's clickable
        for day in days:
            # if it's not a past day, continue
            if not ('past' in day.get_attribute('class')):
                # click the day
                driver.implicitly_wait(1)
                day.click()
                driver.implicitly_wait(1)

                # pick up day modal
                day_modal = driver.find_element(By.CLASS_NAME, 'modal-content')

                # check if we have shifts today
                no_assigned_shifts_text = 'You have no shifts on this day.'
                # there's a shift if we don't find an element that says 'You have no shifts on this day.'.
                assigned_shifts_today = not bool(len(day_modal.find_elements(By.XPATH, f".//div[contains(text(), '{no_assigned_shifts_text}')]")))

                # also, we really do not want to even check for shifts if we booked it off
                # the following words will appear in the modal if it's booked off.
                has_lieu = bool(len(day_modal.find_elements(By.XPATH, f".//div[contains(text(), 'LIEU')]")))
                has_pto = bool(len(day_modal.find_elements(By.XPATH, f".//div[contains(text(), 'PTO')]")))
                has_vacu = bool(len(day_modal.find_elements(By.XPATH, f".//div[contains(text(), 'VACU')]")))


                # if we have no shift today AND we don't have LIEU, PTO, or VACU in the modal, look for a shift
                if not assigned_shifts_today and not (has_lieu or has_pto or has_vacu):
                    try:
                        # find the open shifts button and click it
                        find_shifts_button = driver.find_element(By.CLASS_NAME, 'di_find_work')
                        find_shifts_button.click()
                        driver.implicitly_wait(1)

                        # pick up shifts if they are there...
                        # to check for shifts, find the "Select a shift you would like to take."
                        available_shifts_text = 'Select a shift you would like to take.'
                        shifts_available = bool(len(driver.find_elements(By.XPATH, f"//div[contains(text(), '{available_shifts_text}')]")))

                        if shifts_available:
                            print(f'We have shifts available on {day.get_attribute("id")}')
                            # then we pick up the shift
                        else:
                            print(f'We do not have shifts available on {day.get_attribute("id")}')
                        #  close the modals and go to the next day
                        close_buttons = driver.find_elements(By.CLASS_NAME, 'di_close')
                        close_buttons[1].click()
                        driver.implicitly_wait(1)
                        close_buttons[0].click()
                        driver.implicitly_wait(1)

                    except NoSuchElementException as e:
                        print(e)
                        print('Could not find di_find_work button.')
                # if we do have a shift today, close the modal
                else:
                    close_buttons = driver.find_elements(By.CLASS_NAME, 'di_close')
                    close_buttons[0].click()
                    driver.implicitly_wait(1)


def pick_up_shifts(driver):
    # first verify we're on the correct page by checking if current date is in the calendar
    current_date = datetime.now().strftime("%Y%m%d")
    try:
        driver.find_element(By.ID, current_date)
        # if no error from this, we are on the correct calendar page.

        # get second and third calendar week elements, based on our assumption that our current week will always
        # be the second week of the second page
        calendar_weeks_first_page = driver.find_elements(By.CLASS_NAME, 'calendarWeek')

        # we only care about the last two weeks here, so delete the first week
        del calendar_weeks_first_page[0]

        # do the check weeks logic
        check_weeks(calendar_weeks_first_page, driver)

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

        DRIVER.implicitly_wait(1)

        # find_shifts()

        # do stuff

        # going to develop code while assuming the page that shows up will always be the second page, and
        # also assume that the current week is always the middle week on the second page, and also going to assume that
        # there will always be 1 week after on the same page, then another week after that on the next page...
        pick_up_shifts(DRIVER)

        # kill driver (logging out is unnecessary with this line)
        DRIVER.quit()

        # run the loop every REFRESH_INTERVAL
        time.sleep(REFRESH_INTERVAL)
