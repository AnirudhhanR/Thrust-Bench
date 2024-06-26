import pygame
import serial
import csv
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog
import yaml
import numpy as np
from matplotlib import animation


# Initialize serial connection
ser = serial.Serial(port='COM3', baudrate=9600)
active_entry = (0, 0)  # Initialize active_entry to a default value
graphlist = []

graph_open = False
count = 0
pick = None
# Initialize Pygame
pygame.init()

# Create game window
SCREEN_WIDTH = 1520
SCREEN_HEIGHT = 770


throttle_entry = ''
entry_box_x = SCREEN_WIDTH - 300  # Define entry_box_x in the global scope
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sensor Data Visualization")

csv_file_path = " Downloads/sensor_data.csv"
csv_header = ["Voltage", "Current", "Torque1", "Torque2", "Thrust"]
data_collection_active = False

# Define fonts and colors
font = pygame.font.SysFont("arialblack", 24)
TEXT_COL = (255, 255, 255)
BOX_COLOR = (150, 150, 50)
ENTRY_COLOR = (150, 150, 150)
ACTIVE_ENTRY_COLOR = (200, 200, 200)

# Define button coordinates
HALT_BUTTON_X = SCREEN_WIDTH - 180
HALT_BUTTON_Y = SCREEN_HEIGHT - 180
HALT_BUTTON_RADIUS = 80

# Game variables
menu_state = "home"
receive_data = True
data_values = {"Voltage": 0, "Current": 0, "Torque1": 0, "Torque2": 0, "Thrust": 0}

# Entry box parameters
entry_width = 100
entry_height = 40
entry_x = [700, 1100]  # X positions for entry boxes
entry_y = [200, 300]  # Y positions for entry boxes
entry_text = [["", ""], ["", ""]]  # Initial text for entry boxes

data_collection_list = []

# Entry box labels
entry_labels = [["Voltage Min", "Voltage Max"],
                ["Current Min", "Current Max"],]

def append_data_to_csv(data):
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

def draw_set_throttle_button():
    button_x = 1170  # Adjusted x-coordinate for the button
    button_y = 125
    pygame.draw.rect(screen, ENTRY_COLOR, (button_x, button_y, entry_width + 100, entry_height), 2)
    draw_text("Set Throttle", font, TEXT_COL, button_x + 10, button_y + 10)

def draw_general_data():
    data_y = 200
    for key, value in data_values.items():
        text = f"{key}: {value}"
        draw_text(text, font, TEXT_COL, 400, data_y)
        data_y += 100

    draw_throttle_entry()

def handle_general_menu_event(event):
    global throttle_entry
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_BACKSPACE:
            throttle_entry = throttle_entry[:-1]  # Remove last character
        elif event.key == pygame.K_RETURN:
            try:
                float_value = float(throttle_entry)  # Convert the entered text to float
                throttle_entry = str(float_value)  # Update the throttle entry with the valid float
                print(f"Current custom entry box: {throttle_entry}")
            except ValueError:
                print("Invalid input. Please enter a valid float value.")
                throttle_entry = ""  # Clear the entry box if not a valid float
        else:
            # Add typed character to entry text only if it results in a valid float
            try:
                float(throttle_entry + event.unicode)
                throttle_entry += event.unicode
            except ValueError:
                print("Invalid input. Please enter a valid float value.")


def draw_throttle_entry():
    entry_box_x = SCREEN_WIDTH - 300
    pygame.draw.rect(screen, ENTRY_COLOR, (entry_box_x, 50 + 20, entry_width, entry_height), 2)
    draw_text("Throttle", font, TEXT_COL, entry_box_x - 120, 50 + 30)
    draw_text(throttle_entry, font, TEXT_COL, entry_box_x + 10, 50 + 30)

    # Add this line to display the throttle value
    draw_text(f"Throttle Value: {throttle_entry}", font, TEXT_COL, 1150, 50 + 120   )

# Function to draw text on the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Function to read and process serial data
def read_serial_data():
    global receive_data, data_values, data_collection_active, data_collection_list, graphlist
    try:
        if ser.in_waiting > 0 and receive_data:
            data = ser.readline().decode('UTF-8').strip()
            # print("Received data from Arduino:", data)  # Debug statement
            values = [float(value) for value in data.split("\t") if value.strip()]
            # print("Parsed values:", values)  # Debug statement
            if len(values) == 5:
                data_values["Voltage"], data_values["Current"], data_values["Torque1"], data_values["Torque2"], data_values["Thrust"] = values
                # print("Updated data values:", data_values)
                graphlist = values
                # Append data to the list when data collection is active
                if data_collection_active:
                    data_collection_list.append(values)

    except ValueError as e:
        print("Error processing serial data:", e)


