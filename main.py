# adapted from https://github.com/juliusfrost/BU-Registration-Bot/blob/master/reg.py

from typing import Tuple
from registrar import Registrar, Status

# Put here the list of courses you want to register for
# Ex. ('cas','wr','100','a1')
my_courses = [
    ('CAS', 'CS', '585', 'A1'),
    ('CAS', 'CS', '460', 'A1'),
    ('CAS', 'CS', '460', 'A2'),
]

# in test mode, we will only add courses to the planner just to make sure stuff works
test_mode = True

################################################################
# Don't modify below here unless you know what you are doing
################################################################
def credentials() -> (str, str):
    # you could replace this with your literal username and password...
    # but that's insecure :)
    bu_username = input('Enter your BU username: ')
    bu_password = input("Enter your BU password: ")
    return bu_username, bu_password

def semester() -> Tuple[str, int]:
    while True:
        semester = input('What semester are you trying to register for (e.g. Fall 2024, Spring 2025, Summer 1 2023, '
                         'Summer 2 2025)? ').strip()
        split = semester.split(" ")
        season = split[0]
        if (season.lower() != 'spring' and season.lower() != 'summer 1' and season.lower() != 'summer 2' and season.lower() != 'fall') or len(split) != 2:
            print('Invalid semester entry. Make sure you use the same format shown in the examples! Lets try that '
                  'again.')
            continue
        try:
            year = int(split[1])
        except ValueError:
            print(F"Bud. {split[1]} is not a valid year. Hell, it doesn't even look like a number. Lets try that again.")
            continue
        return season, year

if __name__ == "__main__":
    season, year = semester()
    creds = credentials()
    registrar = Registrar(creds, test_mode, season, year, my_courses)
    while registrar.login() != Status.SUCCESS:
        print('Hmm... Lets try that again...')
        registrar.login(credentials())
    registrar.navigate()
    if registrar.find_courses() == Status.SUCCESS:
        print('Successfully registered for all courses :)')
    exit(0)
