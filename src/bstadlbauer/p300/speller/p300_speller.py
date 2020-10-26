"""Script that starts a P300 Speller. Run with 'python p300_speller' to show config window.

Default configuration loaded at startup is stored in /config_files/default.cfg. Creates an LSL stream of type
'P300_Marker' with one channel of 'int8' sending a marker every time an image flashes.

The script consists of three main classes.
ConfigParams: Stores all config parameters that are set in the configuration GUI
MainWindow: The main configuration window, launched at startup
P300Window: All logic concerning the Image flashing window. E.g. the flash-sequence is generated here.
"""

import configparser
import glob
import os
from collections import deque
from tkinter import (
    EW,
    IntVar,
    Radiobutton,
    StringVar,
    Text,
    Tk,
    Toplevel,
    W,
    filedialog,
)
from tkinter.ttk import Button, Entry, Frame, Label

import numpy as np
from PIL import Image, ImageTk
from pylsl import IRREGULAR_RATE, StreamInfo, StreamOutlet, local_clock

MAX_FLASHES = 10000  # Maximum number of flashed images. Window will stop afterwards


class ConfigParams(object):
    """Stores all parameters that can be set in the MainWindow. Acts as model in MVC pattern."""

    def __init__(self):
        self.config_parser = configparser.RawConfigParser()

        # GUI Parameters
        self.imagesize = IntVar()
        self.config_file_path = StringVar()
        self.images_folder_path = StringVar()
        self.flash_image_path = StringVar()
        self.number_of_rows = IntVar()
        self.number_of_columns = IntVar()
        self.lsl_streamname = StringVar()
        self.flash_mode = IntVar()
        self.flash_duration = IntVar()
        self.break_duration = IntVar()

        # Default values
        self.config_file_path.set(os.path.join(os.path.dirname(__file__), "conf_files/default.cfg"))

        try:
            self.read_from_file()
        except configparser.NoSectionError:
            print("Config file {} not found".format(self.config_file_path.get()))

    def save_to_file(self):
        """Saves the current configuration to self.config_file_path"""
        try:
            self.config_parser.add_section("Parameters")
        except configparser.DuplicateSectionError:
            pass
        self.config_parser.set("Parameters", "Break Duration", self.break_duration.get())
        self.config_parser.set("Parameters", "Flash Duration", self.flash_duration.get())
        self.config_parser.set("Parameters", "Imagesize", self.imagesize.get())
        self.config_parser.set("Parameters", "Flash Mode", self.flash_mode.get())
        self.config_parser.set("Parameters", "LSL streamname", self.lsl_streamname.get())
        self.config_parser.set("Parameters", "Number of Rows", self.number_of_rows.get())
        self.config_parser.set("Parameters", "Number of Columns", self.number_of_columns.get())
        self.config_parser.set("Parameters", "Flash image path", self.flash_image_path.get())
        self.config_parser.set("Parameters", "Images Folder Path", self.images_folder_path.get())

        # Writing our configuration file to 'example.cfg'
        with open(self.config_file_path.get(), "w") as configfile:
            self.config_parser.write(configfile)

    def read_from_file(self):
        """Loads all configuration parameters from self.config_file_path"""
        self.config_parser.read(self.config_file_path.get())

        images_folder_fallback = os.path.join(os.path.dirname(__file__), "number_images")
        flash_image_fallback = os.path.join(os.path.dirname(__file__), "flash_images", "einstein.jpg")

        self.imagesize.set(self.config_parser.getint("Parameters", "Imagesize"))
        self.images_folder_path.set(
            self.config_parser.get("Parameters", "Images Folder Path", fallback=images_folder_fallback)
        )
        self.flash_image_path.set(
            self.config_parser.get("Parameters", "Flash image path", fallback=flash_image_fallback)
        )
        self.number_of_rows.set(self.config_parser.getint("Parameters", "Number of Rows"))
        self.number_of_columns.set(self.config_parser.getint("Parameters", "Number of Columns"))
        self.lsl_streamname.set(self.config_parser.get("Parameters", "LSL Streamname"))
        self.flash_mode.set(self.config_parser.getint("Parameters", "Flash Mode"))
        self.flash_duration.set(self.config_parser.getint("Parameters", "Flash duration"))
        self.break_duration.set(self.config_parser.getint("Parameters", "Break duration"))