# Function to draw the menu 
def draw_menu():
    menu_items = ["General", "Limits", "Graph", "Data Collection","Custom Setup"]  
    menu_y = 50
    box_width = 200
    box_height = 70
    for item in menu_items:
        pygame.draw.rect(screen, BOX_COLOR, (50, menu_y, box_width, box_height), 2)
        draw_text(item, font, TEXT_COL, 50 + 10, menu_y + 10)
        menu_y += 100

# Function to draw data in the General section
def draw_general_data():
    data_y = 200  # Adjusted y-coordinate to move the entry box up
    data_y1 = 50
    for key, value in data_values.items():
        text = f"{key}: {value}"
        draw_text(text, font, TEXT_COL, 400, data_y)
        data_y += 100

    draw_throttle_entry()
    # Add an entry box for a custom value on the right side
    entry_box_x = SCREEN_WIDTH - 300  # Adjusted x-coordinate for the right side
    pygame.draw.rect(screen, ENTRY_COLOR, (entry_box_x, data_y1 + 20, entry_width, entry_height), 2)
    draw_text("", font, TEXT_COL, entry_box_x - 200, data_y1 + 30)
    draw_text(entry_text[0][0], font, TEXT_COL, entry_box_x + 10, data_y1 + 30)

# Function to draw entry boxes and buttons in the Limits menu
def draw_limits_entry_boxes():
    for i in range(min(len(entry_y), len(entry_text))):  # Use the minimum length to avoid IndexError
        for j in range(len(entry_x)):
            color = ACTIVE_ENTRY_COLOR if (active_entry[0] == i and active_entry[1] == j) else (255, 255, 255)
            pygame.draw.rect(screen, color, (entry_x[j], entry_y[i], entry_width, entry_height), 2)
            draw_text(entry_labels[i][j], font, TEXT_COL, entry_x[j] - 200, entry_y[i] + 10)
            draw_text(entry_text[i][j], font, TEXT_COL, entry_x[j] + 10, entry_y[i] + 10)

    # Draw the "Send Data" button
    pygame.draw.rect(screen, BOX_COLOR, (50, 600, 200, 70), 2)
    draw_text("Send Data", font, TEXT_COL, 50 + 10, 600 + 10)


# Function to draw the HALT button
def draw_halt_button():
    pygame.draw.circle(screen, (255, 0, 0), (HALT_BUTTON_X, HALT_BUTTON_Y), HALT_BUTTON_RADIUS, 0)
    draw_text("HALT", font, TEXT_COL, HALT_BUTTON_X - 40, HALT_BUTTON_Y - 20)

def send_data_to_arduino():
    try:
        # Read values from entry boxes
        voltage_min = float(entry_text[0][0])
        voltage_max = float(entry_text[0][1])
        current_min = float(entry_text[1][0])
        current_max = float(entry_text[1][1])

        # Format data and send it to Arduino
        data_to_send = f"LIMITS {voltage_min} {voltage_max} {current_min} {current_max}"
        ser.write(data_to_send.encode())

        print("Data sent to Arduino:", data_to_send)
    except ValueError:
        print("Error: Invalid input. Please enter valid float values in all entry boxes.")

def send_throttle_to_arduino(throttle_value):
    try:
        # Format data and send it to Arduino
        data_to_send = f"SET_THROTTLE {throttle_value}\n"
        ser.write(data_to_send.encode())
        print("Throttle Data sent to Arduino:", data_to_send)

        # Clear the entry box after sending the throttle value
        global throttle_entry
        throttle_entry = ""
        # Update the data_values dictionary to store the latest throttle value
        data_values["Throttle"] = throttle_value
    except ValueError:
        print("Error: Invalid throttle input.")



def handle_data_collection_button_click(x, y):
    global data_collection_active, data_collection_list, csv_file_path

    button_width = 150
    button_height = 50
    button_x = 400
    button_y1 = 300
    button_y2 = 370
    button_y3 = 440

    if button_x <= x <= button_x + button_width and button_y1 <= y <= button_y1 + button_height:
        print("Clicked on Start Button")
        data_collection_active = True
        # Add functionality for Start Button here
    elif button_x <= x <= button_x + button_width and button_y2 <= y <= button_y2 + button_height:
        print("Clicked on Stop Button")
        data_collection_active = False
        if data_collection_list:
            # Convert the list to CSV when the "Stop" button is pressed
            save_data_to_csv(data_collection_list)
        # Add functionality for Stop Button here
    elif button_x <= x <= button_x + button_width and button_y3 <= y <= button_y3 + button_height:
        print("Clicked on Browse Button")
        choose_save_location()


