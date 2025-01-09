# THIS VERSION WILL BE MAINLY FOR SETTING UP BASIC PREFERENCE SORTING
# T6 involves using easier file formatting
# T9 Involves an update to file format, including a # of available seats value, to determine if the course section is available.
# T9 file format also involves a ticker with an "canOverlap" flag, as some items like Exams, and other specific courses
# might want to be displayed
#
from itertools import product
from tabulate import tabulate
import tkinter as tk
from tkinter import ttk


# FOR PARSING COURSES
# "&" symbol is for reading number of courses line
# "#" symbol is for reading the Course name and Course Code line
# "~" symbol is for reading the Section Code line
# "!" symbol is for reading a Class line (includes Lectures, Labs, Seminars, Tutorials, and final Exams)
def parse_available_courses(file_name):
    timetable = {}
    current_course = ""
    current_section = ""
    global numCourses

    with open(file_name, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith('&'):  # Num Courses
                numCourses = line[1:]
            elif line == "":  # Skip empty lines
                pass
            elif line.startswith('#'):  # Course
                course_info = line[1:].split('-')
                current_course = course_info[0].strip()
                course_code = course_info[1].strip() if len(course_info) >= 2 else ""

                timetable[current_course] = {"code": course_code, "sections": {}}
            elif line.startswith('~'):  # Section
                section_info = line[1:].strip()
                current_section = section_info
                timetable[current_course]["sections"][current_section] = []
            elif line.startswith('!'):  # Classes
                class_info = line[1:].split(',')
                class_type = class_info[0].strip()
                start_time_hour = class_info[1].strip()
                start_time_minute = class_info[2].strip()
                start_mer = class_info[3].strip()

                end_time_hour = class_info[4].strip()
                end_time_minute = class_info[5].strip()
                end_mer = class_info[6].strip()

                day = class_info[7].strip()
                location = class_info[8].strip()

                start_time = f"{start_time_hour}:{start_time_minute}"
                end_time = f"{end_time_hour}:{end_time_minute}"

                timetable[current_course]["sections"][current_section].append(
                    {
                        "type": class_type,
                        "location": location,
                        "start_time": start_time,
                        "start_mer": start_mer,
                        "end_time": end_time,
                        "end_mer": end_mer,
                        "day": day,
                    }
                )
                # print(class_info)

    print(numCourses)
    return timetable


def has_overlaps(timetable_combination):  # also checking preferences here for now
    global invalidTimetables, tooManyClasses, tmfc, tooEarly, tooLate

    # print(timetable_combination)
    days = ['M', 'T', 'W', 'TH', 'F']

    for day in days:
        numClasses = 0
        classes = []
        for course_info in timetable_combination.values():
            classes += course_info['classes']

        for class_info in classes:
            if class_info['day'] == day:
                numClasses += 1

        if checkNCOF:
            if day == 'F' and numClasses > numFridayClasses:
                tmfc = True
                invalidTimetables += 1
                return True
            # print(f"For {day}, there are {numClasses} classes")

        if checkNCPD:
            if numClasses > numClassesPerDays:
                # print("Classes per day for this option exceed Preference, therefore invalid")
                tooManyClasses = True
                invalidTimetables += 1
                return True

        # area for too early/too late preference check
        # for too early
        for class_info in classes:
            if checkST:
                found12 = int(class_info['start_time'].split(':')[0])
                set12 = int(startTime.split(':')[0])
                if class_info['start_mer'] == sM and found12 <= set12:
                    if found12 == 12:
                        found12 = 0
                    if set12 == 12:
                        set12 = 0
                    # print(found12)
                    # print(set12)

                    if set12 == found12:
                        if int(class_info['start_time'].split(':')[1]) < int(startTime.split(':')[1]):
                            tooEarly = True
                            invalidTimetables += 1
                            return True
                    elif set12 > found12:
                        tooEarly = True
                        invalidTimetables += 1
                        return True
                elif class_info['start_mer'] != sM:
                    tooEarly = False
            # for too late
            if checkET:
                found12 = int(class_info['end_time'].split(':')[0])
                set12 = int(endTime.split(':')[0])
                if class_info['end_mer'] == eM and found12 >= set12:
                    if found12 == 12:
                        found12 = 0
                    if set12 == 12:
                        set12 = 0

                    if set12 == found12:
                        if int(class_info['end_time'].split(':')[1]) > int(endTime.split(':')[1]):
                            tooLate = True
                            invalidTimetables += 1
                            return True
                    elif set12 < found12:
                        tooLate = True
                        invalidTimetables += 1
                        return True
                elif class_info['end_mer'] != eM:
                    tooLate = False

        day_classes = [class_info for class_info in classes if class_info['day'] == day]
        day_classes.sort(key=lambda x: x['start_time'])

        for i in range(len(day_classes)):
            class_1 = day_classes[i]
            start_time_1 = class_1['start_time']
            end_time_1 = class_1['end_time']

            for j in range(i + 1, len(day_classes)):
                class_2 = day_classes[j]
                start_time_2 = class_2['start_time']
                end_time_2 = class_2['end_time']

                if start_time_1 <= start_time_2 <= end_time_1 or start_time_1 <= end_time_2 <= end_time_1:
                    # print(start_time_1)
                    # print(end_time_1)
                    # print(start_time_2)
                    # print(end_time_2)
                    # print("Invalid: Overlapping classes")
                    invalidTimetables += 1
                    return True

                if start_time_1 == start_time_2 and end_time_1 == end_time_2:
                    # print("Invalid: Classes at the exact same time")
                    invalidTimetables += 1
                    return True

    # print("Valid: No overlapping classes")
    return False


def find_valid_timetables(available_courses, numCourses):
    # print(available_courses)
    courses = list(available_courses.keys())  # Gets course names; ex: ['Mathematics and design', 'Physics']

    sections = [list(course_info['sections'].keys()) for course_info in
                available_courses.values()]  # gets all the available sections
    combinations = list(product(*sections))  # Gets all the different combinations of sections
    # print(combinations)

    valid_timetables = []
    for combination in combinations:
        timetable_combination = {
            course: {"course_name": course, "code": available_courses[course]['code'], "section": section,
                     "classes": []}
            for course, section in zip(courses, combination)}

        for course, course_info in timetable_combination.items():
            section = course_info['section']
            classes = available_courses[course]['sections'][section]
            timetable_combination[course]['classes'] = classes

        # print(timetable_combination)

        if not has_overlaps(timetable_combination):
            valid_timetables.append(timetable_combination)

    return valid_timetables


def sortCombination(combination):
    sortedCombo = []
    temp = []
    eTime = 0
    for a, b in combination.items():
        for c in b['classes']:
            # print(c)
            if c['day'] == 'M':
                # print(b['code'] + " " + c['type'] + " " + c['start_time'].split(':')[0] + " " + c['start_mer'] + " " + c['day'])
                tempeTime = c['start_time'].split(':')[0]
                teT = int(tempeTime)
                # print(teT)
                if teT < eTime and len(temp) == 0:
                    temp.append(teT)
                    eTime = teT
                if teT > eTime:
                    sortedCombo.append(teT)
                    for i in temp:
                        sortedCombo.append(i)
                    temp = []
        # print(sortedCombo)

    return sortedCombo


def print_timetable_graph(timetable_combinations):
    global options
    days = ['SU', 'M', 'T', 'W', 'TH', 'F', 'S']
    dayNames = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    timetable_table = [[''] + dayNames]

    for i, combination in enumerate(timetable_combinations,
                                    start=1):  # NOTE: these combinations are already valid, not overlapping, but need to be sorted
        row = [f"Option {i}"]
        # print(combination.items())
        # print(combination['Biological Concepts of Health']['classes'])

        optionList = [f"Option {i}"]

        sortedCombinations = sortCombination(
            combination)  # Function that will sort the combinations based on their times

        for day in days:
            slots = []
            for course, course_info in combination.items():
                section = course_info['section']
                classes = available_courses[course]['sections'][section]
                slots += [(class_info['start_time'], class_info['start_mer'], class_info['end_time'],
                           class_info['end_mer'], course_info['course_name'], section,
                           class_info['type'], class_info['location'])
                          for class_info in classes if class_info['day'] == day]

            # print(slots)
            slots.sort(reverse=False)
            # print(slots)
            slots_str = ''
            prev_end = None

            for start, startMer, end, endMer, course_name, section, class_type, location in slots:
                if prev_end and start > prev_end:
                    slots_str += '\n'  # Add line break between courses
                slots_str += f"{course_name} - {section}\n{class_type} - {location}\n{start}{startMer} - {end}{endMer}\n"
                prev_end = end

            row.append(slots_str)
            optionList.append(slots_str)

        timetable_table.append(row)
        options.append(optionList)
        # print()

    print(tabulate(timetable_table, headers='firstrow', tablefmt='fancy_grid'))


def printOption(index):
    row = []
    found = False
    dayNames = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    data = [[''] + dayNames]
    for option in options:
        if option[0].split("Option ")[1] == str(index):
            found = True
            data.append(option[:])
            print(tabulate(data, headers='firstrow', tablefmt='fancy_grid'))


class Window:
    def __init__(self, master, valid_timetables):
        self.master = master
        # self.excluded_options = invalidTimetables + valid_timetables

        self.valid_timetables = valid_timetables
        self.master.title("Timetable Viewer")
        self.current_index = 0

        self.label_var = tk.StringVar()
        self.label_var.set("Timetable Viewer")
        self.label = tk.Label(master, text=f"Option {self.current_index}", font=("Arial", 12))
        self.label.pack()

        # self.timetable_display = tk.Label(master, text=self.valid_timetables[self.current_index])
        # self.timetable_display.pack()

        self.prev_button = tk.Button(master, text="◄", command=self.show_prev_timetable)
        self.prev_button.pack(side=tk.LEFT)

        self.next_button = tk.Button(master, text="►", command=self.show_next_timetable)
        self.next_button.pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(master, width=800, height=500, bg="gray")
        # self.canvas
        self.canvas.pack()

        self.update_timetable_display()

    def show_prev_timetable(self):
        self.current_index = (self.current_index - 1) % len(self.valid_timetables)
        self.update_timetable_display()


    def show_next_timetable(self):
        self.current_index = (self.current_index + 1) % len(self.valid_timetables)
        self.update_timetable_display()

    def update_timetable_display(self):
        timetable_text = self.valid_timetables[self.current_index]
        self.canvas.delete("all")
        self.canvas.create_text(200, 100, text=timetable_text, font=("Arial", 12), anchor="center")
        self.label_var.set(f"Timetable Viewer - {timetable_text}")


        # self.open_GUI(self)



    def open_GUI(self):
        pass


# Toggle preference check
checkNCPD = True  # num classes per day
checkNCOF = True  # num class on friday
checkST = False  # check start times
checkET = False  # check end times

# PREFERENCES
numClassesPerDays = 5
numFridayClasses = 3
# time preferences
startTime = "8:00"
sM = "am"
endTime = "5:30"
eM = "pm"

# to set up

# ///////// FLAG
tooManyClasses = False
tmfc = False
tooEarly = False
tooLate = False

# ////////////////

options = []
running = True

numCourses = -1
invalidTimetables = 0
file_name = "myCourses.txt"  # Replace with your input file name
available_courses = parse_available_courses(file_name)
valid_timetables = find_valid_timetables(available_courses, numCourses)

if len(valid_timetables) > 0:
    # print(f"Avoided {invalidTimetables} invalid timetable combinations.\n")
    # print(f"Found {len(valid_timetables)} possible timetable combinations:\n")
    print_timetable_graph(valid_timetables)
    print(f"Avoided {invalidTimetables} invalid timetable combinations.\n")
    print(f"Found {len(valid_timetables)} possible timetable combinations:\n")
else:
    print(f"Found {invalidTimetables} invalid timetable combinations.\n")
    print("No valid timetable combinations found.")
    if tooManyClasses:
        print("Too many classes per day, exceeded preference")
    if tmfc:
        print("Exceed requested number of classes on friday :P")
    if tooEarly:
        print("No combinations can be made with classes earlier than set time, wake up earlier!")
    if tooLate:
        print("No combinations can be made with classes later than set time, sorry, you've got a long day :(")

# printOption(1)

# print(numCourses)

while running:
    print("Please select an option (print number) to continue: ")
    print("\t1.Print a specific table")
    print("\t2.Open GUI Interface")
    print("\t3.Exit the program")

    option = input("Option: ")

    if option == "1":
        print("\nPlease provide the table # (number) that you would like to print")
        print(f"NOTE: there are {len(valid_timetables)} options available to choose from.")
        tableNumber = input("Table No:")
        printOption(tableNumber)
    elif option == "2":
        print("Opening GUI Interface")
        # displayTable(tableNumber)
        root = tk.Tk()
        window = Window(root, valid_timetables)
        root.mainloop()
