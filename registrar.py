import re
import time
from enum import Enum
from typing import List, Tuple

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

STUDENT_LINK_URL = 'https://www.bu.edu/link/bin/uiscgi_studentlink.pl'

season_to_key = {
    'spring': 4,
    'summer 1': 1,
    'summer 2': 2,
    'fall': 3
}

class Status(Enum):
    ERROR = 2
    SUCCESS = 1
    FAILURE = 0


class Registrar():
    driver: WebDriver
    is_planner: bool
    module: str
    target_courses: List[Tuple[str, str, str, str]]
    season: str
    year: int
    semester_key: str

    def __init__(self, planner: bool, season: str, year: int, target_courses: List[Tuple[str, str, str, str]]):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(chrome_options)
        self.driver.set_page_load_timeout(30)
        self.is_planner = planner
        self.module = 'reg/plan/add_planner.pl' if planner else 'reg/add/confirm_classes.pl'
        self.target_courses = target_courses
        self.season = season.capitalize()
        self.year = year
        self.semester_key = str(year) + str(season_to_key[season.lower()])

    def login(self, credentials: Tuple[str, str]) -> Status:
        print('Logging in...')
        self.driver.get(f"{STUDENT_LINK_URL}?ModuleName=regsched.pl")
        username, password = credentials
        self.driver.find_element(By.ID, 'j_username').send_keys(username)
        self.driver.find_element(By.ID, 'j_password').send_keys(password)
        self.driver.find_element(By.CLASS_NAME, 'input-submit').click()

        bad_user_elems = self.driver.find_elements(By.CLASS_NAME, 'error-box')
        if len(bad_user_elems) > 0:
            print('Error:', bad_user_elems[0].find_element(By.CLASS_NAME, 'error').text)
            self.driver.close()
            return Status.ERROR

        duo_messaged = False
        while 'studentlink' not in self.driver.current_url:
            if 'duosecurity' in self.driver.current_url:
                if not duo_messaged:
                    print('Waiting for you to approve this login on Duo...')
                    duo_messaged = True
                # also check if Duo has timed us out...
                failure_elements = self.driver.find_elements(By.ID, 'error-view-header-text')
                if len(failure_elements) > 0:
                    text = failure_elements[0].text
                    if text == 'Duo Push timed out':
                        # start over
                        print('Oops, Duo Pushed timed out!')
                        self.driver.close()
                        return Status.ERROR
                # once login is approved, Duo asks whether to "trust" this device.
                # we are paranoid people so we answer 'no'
                dont_trust_elements = self.driver.find_elements(By.ID, 'dont-trust-browser-button')
                if len(dont_trust_elements) > 0:
                    dont_trust_elements[0].click()
                # wait a couple sec
                time.sleep(2)

        print('Successfully Logged in!')
        return Status.SUCCESS

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
        if len(self.target_courses) == 0:
            print("Error! You haven't specified any target courses")
            return Status.ERROR
        original_len = len(self.target_courses)
        while len(self.target_courses) != 0:  # keep trying forever!
            for course in self.target_courses:
                duration = (time.time() - start)
                print(f'\n[{time.asctime()}] [Current Runtime: {round(duration/60/60, 2)} hours]')
                result = self.__find_course(course)
                if result == Status.SUCCESS:
                    self.target_courses.remove(course)
                    print(F'Successfully registered for {course}')
                elif result == Status.FAILURE:
                    continue # NEVER SURRENDER!!
                else:
                    print('Irrecoverable error occurred. Exiting...')
                    exit(1)
            print('----------------')
            print(f'{(original_len - len(self.target_courses))}/{original_len} courses have been registered for!')
            print('----------------')
            cycles += 1
            time.sleep(2)  # can't have bu get mad at us for spamming them <3

        self.driver.close() # we are done!

    def __find_course(self, course: (str, str, str, str)) -> Status.SUCCESS:
        college, dept, course, section = course
        name = dept.upper() + course + ' ' + section.upper()
        params_browse = self.generate_params(college, dept, course, section)
        url_with_params = f"{STUDENT_LINK_URL}?{'&'.join([f'{key}={value}' for key, value in params_browse.items()])}"
        self.driver.get(url_with_params)

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
                        print(f'Can not register yet for {name}...')
                    else:
                        return Status.SUCCESS
                except NoSuchElementException:
                    print(f"Can not register yet for {name} because registration is blocked (full class?)")

        if not found:
            print('could not find course')

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

    def generate_reg_params(self, college, dept, course, section, ssid):
        return {
                'SelectIt': ssid,
                'College': college.upper(),
                'Dept': dept.upper(),
                'Course': course,
                'Section': section.upper(),
                'ModuleName': self.module,
                'AddPreregInd': '',
                'AddPlannerInd': 'Y' if self.is_planner else '',
                'ViewSem': self.season + ' ' + str(self.year),
                'KeySem': self.semester_key,
                'PreregViewSem': '',
                'PreregKeySem': '',
                'SearchOptionCd': 'S',
                'SearchOptionDesc': 'Class Number',
                'MainCampusInd': '',
                'BrowseContinueInd': '',
                'ShoppingCartInd': '',
                'ShoppingCartList': ''
        }