def handle_custom_setup():
    # Add code here to handle events specific to the "Custom Setup" menu, if needed
    pass


def draw_custom_setup():
    custom_setup_text = "Custom Setup: Choose config file"

    # Draw main text
    draw_text(custom_setup_text, font, TEXT_COL, 400, 200)

    # Draw "Browse" button
    browse_button_x = 400
    browse_button_y = 300
    pygame.draw.rect(screen, BOX_COLOR, (browse_button_x, browse_button_y, 200, 50), 2)
    draw_text("Browse", font, TEXT_COL, browse_button_x + 10, browse_button_y + 10)

    # Draw "Use" button
    use_button_x = 400
    use_button_y = 370
    pygame.draw.rect(screen, BOX_COLOR, (use_button_x, use_button_y, 200, 50), 2)
    draw_text("Use", font, TEXT_COL, use_button_x + 10, use_button_y + 10)

    # draw "Sample Graph" button
    graph_button_x = 800
    graph_button_y = 300
    pygame.draw.rect(screen, BOX_COLOR, (graph_button_x, graph_button_y, 200, 50), 2)
    draw_text("Sample Graph", font, TEXT_COL, graph_button_x + 10, graph_button_y + 10)

    # Handle button clicks
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
            x, y = event.pos
            if browse_button_x <= x <= browse_button_x + 200 and browse_button_y <= y <= browse_button_y + 50:
                print("Clicked on Browse Button")
                choose_file()  # Call the function to open a file dialog
            elif use_button_x <= x <= use_button_x + 200 and use_button_y <= y <= use_button_y + 50:
                print("Clicked on Use Button")
                use_file()
            elif graph_button_x <= x <= graph_button_x + 200 and graph_button_y <= y <= graph_button_y + 50:
                print("Clicked on Sample Graph Button")
                plot_throttle_profile(use_file())
                # Add functionality for the "Use" button here

def plot_throttle_profile(params):
    def generate_throttle_profile(params):
        min_throttle = params['min_throttle']
        max_throttle = params['max_throttle']
        total_duration = params['total_duration']
        rise_time = params['rise_time']
        fall_time = params['fall_time']
        step = params['step']
        step_duration = params['step_duration']

        # Generate time array
        time = np.arange(0, total_duration)  
        # Initialize throttle profile array
        throttle_profile = np.full_like(time, min_throttle)

        # Calculate rise and fall rate
        rise_rate = (max_throttle - min_throttle) / rise_time
        fall_rate = (max_throttle - min_throttle) / fall_time

        # Apply rise time
        rise_end_index = int(rise_time / step_duration)
        throttle_profile[:rise_end_index] = min_throttle + rise_rate * time[:rise_end_index]

        # Apply constant throttle
        constant_throttle_start_index = rise_end_index
        constant_throttle_end_index = constant_throttle_start_index + int((total_duration - rise_time - fall_time) / step_duration)
        throttle_profile[constant_throttle_start_index:constant_throttle_end_index] = max_throttle

        # Apply fall time
        fall_start_index = constant_throttle_end_index
        throttle_profile[fall_start_index:] = max_throttle - fall_rate * (time[fall_start_index:] - rise_time - (total_duration - rise_time - fall_time))

        return time, throttle_profile

    
    # Generate throttle profile
    time, throttle_profile = generate_throttle_profile(params)

    # Plotting the graph
    plt.plot(time, throttle_profile)
    plt.title('Throttle vs Time')
    plt.xlabel('Time (s)')
    plt.ylabel('Throttle')
    plt.grid(True)
    plt.show()

    
def choose_file():
    root = Tk()
    global yaml_file_path
    root.withdraw()  # Hide the main window
    yaml_file_path = filedialog.askopenfilename(filetypes=[("YAML Files", "*.yaml .yml"), ("All files", "*.*")])
    print("Selected file:", yaml_file_path)
    # with open(yaml_file_path, "r") as pp:
    #     data = yaml.safe_load(pp)
    #     print(data)

        # Perform actions with the selected file path here

