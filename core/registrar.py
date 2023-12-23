import concurrent.futures
import logging
import os
import statistics
import threading
import time
import traceback
from collections import defaultdict
from concurrent.futures import Future
from typing import List, Tuple, Union, Set, Dict

import requests
from bs4 import BeautifulSoup, ResultSet, Tag, NavigableString
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from core import util
from core.bu_course import BUCourse
from core.configuration import Configurations
from core.status import Status
from core.threadsafe.thread_safe_bool import ThreadSafeBoolean
from core.threadsafe.thread_safe_int import ThreadSafeInt

STUDENT_LINK_URL = 'https://www.bu.edu/link/bin/uiscgi_studentlink.pl'
REGISTER_SUCCESS_ICON = 'https://www.bu.edu/link/student/images/checkmark.gif'
REGISTER_FAILED_ICON = 'https://www.bu.edu/link/student/images/xmark.gif'
TOTAL_RETRY_LIMIT = 9  # Note: retry limit should ideally be at least the number of threads + 1 (5)
PER_COURSE_RETRY_LIMIT = 12  # should b
# each semester season has an id
SEMESTER_ID_DICT = {
    'spring': 4,
    'summer1': 1,
    'summer2': 2,
    'fall': 3
}


class Registrar:
    driver: webdriver
    is_planner: bool
    module: str
    target_courses: Set[BUCourse]
    season: str
    year: int
    semester_key: str
    credentials: Tuple[str, str]
    should_ignore_non_existent_courses: bool
    is_premium: bool
    is_never_give_up: bool
    max_requests_per_second_total: int
    max_requests_per_second_per_course: int

    thread_pool: concurrent.futures.ThreadPoolExecutor = concurrent.futures. \
        ThreadPoolExecutor(max_workers=4)
    # for tracking errors, if too many successive errors happen for the same
    # course, we stop trying that course -- defaultdicts are mostly threadsafe on cpython
    course_consecutive_error_counter: Dict[BUCourse, int] = defaultdict(lambda: 0)
    # total error counter, if too many successive errors happen, we exit
    all_consecutive_error_counter: ThreadSafeInt = ThreadSafeInt(0)
    # tracker keeping track of whether we are logged in
    is_logged_in: ThreadSafeBoolean = ThreadSafeBoolean(False)

    def __init__(self, credentials: Tuple[str, str], config: Configurations, is_premium: bool):
        """
        :param credentials: the tuple containing a string username and a string password to BU Kerberos
        :param config: the program config
        :param is_premium: whether this is a licensed user
        """

        logging.debug(f"User's CPU count is {os.cpu_count()}. Set max workers to {self.thread_pool._max_workers}.")

        options = util.get_chrome_options()
        service = Service() if config.driver_path == '' else Service(executable_path=config.driver_path)
        logging.debug(f"Initializing chrome driver with service_url={service.service_url} path={service.path}...")
        self.driver = webdriver.Chrome(options=options, service=service)
        self.driver.set_page_load_timeout(30)
        logging.debug(f"Browser initialized!")

        self.is_planner = config.is_planner
        self.module = 'reg/plan/add_planner.pl' if self.is_planner else 'reg/add/confirm_classes.pl'
        self.target_courses = config.course_list
        self.season = config.target_semester[0].capitalize()
        self.year = config.target_semester[1]
        self.semester_key = str(self.year) + str(SEMESTER_ID_DICT[self.season.lower()])
        self.credentials = credentials
        self.should_ignore_non_existent_courses = config.should_ignore_non_existent_courses
        self.is_premium = is_premium
        self.is_never_give_up = config.is_never_give_up
        self.max_requests_per_second_total = 99 if is_premium else 6
        self.max_requests_per_second_per_course = 30 if is_premium else 6

    def graceful_exit(self):

        logging.info('Closing thread pools...')
        self.thread_pool.shutdown(wait=False)
        logging.info('Logging off...')
        self.logout()
        logging.info('Closing browser...')
        try:
            self.driver.close()
            self.driver.quit()
        except Exception:
            print()
            # do nothing

    def __duo_login(self):
        try:
            # also check if Duo has timed us out...
            failure_elements = self.driver.find_elements(By.ID, 'error-view-header-text')
            if len(failure_elements) > 0:
                text = failure_elements[0].text
                if text == 'Duo Push timed out':
                    # start over
                    logging.warning('Oops, Duo Pushed timed out!')
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
        assert threading.current_thread().__class__.__name__ == '_MainThread', "Error! Attempted kerberos login-off " \
                                                                               "from a non-main thread."

        try:
            self.driver.get(f"{STUDENT_LINK_URL}?ModuleName=regsched.pl")
            logout_button = self.driver.find_element(By.XPATH,
                                                     '//a/img[@src="https://www.bu.edu/link/student/images'
                                                     '/header_logoff.gif"]')
            logout_button.click()
            return Status.SUCCESS
        except Exception:
            return Status.ERROR

    def login(self, override_credentials=None) -> Status:
        assert threading.current_thread().__class__.__name__ == '_MainThread', "Error! Attempted kerberos login " \
                                                                               "from a non-main thread."
        if override_credentials is not None:
            self.credentials = override_credentials
            logging.debug(f"Login attempted with new credentials for username={self.credentials[0]} and "
                          f"password={'*' * len(self.credentials[1])}")

        username, password = self.credentials

        logging.info(F'Logging into {username}\'s account...!')

        self.driver.get(f"{STUDENT_LINK_URL}?ModuleName=regsched.pl")
        logging.debug(f"Login page loaded at url={self.driver.current_url}.")
        self.driver.find_element(By.ID, 'j_username').send_keys(username)
        self.driver.find_element(By.ID, 'j_password').send_keys(password)
        self.driver.find_element(By.CLASS_NAME, 'input-submit').click()
        logging.debug(f"Password entered, and login button has been clicked.")

        bad_user_elems = self.driver.find_elements(By.CLASS_NAME, 'error-box')
        if len(bad_user_elems) > 0:
            logging.critical('Error:', bad_user_elems[0].find_element(By.CLASS_NAME, 'error').text)
            self.driver.close()
            return Status.ERROR

        duo_messaged = False
        while 'studentlink' not in self.driver.current_url:
            logging.debug(f"Now on the page with the title {self.driver.title} at url={self.driver.current_url}")
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
        self.is_logged_in.set_flag(True)
        logging.debug(f"Login flag is now set to: {self.is_logged_in}")
        return Status.SUCCESS

    """
    It looks like to prevent bot-registrations, BU requires you go through here first before you register.
    Otherwise it will prevent registration with a misleading error. AHAHA SUCK IT!
    """

    def navigate(self):
        assert threading.current_thread().__class__.__name__ == '_MainThread', "Error! Attempted to navigate to the " \
                                                                               "registration page from a non-main " \
                                                                               "thread."

        self.driver.get(
            f'{STUDENT_LINK_URL}?ModuleName=reg/option/_start.pl&ViewSem={self.season}%20{self.year}&KeySem={self.semester_key}')
        # note: the tbody tag is injected by chrome
        rows = self.driver.find_element(By.TAG_NAME, 'tbody').find_elements(By.XPATH,
                                                                            '//tr[@align="center" and @valign="top"]')
        plan = rows[0]
        register = rows[1]
        if self.is_planner:
            plan.find_element(By.TAG_NAME, 'a').click()
        else:
            register.find_element(By.TAG_NAME, 'a').click()
        time.sleep(0.5)

    '''
    Finds course listing and tries to register for the class.
    Sometimes course names are wrong, use at your own discretion. 
    '''

    def find_courses(self) -> Status.SUCCESS:
        search_start = time.time()
        original: Set[BUCourse] = self.target_courses.copy()
        cycle_durations = []
        sleep_durations = []

        while len(self.target_courses) != 0:  # keep trying until all courses are registered

            # if global error threshold reached
            if self.all_consecutive_error_counter.get() > TOTAL_RETRY_LIMIT:
                if self.is_never_give_up:
                    # first time wait 2 sec, then 4 sec, then 8 sec, then 16, 32, 64, 128, 256, 512, 600 seconds
                    # the wait times are capped at 600 seconds (10 min)
                    error_sleep_penalty = 2 ** (self.all_consecutive_error_counter.get() / TOTAL_RETRY_LIMIT)
                    error_sleep_penalty = min(600, error_sleep_penalty)
                    logging.warning(f'Number of successive failures has reached a critical threshold. '
                                    f'Going to sleep for {error_sleep_penalty} seconds.')
                    time.sleep(error_sleep_penalty)
                    logging.info(f'System is now awake again and reattempting request.')
                else:
                    logging.critical(
                        'Number of successive failures has reached its threshold. We can no longer continue.')
                    return Status.ERROR

            # if all courses have reached their respective error threshold (shouldnt happen)
            all_courses_failed = True
            for course in self.target_courses:
                if self.course_consecutive_error_counter[course] <= PER_COURSE_RETRY_LIMIT or self.is_never_give_up:
                    all_courses_failed = False
                    break
            if all_courses_failed:
                logging.critical(
                    'Number of successive failures has reached its threshold for all courses. We can no longer '
                    'continue.')
                return Status.ERROR

            start = time.time()

            # calculate the time to sleep
            # we do it here in advance in case amount of courses change
            # picks whatever rate is needed to make sure we neither exceed
            # the total rate nor the course rate
            actual_rate = min(
                len(self.target_courses) * self.max_requests_per_second_per_course,
                self.max_requests_per_second_total
            )
            min_wait_time = (len(self.target_courses) / actual_rate) * 60  # min wait time we must reach this cycle

            # Check login status
            if self.__check_if_logged_out() == Status.ERROR:
                logging.critical('Re-login failed...! We cannot continue.')
                return Status.ERROR

            # find registrable courses
            futures: List[Future[Status]] = []
            courses_and_results: List[Tuple[BUCourse, Future[Status]]] = []
            for course in self.target_courses:
                if self.course_consecutive_error_counter[course] > PER_COURSE_RETRY_LIMIT and not self.is_never_give_up:
                    logging.warning(f'Skipping course lookup for {course} due to too many successive failures in '
                                    f'finding/parsing that course.')
                    continue
                submitted_request = self.thread_pool.submit(self.__is_course_available, course)
                futures += [submitted_request]
                courses_and_results += [(course, submitted_request)]
                time.sleep(0.3)  # a small delay to prevent way too many requests together
                # ^ todo, maybe make this a dynamic val?
            # wait for the threads to finish
            concurrent.futures.wait(futures)

            # Check login status
            if self.__check_if_logged_out() == Status.ERROR:
                logging.critical('Re-login failed...! We cannot continue.')
                return Status.ERROR

            # get the list of courses that we can potentially register for
            # and set the error counters here as well
            registrable_courses: List[BUCourse] = []
            for bu_course, future_result in courses_and_results:
                course_status = future_result.result()
                if course_status == Status.SUCCESS:
                    registrable_courses += [bu_course]
                    self.__reset_error_counter(bu_course)
                elif course_status == Status.FAILURE:
                    self.__reset_error_counter(bu_course)
                elif course_status == Status.ERROR:
                    self.__increment_error_counter(bu_course)

            logging.info(f"Found {'no' if len(registrable_courses) == 0 else len(registrable_courses)} "
                         f"registrable course(s){'.' if len(registrable_courses) == 0 else '!'}")

            # for all registrable courses, register for them ASAP
            for registrable_course in registrable_courses:
                logging.info(f"Attempting to register for {registrable_course}!")
                result = self.__register_course(registrable_course)
                if result == Status.SUCCESS:
                    self.target_courses.remove(registrable_course)
                elif result == Status.FAILURE:
                    continue  # NEVER SURRENDER!!
                else:
                    logging.critical('Irrecoverable error occurred. Exiting...')
                    return Status.ERROR

            # print the State of the Union
            logging.info('----------------------------------')
            duration = (time.time() - search_start)
            logging.info(f'Running Time: {round(duration / 60 / 60, 2)} hours.')
            logging.info(f'Registration Mode: {"PLANNER" if self.is_planner else "REAL"}')
            logging.info(
                f'Course Status: {(len(original) - len(self.target_courses))}/{len(original)} courses registered')
            # print unregistered courses
            logging.info(f"  Unregistered:")
            for u in self.target_courses:
                logging.info(f"   - {u}")
            # print registered courses
            logging.info(f"  Registered:" + ('' if len(original - self.target_courses) > 0 else ' None'))
            for r in original - self.target_courses:
                logging.info(f"   - {r}")

            execution_time = time.time() - start
            time_to_wait = min_wait_time - execution_time
            if time_to_wait > 0:
                time.sleep(time_to_wait)

            cycle_durations += [execution_time]
            sleep_durations += [time_to_wait]
            cycle_durations = cycle_durations[-25:]
            sleep_durations = sleep_durations[-25:]

            logging.debug(f'Current Cycle Duration: {round(execution_time, 3)} seconds')
            logging.debug(f'Average Cycle Duration (c={len(cycle_durations)}): '
                          f'{round(statistics.mean(cycle_durations), 3)} seconds')
            logging.debug(f'Current Sleep Time [25]: {round(max(time_to_wait, 0), 3)} seconds')
            logging.debug(f'Average Sleep Time [25]: {round(statistics.mean(sleep_durations), 3)} seconds')
            logging.info(
                f'Request Rate: {60 * len(self.target_courses) / round(time_to_wait + execution_time, 4)} req/min')
            logging.info('----------------------------------')

        # we are done!
        return Status.SUCCESS

    def __register_course(self, course: BUCourse) -> Status.SUCCESS:

        assert threading.current_thread().__class__.__name__ == '_MainThread', "Error! Attempted course registration " \
                                                                               "login from a non-main thread."

        params_browse = self.__get_parameters(course)
        url_with_params = f"{STUDENT_LINK_URL}?{'&'.join([f'{key}={value}' for key, value in params_browse.items()])}"
        self.driver.get(url_with_params)

        try:
            tr_elements = self.driver.find_element(By.NAME, 'SelectForm') \
                .find_element(By.TAG_NAME, 'table') \
                .find_element(By.TAG_NAME, 'tbody') \
                .find_elements(By.TAG_NAME, 'tr')  # note: the tbody tag is injected by chrome

            found = False

            for tr_element in tr_elements:
                table_columns = tr_element.find_elements(By.TAG_NAME, 'td')

                if len(table_columns) < 11:
                    continue

                if table_columns[0].get_attribute("innerHTML") == '':
                    continue

                course_name_tag = table_columns[2]
                course_id_tag = table_columns[0]

                # self note: the spaces inside this text are really \xa0 but selenium seems to take care of that
                if course_name_tag.text == str(course):
                    found = True
                    try:
                        # this call will produce an error if the class is blocked from registration
                        course_id_tag.find_element(By.CSS_SELECTOR, "input[name='SelectIt']").click()
                        logging.info(F'Registration for {course} is open! Attempting to register now...')

                        button = self.driver.find_element(By.XPATH, "//input[@type='button']")
                        button.click()

                        # real registration requires accepting an alert
                        if not self.is_planner:
                            alert = self.driver.switch_to.alert
                            alert.accept()

                        if self.driver.title == 'Add Classes - Confirmation':
                            status_element = self.driver.find_element(By.XPATH, "//tr[@ALIGN='center'][@Valign='top']")
                            status_icon_url = status_element.find_element(By.TAG_NAME, "img").get_attribute('src')
                            if status_icon_url == REGISTER_SUCCESS_ICON:
                                return Status.SUCCESS
                            elif status_icon_url == REGISTER_FAILED_ICON:
                                reason_element = status_element.find_elements(By.TAG_NAME, 'td')[-1].find_element(
                                    By.TAG_NAME, 'font')
                                reason = reason_element.text
                                logging.warning(F'Failed to register for {course} because: \'{reason}\'')
                                if reason == "You're already registered for this class":
                                    return Status.SUCCESS  # since we are already registered, lets call it a "success"
                                return Status.FAILURE
                            else:  # this case should never happen if I made this right
                                logging.critical("Unknown registration state. This should NEVER happen!")
                                return Status.ERROR
                        elif self.driver.title == 'Error':
                            logging.warning(f'Can not register yet for {course}...')
                        else:  # the planner doesn't have a confirmation state
                            logging.info(F'Successfully registered for {course}!')
                            return Status.SUCCESS

                    except NoSuchElementException:
                        logging.warning(
                            f"Can not register yet for {course} because registration is blocked (full class?)")

                    # reset error counters
                    self.__reset_error_counter(course)

            if not found:
                logging.error(f'Error, {course} does not exist! Have you entered the correct course?')

            return Status.FAILURE

        except (Exception) as e:
            # if we got logged out log back in
            if self.driver.title == 'Boston University | Login':
                logging.warning(f'Failed to attempt registration for {course} because we are logged out!')
                self.is_logged_in.set_flag(False)
                if self.__check_if_logged_out() == Status.ERROR:
                    logging.critical('Re-login failed...! We cannot continue.')
                    return Status.ERROR
                else:
                    # increment fail counters and try again next time
                    self.__increment_error_counter(course)
                    return Status.FAILURE
            else:
                # if something else happened, increment the error counter and try again
                self.__increment_error_counter(course)

                logging.error(traceback.format_exc())
                logging.error(self.driver.page_source)
                logging.error('Unexpected page. Something went wrong. Read above dump for more info.')
                time.sleep(2)  # Sleep for a couple second as to delay the next request a bit

                return Status.FAILURE

    def __is_course_available(self, course: BUCourse) -> Status:
        # make sure they are on the correct page
        if self.driver.current_url.__contains__(f'{STUDENT_LINK_URL}?ModuleName={self.module}'):
            logging.error(F"Unexpected state. Driver is current on url={self.driver.current_url} "
                          F"but state expected the URL to be {STUDENT_LINK_URL}?ModuleName={self.module}.")
            return Status.ERROR

        params_browse = self.__get_parameters(course)
        headers = self.__get_headers()
        page_title = ''
        res = None

        try:
            res = requests.get(STUDENT_LINK_URL, params=params_browse, headers=headers)

            parser = BeautifulSoup(res.text, 'html.parser')
            page_title = parser.find('title').text

            assert page_title == 'Add Classes - Display', f"Incorrect page. Expected to be on the page \'Add " \
                                                          f"Classes - Display\' but instead ended up on " \
                                                          f"the page \'{page_title}\'."

            table_rows: ResultSet = parser.find('form').find('table').find_all('tr')

            assert len(table_rows) > 0, "Error. No course rows found. This shouldn't happen!"

            for table_row in table_rows:
                table_columns: ResultSet = table_row.find_all('td')

                if len(table_columns) < 11 or table_columns[0].text == '':
                    continue

                course_name_tag: Union[Tag, NavigableString] = table_columns[2]
                course_id_tag: Union[Tag, NavigableString] = table_columns[0]
                course_name_str = course_name_tag.text.replace('\xa0', ' ')

                if course_name_str == str(course):
                    # TODO: add a debug message displaying the reason class is closed
                    #  and the number of seats
                    if course_id_tag.select_one(selector="input[name='SelectIt']"):
                        return Status.SUCCESS
                    else:
                        return Status.FAILURE
                else:
                    if not self.should_ignore_non_existent_courses:
                        logging.error(
                            f"Error! Unable to find the course \'{course}\'. Are you sure this course exists?")
                        return Status.ERROR
                    else:
                        logging.warning(f"Warning. The course \'{course}\' does not exist (yet?). Ignoring this error "
                                        f"based on the bot configurations.")
                        return Status.FAILURE

        except (Exception) as e:

            if self.driver.title == "Boston University | Login" or \
                    page_title == 'Web Login Service - Message Security Error':
                logging.warning(f'Failed to check class status for {course} because we are no longer logged in...')
                # we don't increment fail counters for this
                # also, since this is a different thread, we can't relog from here
                self.is_logged_in.set_flag(False)
                return Status.FAILURE
            else:
                logging.error(traceback.format_exc())
                if res is not None:
                    logging.error(res.text)
                if isinstance(e, ConnectionError):
                    logging.error('Connection error. Unable to connect to the student link. Did the internet go out?')
                elif isinstance(e, AttributeError) or isinstance(e, AssertionError):
                    logging.error('Something went wrong and we were routed to an expected page. Read above dump for '
                                  'more info.')
                else:
                    logging.error('An unknown error occurred. Read above dump for more info.')
                time.sleep(2)  # Sleep for a couple second as to delay the next request a bit

                return Status.ERROR

    def __check_if_logged_out(self) -> Status:
        if self.driver.title == "Boston University | Login" or not self.is_logged_in.get_flag():
            logging.warning('Oops. We got logged out. Attempting to log back in...!')
            if self.login() != Status.SUCCESS:
                return Status.ERROR
            else:
                self.navigate()
                return Status.FAILURE
        else:
            return Status.SUCCESS

    def __reset_error_counter(self, bu_course: BUCourse):
        # TODO: improve with bettering logging

        if self.all_consecutive_error_counter.get() > 0:
            logging.debug(f'Global error counter reset from {self.all_consecutive_error_counter.get()}!')
            self.all_consecutive_error_counter.set(0)

        if self.course_consecutive_error_counter[bu_course] != 0:
            logging.debug(f'Course error counter reset from '
                         f'{self.course_consecutive_error_counter[bu_course]} for course {bu_course}!')
            self.course_consecutive_error_counter[bu_course] = 0

    def __increment_error_counter(self, bu_course: BUCourse):
        self.course_consecutive_error_counter[bu_course] += 1
        self.all_consecutive_error_counter.increment(1)
        logging.debug(f'Course error counter incremented to '
                     f'{self.course_consecutive_error_counter[bu_course]}/{PER_COURSE_RETRY_LIMIT}')
        logging.debug(f'Global error counter incremented to '
                     f'{self.all_consecutive_error_counter.get()}/{TOTAL_RETRY_LIMIT}')

    def __get_parameters(self, bu_course: BUCourse):
        college, dept, course_code, section = \
            bu_course.college, \
                bu_course.dept, \
                bu_course.course_code, \
                bu_course.section
        return {
            'College': college.upper(),
            'Dept': dept.upper(),
            'Course': course_code,
            'Section': section.upper(),
            'ModuleName': 'reg/add/browse_schedule.pl',
            'AddPreregInd': '',
            'AddPlannerInd': 'Y' if self.is_planner else '',
            'ViewSem': self.season + ' ' + str(self.year),
            'KeySem': self.semester_key,
            'PreregViewSem': '',
            'SearchOptionCd': 'S',
            'SearchOptionDesc': 'Class Number',
            'MainCampusInd': '',
            'BrowseContinueInd': '',
            'ShoppingCartInd': '',
            'ShoppingCartList': ''
        }

    def __get_headers(self):
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Cookie': "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in self.driver.get_cookies()]),
            'Host': 'www.bu.edu',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/118.0.0.0 Safari/537.36'
        }
# https://www.bu.edu/link/bin/uiscgi_studentlink.pl?SelectIt=0001190094&College=CAS&Dept=CS&Course=440&Section=A3&ModuleName=reg%2Fplan%2Fadd_planner.pl&AddPreregInd=&AddPlannerInd=Y&ViewSem=Spring+2024&KeySem=20244&PreregViewSem=&PreregKeySem=&SearchOptionCd=S&SearchOptionDesc=Class+Number&MainCampusInd=&BrowseContinueInd=&ShoppingCartInd=&ShoppingCartList=