class MainWindow(object):
    """Handles all the configuration and starts flashing window

    Args:
        master: Tkinter root window

    """

    def __init__(self, master: Tk):
        self.master = master
        master.title("P300 speller configuration")

        self.p300_window = None

        # Variables
        self.usable_images = []
        self.image_labels = []
        self.flash_sequence = []
        self.flash_image = None
        self.sequence_number = 0
        self.lsl_output = None

        self.config = ConfigParams()

        # Widget definition
        self.changeable_widgets = []

        self.config_file_label = Label(self.master, text="Config File:")
        self.config_file_label.grid(row=0, column=0)

        self.config_file_entry = Entry(self.master, textvariable=self.config.config_file_path)
        self.config_file_entry.grid(row=0, column=1, sticky=EW)
        self.changeable_widgets.append(self.config_file_entry)

        self.open_conf_btn = Button(
            self.master,
            text="Open config file",
            command=lambda: self.open_file_update_entry(self.config.config_file_path),
        )
        self.open_conf_btn.grid(row=0, column=2, sticky=EW)
        self.changeable_widgets.append(self.open_conf_btn)

        self.use_conf_btn = Button(self.master, text="Apply", command=self.config.read_from_file)
        self.use_conf_btn.grid(row=0, column=3)
        self.changeable_widgets.append(self.use_conf_btn)

        self.save_settings_btn = Button(self.master, text="Save", command=self.config.save_to_file)
        self.save_settings_btn.grid(row=0, column=4)
        self.changeable_widgets.append(self.save_settings_btn)

        self.images_folder_label = Label(self.master, text="Images folder:")
        self.images_folder_label.grid(row=1, column=0)

        self.images_folder_entry = Entry(self.master, textvariable=self.config.images_folder_path)
        self.images_folder_entry.grid(row=1, column=1, sticky=EW)
        self.changeable_widgets.append(self.images_folder_entry)

        self.open_images_dir_btn = Button(
            self.master,
            text="Open image folder",
            command=lambda: self.open_folder_update_entry(self.config.images_folder_path),
        )
        self.open_images_dir_btn.grid(row=1, column=2, sticky=EW)
        self.changeable_widgets.append(self.open_images_dir_btn)

        self.flash_image_label = Label(self.master, text="Flash image:")
        self.flash_image_label.grid(row=2, column=0)

        self.flash_image_file_entry = Entry(self.master, textvariable=self.config.flash_image_path)
        self.flash_image_file_entry.grid(row=2, column=1, sticky=EW)
        self.changeable_widgets.append(self.flash_image_file_entry)

        self.open_flash_dir_btn = Button(
            self.master, text="Open image", command=lambda: self.open_file_update_entry(self.config.flash_image_path)
        )
        self.open_flash_dir_btn.grid(row=2, column=2, sticky=EW)
        self.changeable_widgets.append(self.open_flash_dir_btn)

        self.imagesize_label = Label(self.master, text="Imagesize (px):")
        self.imagesize_label.grid(row=3, column=0)

        self.imagesize_entry = Entry(self.master, textvariable=self.config.imagesize)
        self.imagesize_entry.grid(row=3, column=1, sticky=W)
        self.changeable_widgets.append(self.imagesize_entry)

        self.number_of_rows_label = Label(self.master, text="Number of rows:")
        self.number_of_rows_label.grid(row=4, column=0)

        self.number_of_rows_entry = Entry(self.master, textvariable=self.config.number_of_rows)
        self.number_of_rows_entry.grid(row=4, column=1, sticky=W)
        self.changeable_widgets.append(self.number_of_rows_entry)

        self.number_of_columns_label = Label(self.master, text="Number of columns:")
        self.number_of_columns_label.grid(row=5, column=0)

        self.number_of_columns_entry = Entry(self.master, textvariable=self.config.number_of_columns)
        self.number_of_columns_entry.grid(row=5, column=1, sticky=W)
        self.changeable_widgets.append(self.number_of_columns_entry)

        self.lsl_streamname_label = Label(self.master, text="LSL Streamname:")
        self.lsl_streamname_label.grid(row=6, column=0)

        self.lsl_streamname_entry = Entry(self.master, textvariable=self.config.lsl_streamname)
        self.lsl_streamname_entry.grid(row=6, column=1, sticky=W)
        self.changeable_widgets.append(self.lsl_streamname_entry)

        self.flash_duration_label = Label(self.master, text="Flash duration (ms):")
        self.flash_duration_label.grid(row=7, column=0)

        self.flash_duration_entry = Entry(self.master, textvariable=self.config.flash_duration)
        self.flash_duration_entry.grid(row=7, column=1, sticky=W)
        self.changeable_widgets.append(self.flash_duration_entry)

        self.break_duration_label = Label(self.master, text="Break duration (ms):")
        self.break_duration_label.grid(row=8, column=0)

        self.break_duration_entry = Entry(self.master, textvariable=self.config.break_duration)
        self.break_duration_entry.grid(row=8, column=1, sticky=W)
        self.changeable_widgets.append(self.break_duration_entry)

        self.flash_mode_label = Label(self.master, text="Flashmode:")
        self.flash_mode_label.grid(row=9, column=0)

        self.flash_mode_1_rb = Radiobutton(
            self.master,
            text="Rows and Columns (Sequence not pseudorandom yet!)",
            variable=self.config.flash_mode,
            value=1,
        )
        self.flash_mode_1_rb.grid(row=9, column=1, sticky=W)
        self.changeable_widgets.append(self.flash_mode_1_rb)

        self.flash_mode_2_rb = Radiobutton(self.master, text="Single images", variable=self.config.flash_mode, value=2)
        self.flash_mode_2_rb.grid(row=10, column=1, sticky=W)
        self.changeable_widgets.append(self.flash_mode_2_rb)
        self.set_flash_mode_rbs()

        self.text_console = Text(self.master)
        self.text_console.grid(row=11, column=0, rowspan=4, columnspan=5)
        self.text_console.configure(state="disabled")

        self.close_button = Button(self.master, text="Close", command=master.quit)
        self.close_button.grid(row=15, column=0)

        self.open_button = Button(self.master, text="Open", command=self.open_p300_window)
        self.open_button.grid(row=15, column=3)
        self.changeable_widgets.append(self.open_button)

    def set_flash_mode_rbs(self):
        if self.config.flash_mode.get() == 1:
            self.flash_mode_1_rb.select()
        else:
            self.flash_mode_2_rb.select()

    def open_folder_update_entry(self, entry_var):
        new_path = filedialog.askdirectory()
        if new_path != "":
            entry_var.set(new_path)

    def open_file_update_entry(self, entry_var):
        new_path = filedialog.askopenfilename()
        if new_path != "":
            entry_var.set(new_path)

    def print_to_console(self, text_to_print):
        if not isinstance(text_to_print, str):
            text_to_print = str(text_to_print)

        self.text_console.configure(state="normal")
        self.text_console.insert("end", text_to_print + "\n")
        self.text_console.configure(state="disabled")

    def disable_all_widgets(self):
        for widget in self.changeable_widgets:
            widget.configure(state="disabled")
        self.master.iconify()

    def enable_all_widgets(self):
        for widget in self.changeable_widgets:
            widget.configure(state="normal")
        self.master.deiconify()

    def open_p300_window(self):
        p300_window_master = Toplevel(self.master)
        self.p300_window = P300Window(p300_window_master, self, self.config)
        self.disable_all_widgets()


