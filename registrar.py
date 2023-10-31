import logging
import platform
import re
import time
from enum import Enum
from typing import List, Tuple

from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import util

STUDENT_LINK_URL = 'https://www.bu.edu/link/bin/uiscgi_studentlink.pl'
RETRY_LIMIT = 3

season_to_key = {
    'spring': 4,
    'summer1': 1,
    'summer2': 2,
    'fall': 3
}

class Status(Enum):
    ERROR = 2
    SUCCESS = 1
    FAILURE = 0


class Registrar():
    driver: webdriver
    is_planner: bool
    module: str
    target_courses: List[Tuple[str, str, str, str]]
    season: str
    year: int
    semester_key: str
    credentials: Tuple[str, str]

    error_counter: int = 0 # for tracking errors, if too many successive errors happen, we exit
    def __init__(self, credentials: Tuple[str, str], planner: bool, season: str, year: int, target_courses: List[Tuple[str, str, str, str]]):

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        service = Service(
            executable_path="/usr/lib/chromium-browser/chromedriver") if platform.system() == "Linux" else Service()

        self.driver = webdriver.Chrome(options=options, service=service)

        self.driver.set_page_load_timeout(30)
        self.is_planner = planner
        self.module = 'reg/plan/add_planner.pl' if planner else 'reg/add/confirm_classes.pl'
        self.target_courses = target_courses
        self.season = season.capitalize()
        self.year = year
        self.semester_key = str(year) + str(season_to_key[season.lower()])
        self.credentials = credentials

    def __duo_login(self):
        try:
            # also check if Duo has timed us out...
            failure_elements = self.driver.find_elements(By.ID, 'error-view-header-text')
            if len(failure_elements) > 0:
                text = failure_elements[0].text
                if text == 'Duo Push timed out':
                    # start over
                    logging.warning('Oops, Duo Pushed timed out!')
                    self.driver.close()
                    return Status.FAILURE
            # trust browser so we can log back in without duo when BU times us out
            dont_trust_elements = self.driver.find_elements(By.ID, 'trust-browser-button')
            if len(dont_trust_elements) > 0:
                dont_trust_elements[0].click()
        except NoSuchElementException:
            logging.critical('Unexpected page. Something went wrong. Dumping page...')
            logging.critical(self.driver.page_source)
            return Status.ERROR

    """
    NOTE: Intended only for testing
    """
    def logout(self) -> Status:
        try:
            self.driver.get(f"{STUDENT_LINK_URL}?ModuleName=regsched.pl")
            logout_button = self.driver.find_element(By.XPATH, '//a/img[@src="https://www.bu.edu/link/student/images/header_logoff.gif"]')
            logout_button.click()
            return Status.SUCCESS
        except Exception:
            return Status.ERROR

    def login(self, override_credentials=None) -> Status:

        if override_credentials is not None:
            self.credentials = override_credentials

        username, password = self.credentials

        logging.info(F'Logging into {username}\'s account...!')

        self.driver.get(f"{STUDENT_LINK_URL}?ModuleName=regsched.pl")
        self.driver.find_element(By.ID, 'j_username').send_keys(username)
        self.driver.find_element(By.ID, 'j_password').send_keys(password)
        self.driver.find_element(By.CLASS_NAME, 'input-submit').click()

        bad_user_elems = self.driver.find_elements(By.CLASS_NAME, 'error-box')
        if len(bad_user_elems) > 0:
            logging.critical('Error:', bad_user_elems[0].find_element(By.CLASS_NAME, 'error').text)
            self.driver.close()
            return Status.ERROR

        duo_messaged = False
        while 'studentlink' not in self.driver.current_url:
            if 'duosecurity' in self.driver.current_url:
                if not duo_messaged:
                    logging.info('Waiting for you to approve this login on Duo...')
                    duo_messaged = True
                # if duo login false, we fail
                status = self.__duo_login()
                if status == Status.FAILURE or status == Status.ERROR:
                    return status
                # wait a couple sec
                time.sleep(2)

        logging.info(F'Successfully logged into {username}\'s account!')
        return Status.SUCCESS

    #TODO: get a list of registered courses and remove them from the list of courses

    """
    It looks like to prevent bot-registrations, BU requires you go through here first before you register.
    Otherwise it will prevent registration with a misleading error. AHAHA SUCK IT!
    """
    def navigate(self):
        self.driver.get(f'{STUDENT_LINK_URL}?ModuleName=reg/option/_start.pl&ViewSem={self.season}%20{self.year}&KeySem={self.semester_key}')
        rows = self.driver.find_element(By.TAG_NAME, 'tbody').find_elements(By.XPATH, '//tr[@align="center" and @valign="top"]')
        plan = rows[0]
        register = rows[1]
        if self.is_planner:
            plan.find_element(By.TAG_NAME, 'a').click()
        else:
            register.find_element(By.TAG_NAME, 'a').click()
        time.sleep(1)

    '''
    Finds course listing and tries to register for the class.
    Sometimes course names are wrong, use at your own discretion. 
    '''
    def find_courses(self) -> Status.SUCCESS:
        start = time.time()
        cycles = 0
        original_len = len(self.target_courses)

        while len(self.target_courses) != 0:  # keep trying until all courses are registered
            for course in self.target_courses:
                duration = (time.time() - start)
                logging.info(f'Running since the past {round(duration/60/60, 2)} hours...')
                result = self.__find_course(course)
                time.sleep(0.5) # can't have bu get mad at us for spamming them too hard <3
                if result == Status.SUCCESS:
                    self.target_courses.remove(course)
                    logging.info(F'Successfully registered for {course}!')
                elif result == Status.FAILURE:
                    continue # NEVER SURRENDER!!
                else:
                    logging.critical('Irrecoverable error occurred. Exiting...')
                    exit(1)
            logging.info('--------------------------')
            logging.info(f'{(original_len - len(self.target_courses))}/{original_len} courses have been registered for!')
            logging.info('--------------------------')
            cycles += 1

        # we are done!
        self.driver.close()
        self.driver.quit()

    def __find_course(self, course: (str, str, str, str)) -> Status.SUCCESS:
        college, dept, course, section = course
        name = dept.upper() + course + ' ' + section.upper()
        params_browse = self.generate_params(college, dept, course, section)
        url_with_params = f"{STUDENT_LINK_URL}?{'&'.join([f'{key}={value}' for key, value in params_browse.items()])}"
        self.driver.get(url_with_params)

        try:
            tr_elements = self.driver.find_element(By.NAME, 'SelectForm')\
                .find_element(By.TAG_NAME, 'table')\
                .find_element(By.TAG_NAME, 'tbody')\
                .find_elements(By.TAG_NAME, 'tr')

            found = False

            for tr_element in tr_elements:
                if len(tr_element.find_elements(By.TAG_NAME, 'td')) < 11:
                    continue
                course_name_tag = tr_element.find_elements(By.TAG_NAME, 'td')[2]
                course_id_tag = tr_element.find_elements(By.TAG_NAME, 'td')[0]
                if course_name_tag.text == college.upper() + ' ' + dept.upper() + course + ' ' + section.upper():
                    found = True
                    try:
                        course_id_tag.find_element(By.CSS_SELECTOR, "input[name='SelectIt']").click()
                        button = self.driver.find_element(By.XPATH, "//input[@type='button']")
                        button.click()
                        # real registration requires accepting an alert
                        if not self.is_planner:
                            alert = self.driver.switch_to.alert
                            alert.accept()
                        o = re.search('<title>Error</title>', self.driver.page_source)
                        if o:
                            logging.warning(f'Can not register yet for {name}...')
                        else:
                            return Status.SUCCESS
                    except NoSuchElementException:
                        logging.warning(f"Can not register yet for {name} because registration is blocked (full class?)")

                    self.error_counter = 0 # reset error counter

            if not found:
                logging.error('could not find course')

        except (NoSuchElementException, StaleElementReferenceException) as e:
            # if we got logged out log back in
            if self.driver.title == 'Boston University | Login':
                logging.warning('Oops. We got logged out. Attempting to log back in...!')
                if self.login() != Status.SUCCESS:
                    logging.critical('Re-login failed...! We cannot continue.')
                    return Status.ERROR
            else:
                # if something else happened, increment the error counter and try again
                self.error_counter += 1

                # if the error counter exceeds max errors, exit
                if self.error_counter > RETRY_LIMIT:
                    logging.critical('Unexpected page. Something went wrong. Dumping page and exiting...')
                    logging.critical(self.driver.page_source)
                    return Status.ERROR
                # if retry threshold not reach, simply return a failure and retry later
                else:
                    logging.error('Unexpected page. Something went wrong. Retrying...')

        return Status.FAILURE

    def generate_params(self, college, dept, course, section):
        return {
            'College': college.upper(),
            'Dept': dept.upper(),
            'Course': course,
            'Section': section.upper(),
            'ModuleName': 'reg/add/browse_schedule.pl',
            'AddPreregInd': '',
            'AddPlannerInd': 'Y' if self.is_planner else '',
            'ViewSem': self.season + ' ' + str(self.year),
            'KeySem': self.semester_key,
            'PreregViewSem':  '',
            'SearchOptionCd': 'S',
            'SearchOptionDesc': 'Class Number',
            'MainCampusInd': '',
            'BrowseContinueInd': '',
            'ShoppingCartInd': '',
            'ShoppingCartList': ''
        }