def use_file():
    with open(yaml_file_path, "r") as pp:
        data = yaml.safe_load(pp)
        print(data)
    return data

# Function to draw content in the "Data Collection" menu
def draw_data_collection():
    global data_collection_active, csv_file_path

    data_collection_text = "Data Collection Options"

    # Draw main text
    draw_text(data_collection_text, font, TEXT_COL, 400, 200)

    # Draw three buttons
    button_width = 150
    button_height = 50
    button_x = 400
    button_y1 = 300
    button_y2 = 370
    button_y3 = 440

    pygame.draw.rect(screen, BOX_COLOR, (button_x, button_y1, button_width, button_height), 2)
    draw_text("Start", font, TEXT_COL, button_x + 10, button_y1 + 10)

    pygame.draw.rect(screen, BOX_COLOR, (button_x, button_y2, button_width, button_height), 2)
    draw_text("Stop", font, TEXT_COL, button_x + 10, button_y2 + 10)

    pygame.draw.rect(screen, BOX_COLOR, (button_x, button_y3, button_width, button_height), 2)
    draw_text("Browse...", font, TEXT_COL, button_x + 10, button_y3 + 10)

    # Draw data collection status
    draw_text(f"Data Collection Status: {'Active' if data_collection_active else 'Inactive'}", font, TEXT_COL, 400, 550)

    # Handle button clicks
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
            x, y = event.pos
            handle_data_collection_button_click(x, y)


def choose_save_location():
    global csv_file_path
    root = Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        csv_file_path = file_path
        print(csv_file_path)

# Function to draw content in the "Data Collection" menu
def draw_data_collection():
    data_collection_text = "This is the Data Collection menu. Add your content here."     

    # Draw main text
    draw_text(data_collection_text, font, TEXT_COL, 400, 200)

    # Draw three buttons
    button_width = 150
    button_height = 50
    button_x = 400
    button_y1 = 300
    button_y2 = 370
    button_y3 = 440

    pygame.draw.rect(screen, BOX_COLOR, (button_x, button_y1, button_width, button_height), 2)
    draw_text("Start", font, TEXT_COL, button_x + 10, button_y1 + 10)

    pygame.draw.rect(screen, BOX_COLOR, (button_x, button_y2, button_width, button_height), 2)
    draw_text("Stop", font, TEXT_COL, button_x + 10, button_y2 + 10)

    pygame.draw.rect(screen, BOX_COLOR, (button_x, button_y3, button_width, button_height), 2)
    draw_text("Browse...", font, TEXT_COL, button_x + 10, button_y3 + 10)

    # Handle button clicks
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
            x, y = event.pos
            handle_data_collection_button_click(x, y)

# def draw_custom_setup():
#     custom_setup_text = "This is the Custom Setup menu. Add your content here."

#     # Draw main text
#     draw_text(custom_setup_text, font, TEXT_COL, 400, 200)

#     # Draw "Browse" button
#     browse_button_x = 400
#     browse_button_y = 300
#     pygame.draw.rect(screen, BOX_COLOR, (browse_button_x, browse_button_y, 200, 50), 2)
#     draw_text("Browse", font, TEXT_COL, browse_button_x + 10, browse_button_y + 10)

#     # Draw "Use" button
#     use_button_x = 400
#     use_button_y = 370
#     pygame.draw.rect(screen, BOX_COLOR, (use_button_x, use_button_y, 200, 50), 2)
#     draw_text("Use", font, TEXT_COL, use_button_x + 10, use_button_y + 10)

#     graph_button_x = 500
#     graph_button_y = 300
#     pygame.draw.rect(screen, BOX_COLOR, (graph_button_x, graph_button_y, 200, 50), 2)
#     draw_text("Sample Graph", font, TEXT_COL, graph_button_x + 10, graph_button_y + 10)

#     # Handle button clicks
#     for event in pygame.event.get():
#         if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
#             x, y = event.pos
#             if browse_button_x <= x <= browse_button_x + 200 and browse_button_y <= y <= browse_button_y + 50:
#                 print("Clicked on Browse Button")
#                 choose_file()

#             elif use_button_x <= x <= use_button_x + 200 and use_button_y <= y <= use_button_y + 50:
#                 print("Clicked on Use Button")
#                 use_file()
                # Add functionality for the "Use" button here

# def choose_file():
#     root = Tk()
#     root.withdraw()  # Hide the main window
#     file_path = filedialog.askopenfilename(filetypes=[("YAML Files", "*.yaml .yml"), ("All files", "*.*")])
#     if file_path:
#         print("Selected file:", file_path)
#         # Perform actions with the selected file path here

