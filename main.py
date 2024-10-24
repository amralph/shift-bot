import os
import ast
import time
import traceback
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

from dotenv import load_dotenv, find_dotenv

import firebase_admin
from firebase_admin import credentials, firestore


# credentials
load_dotenv(find_dotenv())
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
WEBSITE = os.getenv('WEBSITE')
LOCAL = os.getenv('LOCAL')
OFF_DATES = ast.literal_eval(os.getenv('OFF_DATES'))
WORK_DAYS = os.getenv('WORK_DAYS')
FIREBASE_CONFIG = json.loads(os.getenv('FIREBASE_CONFIG'))
ARMED = os.getenv('ARMED')
ENV = os.getenv('ENV')

REFRESH_INTERVAL = 1

# time pairs
TIME_PAIR_DICT = {
    ('12:00', '20:00'): 1,
    ('14:00', '22:00'): 2,
}

def initialize_firebase(firebase_config):
    """Initializes firebase
    Parameters:
    firebase_config (dictionary): dictionary of firebase configurations

    Returns: None
    """
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)


def log_in(user, password, driver):
    """Logs in user in the browser given user, password, and driver

    Parameters:
    user (string): user id
    password (string): password
    driver (WebDriver): an instance of `selenium.webdriver.chrome.webdriver.WebDriver`

    Returns: None

    Raises:
    NoSuchElementException: if elements can't be found by the driver
    """
    print('signing in')
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


def close_modals(driver):
    """Closes modals on the screen that have di_close in its class
    works hopefully by getting a list of all di_close buttons
    and because they will appear from top layer to bottom layer,
    we close them in reverse order

    Parameters:
    driver (WebDriver): an instance of `selenium.webdriver.chrome.webdriver.WebDriver`

    Returns: None
    """
    close_buttons = driver.find_elements(By.CLASS_NAME, 'di_close')

    for button in reversed(close_buttons):
        button.click()


def check_weeks(weeks, time_pair_dict, off_dates, work_days, driver, database, armed):
    """Helper function for pick_up_shifts
    Will check a given week, then will pick up shifts on each day if appropriate

    Parameters:
    weeks (list of WebElement): a list of Selenium WebElement objects representing weeks
    time_pair_dict (dictionary): a dictionary whose keys are tuples of times and values are a priority
    off_dates (list of strings): a list of strings representing dates
    work_days (string of digits): a string of digits representing days of the week
    driver (WebDriver): an instance of `selenium.webdriver.chrome.webdriver.WebDriver`
    database (Firestore Client): a client for Firestore
    armed (TRUE or FALSE): a string which arms the bot to pick up shifts

    Returns: None
    """
    for week in weeks:
        days = week.find_elements(By.CLASS_NAME, 'dayContainer')
        # convert the string to a list of indices
        indices_to_keep = [int(char) for char in work_days]
        # filter
        filtered_days = [days[i] for i in indices_to_keep]

        # now for each day in days, check if it's clickable
        for day in filtered_days:
            # if it's not a past day, continue
            if not ('past' in day.get_attribute('class')):
                # check day to see if we have vacation, have it off, or already working
                vacation_words = ["LIEU", "PTO", "VACU"]
                working_words = ["TG DLR"]
                # before clicking, check if day is vacation or off date, or already working.
                if any(vacation_word in day.text for vacation_word in vacation_words):
                    print(day.get_attribute("id") + ' is vacation')
                elif day.get_attribute("id") in off_dates:
                    print(day.get_attribute("id") + ' is off day')
                elif any(working_word in day.text for working_word in working_words):
                    print(day.get_attribute("id") + ' already working')
                else:
                    day.click()
                    print(f'{day.get_attribute("id")} looking for work')

                    # find the open shifts button and click it
                    find_shifts_button = driver.find_elements(By.CLASS_NAME, 'di_find_work')
                    find_shifts_button[0].click()

                    # pick up shifts if they are there...
                    # to check for shifts, find the "Select a shift you would like to take."
                    available_shifts_text = 'Select a shift you would like to take.'
                    shifts_available = bool(len(driver.find_elements(By.XPATH, f"//div[contains(text(), '{available_shifts_text}')]")))

                    if shifts_available:
                        print(f'Shifts available on {day.get_attribute("id")}')
                        # then we pick up the shift

                        # pick up the table
                        shifts_table = driver.find_elements(By.TAG_NAME, 'table')[0]

                        # get all rows in the table except the first one
                        rows = shifts_table.find_elements(By.TAG_NAME, 'tr')
                        del rows[0]

                        valid_rows = []

                        # filter out the rows that don't contain our valid time pairs
                        for row in rows:
                            start_time = row.find_element(By.CLASS_NAME, 'starttime').text
                            end_time = row.find_element(By.CLASS_NAME, 'endtime').text

                            # check if starttime and endtime is in the list of valid pairs
                            if (start_time, end_time) in time_pair_dict:
                                # insert a tuple into valid_rows, (row, priority of that row)
                                valid_rows.append((row, time_pair_dict[(start_time, end_time)], start_time, end_time))

                        # sort the valid rows based on the priority
                        valid_rows.sort(key=lambda x: x[1])

                        # if there's a shift we want to take, click the highest priority one
                        if valid_rows:
                            if armed == 'TRUE':
                                # at the first row info, click the row [0][0]
                                valid_rows[0][0].click()
                                # click take shift button
                                # switch this to find_element by ClassName, probably will be di_take_shift
                                take_shift_button = driver.find_element(By.XPATH, "//a[text()='Take Shift']")
                                take_shift_button.click()
                                print('shift picked up')

                                # put it in db
                                doc_ref = database.collection('shifts_picked_up').document(day.get_attribute("id")).set({
                                    'date': day.get_attribute("id"),
                                    'start_time': valid_rows[0][2],
                                    'end_time': valid_rows[0][3],
                                    'current_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                                    'local': LOCAL,
                                    'env': ENV
                                })

                                print(doc_ref)

                                close_modals(driver)
                            else:
                                print('Bot is not armed')
                        else:
                            # else, there is no shift we want, go to next day
                            #  close the modals and go to the next day
                            print(f'No shift we want on {day.get_attribute("id")}')
                            close_modals(driver)
                    else:
                        # close the modals and go to the next day
                        close_modals(driver)