class P300Window(object):
    """All logic for the image flashing window.

    Args:
        master: Tkinter Toplevel element
        parent: Parent that opened the window
        config: ConfigParams instance

    """

    def __init__(self, master: Toplevel, parent: MainWindow, config: ConfigParams):
        self.master = master
        self.parent = parent

        self.master.protocol("WM_DELETE_WINDOW", self.close_window)

        self.config = config
        self.running = 0

        self.image_labels = []
        self.sequence_number = 0
        self.lsl_output = None
        self.usable_images = []
        self.flash_sequence = []

        self.image_frame = Frame(self.master)
        self.image_frame.grid(
            row=0, column=0, rowspan=self.config.number_of_rows.get(), columnspan=self.config.number_of_columns.get()
        )

        self.start_btn_text = StringVar()
        self.start_btn_text.set("Start")
        self.start_btn = Button(self.master, textvariable=self.start_btn_text, command=self.start)
        self.start_btn.grid(row=self.config.number_of_rows.get() + 1, column=self.config.number_of_columns.get() - 1)

        self.pause_btn = Button(self.master, text="Pause", command=self.pause)
        self.pause_btn.grid(row=self.config.number_of_rows.get() + 1, column=self.config.number_of_columns.get() - 2)
        self.pause_btn.configure(state="disabled")

        self.close_btn = Button(self.master, text="Close", command=self.close_window)
        self.close_btn.grid(row=self.config.number_of_rows.get() + 1, column=0)

        # Initialization
        self.show_images()
        self.create_flash_sequence()
        self.lsl_output = self.create_lsl_output()

    def open_images(self):
        self.usable_images = []
        image_paths = glob.glob(os.path.join(self.config.images_folder_path.get(), "*.jpg"))
        png_images = glob.glob(os.path.join(self.config.images_folder_path.get(), "*.png"))
        for png_image in png_images:
            image_paths.append(png_image)
        min_number_of_images = self.config.number_of_columns.get() * self.config.number_of_rows.get()
        if len(image_paths) < min_number_of_images:
            self.parent.print_to_console("To few images in folder: " + self.config.images_folder_path.get())
            return

        # Convert and resize images
        for image_path in image_paths:
            image = Image.open(image_path)
            resized = image.resize((self.config.imagesize.get(), self.config.imagesize.get()), Image.ANTIALIAS)
            Tkimage = ImageTk.PhotoImage(resized)
            self.usable_images.append(Tkimage)

        flash_img = Image.open(self.config.flash_image_path.get())
        flash_img_res = flash_img.resize((self.config.imagesize.get(), self.config.imagesize.get()), Image.ANTIALIAS)
        self.flash_image = ImageTk.PhotoImage(flash_img_res)

    def show_images(self):
        self.open_images()

        if self.usable_images == []:
            self.parent.print_to_console("No images opened")
            return

        num_rows = self.config.number_of_rows.get()
        num_cols = self.config.number_of_columns.get()

        # Arrange images
        for r in range(0, num_rows):
            for c in range(0, num_cols):
                current_image = self.usable_images[r * num_cols + c]
                label = Label(self.image_frame, image=current_image)
                label.image = current_image
                label.grid(row=r, column=c)
                self.image_labels.append(label)

    def create_lsl_output(self):
        """Creates an LSL Stream outlet"""
        info = StreamInfo(
            name=self.config.lsl_streamname.get(),
            type="P300_Marker",
            channel_count=1,
            channel_format="int8",
            nominal_srate=IRREGULAR_RATE,
            source_id="marker_stream",
            handle=None,
        )

        if self.config.flash_mode == 1:
            info.desc().append_child_value("flash_mode", "Row and Column")
        elif self.config.flash_mode == 2:
            info.desc().append_child_value("flash_mode", "Single Value")

        info.desc().append_child_value("num_rows", str(self.config.number_of_rows.get()))
        info.desc().append_child_value("num_cols", str(self.config.number_of_columns.get()))

        return StreamOutlet(info)

    def create_flash_sequence(self):
        self.flash_sequence = []
        num_rows = self.config.number_of_rows.get()
        num_cols = self.config.number_of_columns.get()

        sequence_length = 700  # ms
        distance_between_similar_elements = int((sequence_length / self.config.break_duration.get()) + 1)

        if self.config.flash_mode.get() == 1:
            self.parent.print_to_console("CAUTION: Row and Column flash mode currently uses only random samples!")
            self.flash_sequence = np.random.randint(0, num_rows + num_cols, 3000)
        elif self.config.flash_mode.get() == 2:
            flash_sequence = []
            maximum_number = num_rows * num_cols

            if maximum_number * 0.7 < distance_between_similar_elements:
                self.parent.print_to_console("No sequence could be created because the break duration is too short")
                return

            number_buffer = deque(maxlen=distance_between_similar_elements)

            for _ in range(0, MAX_FLASHES):
                while True:
                    new_number = np.random.randint(0, maximum_number, 1)
                    if bool(number_buffer.count(new_number[0])) is False:
                        number_buffer.append(new_number[0])
                        flash_sequence.append(new_number[0])
                        break
            self.flash_sequence = flash_sequence

    def start(self):
        self.running = 1
        self.start_flashing()
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")

    def pause(self):
        self.running = 0
        self.start_btn_text.set("Resume")
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")

    def start_flashing(self):
        if self.sequence_number == len(self.flash_sequence):
            self.parent.print_to_console("All elements flashed")
            self.running = 0
            self.sequence_number = 0
            return

        if self.running == 0:
            self.parent.print_to_console("Flashing paused at sequence number " + str(self.sequence_number))
            return

        element_to_flash = self.flash_sequence[self.sequence_number]
        self.sequence_number = self.sequence_number + 1

        timestamp = local_clock()
        print([element_to_flash + 1], timestamp)
        self.lsl_output.push_sample([element_to_flash + 1], timestamp)  # add 1 to prevent 0 in markers

        if self.config.flash_mode.get() == 1:
            self.flash_row_or_col(element_to_flash)
        elif self.config.flash_mode.get() == 2:
            self.flash_single_element(element_to_flash)

        self.master.after(self.config.break_duration.get(), self.start_flashing)

    def change_image(self, label, img):
        label.configure(image=img)
        label.image = img

    def flash_row_or_col(self, rc_number):
        num_rows = self.config.number_of_rows.get()
        num_cols = self.config.number_of_columns.get()

        if rc_number < num_rows:
            for c in range(0, num_cols):
                cur_idx = rc_number * num_cols + c
                self.change_image(self.image_labels[cur_idx], self.flash_image)
        else:
            current_column = rc_number - num_rows
            for r in range(0, num_rows):
                cur_idx = current_column + r * num_cols
                self.change_image(self.image_labels[cur_idx], self.flash_image)

        self.master.after(self.config.flash_duration.get(), self.unflash_row_or_col, rc_number)

    def unflash_row_or_col(self, rc_number):
        num_rows = self.config.number_of_rows.get()
        num_cols = self.config.number_of_columns.get()
        if rc_number < num_rows:
            for c in range(0, num_cols):
                cur_idx = rc_number * num_cols + c
                self.change_image(self.image_labels[cur_idx], self.usable_images[cur_idx])
        else:
            current_column = rc_number - num_rows
            for r in range(0, num_rows):
                cur_idx = current_column + r * num_cols
                self.change_image(self.image_labels[cur_idx], self.usable_images[cur_idx])

    def flash_single_element(self, element_no):
        self.change_image(self.image_labels[element_no], self.flash_image)
        self.master.after(self.config.flash_duration.get(), self.unflash_single_element, element_no)

    def unflash_single_element(self, element_no):
        self.change_image(self.image_labels[element_no], self.usable_images[element_no])

    def close_window(self):
        self.parent.enable_all_widgets()
        self.master.destroy()


def main():
    from tkinter import Tk

    root = Tk()
    MainWindow(root)
    root.mainloop()