# def use_file():
#     with open(choose_file.file_path) as pp:
#         data = yaml.SafeLoader(pp)
#         print(data)

def handle_click(x, y):
    global receive_data, menu_state, active_entry, entry_box_x

    if HALT_BUTTON_X - HALT_BUTTON_RADIUS <= x <= HALT_BUTTON_X + HALT_BUTTON_RADIUS and \
            HALT_BUTTON_Y - HALT_BUTTON_RADIUS <= y <= HALT_BUTTON_Y + HALT_BUTTON_RADIUS:
        print("Clicked on HALT button")
        receive_data = False  # Stop receiving data
        ser.write("HALT".encode())

    elif 50 <= x <= 250:
        if 50 <= y <= 120:  # Check if clicked on "Limits" button
            menu_state = "home"
            active_entry = (0, 0)  # Set the first entry box as active
            print("Clicked on General")
        elif 150 <= y <= 220:  # Check if clicked on "General" button within the "Limits" menu
            menu_state = "limits"
            print("Clicked on Limits")
        elif 250 <= y <= 320:  # Check if clicked on "Graphs" button
            menu_state = "Graph"
            print("Clicked on Graph")
        elif 350 <= y <= 420:  # Check if clicked on "Data Collection" button
            menu_state = "data_collection"
            print("Clicked on Data Collection")
        elif 450 <= y <= 520:  # Check if clicked on "Custom Setup" button
            menu_state = "Custom Setup"
            print("Clicked on Custom Setup")
        elif 600 <= y <= 670 and menu_state == "limits":
            print("Clicked on Send Data")
            send_data_to_arduino()

    button_x = 1170
    button_y = 125
    if button_x <= x <= button_x + entry_width and button_y <= y <= button_y + entry_height:
        print("Clicked on Set Throttle button")
        try:
            throttle_value = float(throttle_entry)
            send_throttle_to_arduino(throttle_value)  # Call the function to send the throttle value to Arduino
            # Perform any necessary actions with the throttle value
            print(f"Setting throttle to: {throttle_value}")
        except ValueError:
            print("Invalid throttle value. Please enter a valid float.")

    for i in range(2):
        for j in range(2):
            entry_x_min = entry_x[j]
            entry_x_max = entry_x[j] + entry_width
            entry_y_min = entry_y[i]
            entry_y_max = entry_y[i] + entry_height
            if entry_x_min <= x <= entry_x_max and entry_y_min <= y <= entry_y_max:
                active_entry = (i, j)
                print("Clicked on entry box:", active_entry)

    # Handle clicks on buttons in the "Custom Setup" menu
    if menu_state == "Custom Setup":
        if 400 <= x <= 600 and 300 <= y <= 350:  # Check if clicked on "Browse" button
            print("Clicked on Browse Button")
            choose_file()
        elif 400 <= x <= 600 and 370 <= y <= 420:  # Check if clicked on "Use" button
            print("Clicked on Use Button")
            use_file()
            # Add functionality for the "Use" button here


def plot_dynamic_graph(pick):
    global graph_open
    # if graph_open:
        # plt.close()  # Close the previous plot if it's open
    
    x = np.linspace(0, 10, 100)
    y = np.sin(x + pick)
    plt.plot(x, y)
    plt.xlabel('Time')
    plt.ylabel('Amplitude')
    plt.title('Dynamic Plot')
    plt.grid(True)
    plt.show()
    graph_open = True

def draw_graph_buttons():
    button_width = 150
    button_height = 50
    button_x = 400
    button_y = 200

    # Draw five buttons
    pygame.draw.rect(screen, BOX_COLOR, (button_x, button_y, button_width, button_height), 2)
    draw_text("Button 1", font, TEXT_COL, button_x + 10, button_y + 10)

    pygame.draw.rect(screen, BOX_COLOR, (button_x + 200, button_y, button_width, button_height), 2)
    draw_text("Button 2", font, TEXT_COL, button_x + 210, button_y + 10)

    pygame.draw.rect(screen, BOX_COLOR, (button_x + 400, button_y, button_width, button_height), 2)
    draw_text("Button 3", font, TEXT_COL, button_x + 410, button_y + 10)

    pygame.draw.rect(screen, BOX_COLOR, (button_x, button_y + 100, button_width, button_height), 2)
    draw_text("Button 4", font, TEXT_COL, button_x + 10, button_y + 110)

    pygame.draw.rect(screen, BOX_COLOR, (button_x + 200, button_y + 100, button_width, button_height), 2)
    draw_text("Button 5", font, TEXT_COL, button_x + 210, button_y + 110)