def pick_up_shifts(driver, time_pair_dict, off_dates, work_days, database, armed):
    """Picks up shifts if they exist

    Parameters:
    driver (WebDriver): an instance of `selenium.webdriver.chrome.webdriver.WebDriver`
    time_pair_dict (dictionary): a dictionary whose keys are tuples of times and values are a priority
    off_dates (list of strings): a list of strings representing dates
    work_days (string of digits): a string of digits representing days of the week
    database (Firestore Client): a client for Firestore
    armed (TRUE or FALSE): a string which arms the bot to pick up shifts

    Returns: None

    Raises:
    NoSuchElementException: if elements can't be found by the driver, in particular, today's date
    """
    # in headless, i think it's only one week per page
    # go to front of calendar, if it starts in the future
    while True:
        previous_button = driver.find_elements(By.CLASS_NAME, 'di_previous')

        if len(previous_button) > 0:


            previous_button_class = previous_button[0].get_attribute('class')
            if 'disabled' not in previous_button_class:
                previous_button[0].click()
            else:
                break
        else:
            break
    # move to the end of calendar
    while True:
        # get calendar
        calendar_weeks = driver.find_elements(By.CLASS_NAME, 'calendarWeek')

        # for each week, do it
        check_weeks(calendar_weeks, time_pair_dict, off_dates, work_days, driver, database, armed)

        next_button = driver.find_elements(By.CLASS_NAME, 'di_next')

        if len(next_button) > 0:
            next_button_class = next_button[0].get_attribute('class')

            if 'disabled' not in next_button_class:
                next_button[0].click()
            else:
                break
        else:
            break

if __name__ == '__main__':
    print('start')
    if ARMED == 'TRUE':
        print('Shift Bot is armed: A shift will be picked up if one is found')
    else:
        print('Shift Bot is not armed: A shift will not be picked up if one is found')

    print('Looking for the following shifts with their priorities:', TIME_PAIR_DICT)

    print('initializing db')
    initialize_firebase(FIREBASE_CONFIG)
    db = firestore.client()

    while True:
        DRIVER = None
        try:
            print('loop')
            # initialize driver LOCALLY
            print('initialize driver')
            if LOCAL == 'TRUE':
                DRIVER = webdriver.Chrome()
            else:
                # initialize driver in Heroku
                chrome_options = Options()
                chrome_options.add_argument("--headless=chrome")  # Run in headless mode
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                DRIVER = webdriver.Chrome(options=chrome_options)

            DRIVER.get(WEBSITE)
            DRIVER.implicitly_wait(0.5)

            log_in(USER, PASSWORD, DRIVER)
            pick_up_shifts(DRIVER, TIME_PAIR_DICT, OFF_DATES, WORK_DAYS, db, ARMED)

        except Exception as e:
            print(e)
            traceback.print_exc()
            db.collection('errors').add({
                'message': str(e),
                'traceback': traceback.format_exc(),
                'current_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                'local': LOCAL,
                'env': ENV
            })

        finally:
            # kill driver (logging out is unnecessary with this line)
            if DRIVER:
                print('quitting driver')
                DRIVER.quit()


        print('waiting...')
        time.sleep(REFRESH_INTERVAL)

