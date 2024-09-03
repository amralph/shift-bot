import time
import os
import ast

from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

from dotenv import load_dotenv, find_dotenv


# credentials
load_dotenv(find_dotenv())
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
WEBSITE = os.getenv('WEBSITE')
LOCAL = os.getenv('LOCAL')
OFF_DATES = ast.literal_eval(os.getenv('OFF_DATES'))
WORK_DAYS = os.getenv('WORK_DAYS')

REFRESH_INTERVAL = 300

# time pairs
TIME_PAIR_DICT = {
    ('12:00', '20:00'): 1,
    ('14:00', '22:00'): 2,
    ('18:00', '02:00'): 3,
    ('20:00', '04:00'): 4
}

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
        driver.implicitly_wait(1)


def check_weeks(weeks, time_pair_dict, off_dates, work_days, driver):
    """Helper function for pick_up_shifts
    Will check a given week, then will pick up shifts on each day if appropriate

    Parameters:
    weeks (list of WebElement): a list of Selenium WebElement objects representing weeks
    driver (WebDriver): an instance of `selenium.webdriver.chrome.webdriver.WebDriver`

    Returns: None
    """
    for week in weeks:
        days = week.find_elements(By.CLASS_NAME, 'dayContainer')
        # then remove the last 4 days, we only care about mon, tues, wed

        # del based on work_days

        # convert the string to a list of indices
        indices_to_keep = [int(char) for char in work_days]
        # filter
        filtered_days = [days[i] for i in indices_to_keep]

        # now for each day in days, check if it's clickable
        for day in filtered_days:
            # if it's not a past day, continue
            if not ('past' in day.get_attribute('class')):
                # click the day
                day.click()
                driver.implicitly_wait(0.5)

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

                is_vacation_day = has_lieu or has_pto or has_vacu

                if is_vacation_day:
                    print(day.get_attribute("id"), 'is vacation')

                # if we have no shift today AND we don't have LIEU, PTO, or VACU in the modal, look for a shift

                # ALSO, we must check to see if the day is in OFF_DATES, OR if the day of the week is an allowed day
                is_off_date = False
                if day.get_attribute("id") in off_dates:
                    is_off_date = True
                    print(day.get_attribute("id"), 'is off day')

                available_today = not assigned_shifts_today and not is_vacation_day and not is_off_date

                if available_today:

                    print(f'Looking for work on {day.get_attribute("id")}')

                    # find the open shifts button and click it
                    find_shifts_button = driver.find_elements(By.CLASS_NAME, 'di_find_work')
                    find_shifts_button[0].click()
                    driver.implicitly_wait(1)

                    # pick up shifts if they are there...
                    # to check for shifts, find the "Select a shift you would like to take."
                    available_shifts_text = 'Select a shift you would like to take.'
                    shifts_available = bool(len(driver.find_elements(By.XPATH, f"//div[contains(text(), '{available_shifts_text}')]")))

                    if shifts_available:
                        print(f'We have shifts available on {day.get_attribute("id")}')
                        # then we pick up the shift
                        # priority
                        # 12:00 20:00
                        # 14:00 22:00
                        # 18:00 02:00
                        # 20:00 04:00

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
                                valid_rows.append((row, time_pair_dict[(start_time, end_time)]))

                        # sort the valid rows based on the priority
                        valid_rows.sort(key=lambda x: x[1])

                        # if there's a shift we want to take, click the highest priority one
                        if valid_rows:
                            valid_rows[0][0].click()
                            driver.implicitly_wait(1)
                            # click take shift button
                            # switch this to find_element by ClassName, probably will be di_take_shift
                            take_shift_button = driver.find_element(By.XPATH, "//a[text()='Take Shift']")
                            take_shift_button.click()
                            print('shift picked up')
                            driver.implicitly_wait(3)
                            close_modals(driver)
                        else:
                            # else, there is no shift we want, go to next day
                            #  close the modals and go to the next day
                            print(f'There is no shift we want on {day.get_attribute("id")}')
                            close_modals(driver)

                    else:
                        # close the modals and go to the next day
                        print(f'We have no shifts available on {day.get_attribute("id")}')
                        close_modals(driver)

                # if we do have a shift today, or we have vacation, close the modal
                else:
                    print(f'We are already working, or we do not want to work on {day.get_attribute("id")}')
                    close_buttons = driver.find_elements(By.CLASS_NAME, 'di_close')
                    close_buttons[0].click()
                    driver.implicitly_wait(1)


def pick_up_shifts(driver, time_pair_dict, off_dates, work_days):
    """Picks up shifts if they exist

    Parameters:
    driver (WebDriver): an instance of `selenium.webdriver.chrome.webdriver.WebDriver`

    Returns: None

    Raises:
    NoSuchElementException: if elements can't be found by the driver, in particular, today's date
    """
    # first verify we're on the correct page by checking if current date is in the calendar
    current_date = datetime.now().strftime("%Y%m%d")
    try:
        print('finding date')
        driver.find_element(By.ID, current_date)
        # if no error from this, we are on the correct calendar page.

        # in headless, i think it's only one week per page
        while True:
            # get calendar
            calendar_weeks = driver.find_elements(By.CLASS_NAME, 'calendarWeek')

            # for each week, do it

            check_weeks(calendar_weeks, time_pair_dict, off_dates, work_days, driver)

            next_button = driver.find_elements(By.CLASS_NAME, 'di_next')
            next_button_class = next_button[0].get_attribute('class')

            if 'disabled' not in next_button_class:
                next_button[0].click()
                driver.implicitly_wait(1)
            else:
                break


    except NoSuchElementException as e:
        print(e)
        print("Date not found. Probably on the wrong calendar page.")


if __name__ == '__main__':
    while True:
        # initialize driver LOCALLY
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

        # log in
        log_in(USER, PASSWORD, DRIVER)
        DRIVER.implicitly_wait(1)

        # going to develop code while assuming the page that shows up will always be the second page, and
        # also assume that the current week is always the middle week on the second page, and also going to assume that
        # there will always be 1 week after on the same page, then another week after that on the next page...
        pick_up_shifts(DRIVER, TIME_PAIR_DICT, OFF_DATES, WORK_DAYS)

        # kill driver (logging out is unnecessary with this line)
        DRIVER.quit()

        # run the loop every REFRESH_INTERVAL
        print("refreshing")
        time.sleep(REFRESH_INTERVAL)