def handle_graph_button_click(x, y):
    global pick
    button_width = 150
    button_height = 50
    button_x = 400
    button_y = 200

    if button_x <= x <= button_x + button_width and button_y <= y <= button_y + button_height:
        print("Clicked on Button 1")
        pick = 0  # Set data to "Voltage" when Button 1 is clicked
        plot_dynamic_graph(pick)

    elif button_x + 200 <= x <= button_x + 200 + button_width and button_y <= y <= button_y + button_height:
        print("Clicked on Button 2")
        pick = 1  # Set data to "Current" when Button 2 is clicked
        plot_dynamic_graph(pick)

    elif button_x + 400 <= x <= button_x + 400 + button_width and button_y <= y <= button_y + button_height:
        print("Clicked on Button 3")
        pick = 2  # Set data to "Torque1" when Button 3 is clicked
        plot_dynamic_graph(pick)

    elif button_x <= x <= button_x + button_width and button_y + 100 <= y <= button_y + 100 + button_height:
        print("Clicked on Button 4")
        pick = 3  # Set data to "Torque2" when Button 4 is clicked
        plot_dynamic_graph(pick)

    elif button_x + 200 <= x <= button_x + 200 + button_width and button_y + 100 <= y <= button_y + 100 + button_height:
        print("Clicked on Button 5")
        pick = 4  # Set data to "Thrust" when Button 5 is clicked
        plot_dynamic_graph(pick)

def handle_entry_event(event):
    global active_entry
    if event.type == pygame.KEYDOWN:
        i, j = active_entry
 
        # Ensure that the active entry indices are within the valid range
        if i >= len(entry_y):
            active_entry = (len(entry_y) - 1, j)
        elif j >= len(entry_x):
            active_entry = (i, len(entry_x) - 1)

        if 0 <= i < len(entry_text) and 0 <= j < len(entry_text[i]):
            if event.key == pygame.K_BACKSPACE:
                entry_text[i][j] = entry_text[i][j][:-1]  # Remove the last character
            elif event.key == pygame.K_RETURN:
                try:
                    float_value = float(entry_text[i][j])  # Convert the entered text to float
                    print(f"Value entered in entry box [{i}][{j}]: {float_value}")
                except ValueError:
                    print("Invalid input. Please enter a valid float value.")
                    entry_text[i][j] = ""  # Clear the entry box if not a valid float
            else:
                entry_text[i][j] += event.unicode  # Add typed character to entry text
                print(f"Current entry box [{i}][{j}]: {entry_text[i][j]}")
            # Update the active entry to the entry currently receiving keyboard input
            active_entry = (i, j)

def save_data_to_csv(data):
    try:
        with open(csv_file_path, mode="a", newline='') as file:
            writer = csv.writer(file)
            # Check if the file is empty and write the header if needed
            if file.tell() == 0:
                writer.writerow(csv_header)
            writer.writerow(data)
            print("Data saved to CSV file.")
    except Exception as e:
        print(f"Error saving data to CSV file: {e}")


run = True
while run:
    read_serial_data()
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                x, y = event.pos
                handle_click(x, y)
        if event.type == pygame.KEYDOWN:
            if menu_state == "home":
                handle_general_menu_event(event)  # Call this function for the "General" menu
            elif menu_state == "limits":
                handle_entry_event(event)
            
                

        elif event.type == pygame.QUIT:
            run = False
    # ...

    # Separate drawing loop for improved responsiveness
    screen.fill((52, 78, 91))
    draw_halt_button()

    # Draw functions
    if menu_state == "home":
        draw_general_data()  # Call the function to draw general data
        draw_set_throttle_button()
        draw_throttle_entry()
    elif menu_state == "limits":
        draw_limits_entry_boxes()
    elif menu_state == "data_collection":
        draw_data_collection()
    elif menu_state == "Graph":
        draw_graph_buttons()
        handle_graph_button_click(x, y)



        
        
    elif menu_state == "Custom Setup":
        draw_custom_setup()
        handle_custom_setup()
    # Add this part to print the received data for debugging purposes
    # print("Data values:", data_values)

    draw_menu()
    if data_collection_active:
        data_to_save = [data_values[key] for key in csv_header]
        save_data_to_csv(data_to_save)

    pygame.display.update()

pygame.quit()
