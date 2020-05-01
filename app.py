from tkinter import filedialog, messagebox
from tkinter import *
from PIL import ImageTk,Image
import os
from pyimagesearch.transform import four_point_transform
from skimage.filters import threshold_local
import numpy as np
import argparse
import cv2
import imutils
import glob
from sys import exit
from win10toast import ToastNotifier
import time
import webbrowser
import img2pdf


def popupMessage(status, duration=1.5, icon=None):
    if not icon:
        icon = resource_path('.') + '/resources/success.ico'
    toaster = ToastNotifier()
    toaster.show_toast("Image Scanner",
                        status,
                        icon_path=icon,
                        duration=duration,
                        threaded=True)

def loadImage(path):
    if path is None:
        return None
    _img = Image.open(path)
    _img = _img.resize((500,600), Image.ANTIALIAS)
    return _img

def browse_button():
    global folder_path
    global image_list
    global scanned_img_list
    global my_orig
    global my_scanned
    global button_forward
    global button_forward
    global button_back
    global control_frame
    global next_photo
    global back_photo
    global my_images

    new_folder = os.path.dirname(filedialog.askopenfilename(title="Select any file to open this directory"))
    folder_path.set(new_folder)
    # reinit all vars
    # rename jpeg to jpg
    jpeg_files = glob.glob(new_folder+ '/*.jpeg')
    for filename in jpeg_files:
        os.rename(filename, filename[:-4] + '.jpg')

    my_images = glob.glob(new_folder+ '/*.jpg')
    my_images += glob.glob(new_folder+ '/*.png')
    my_images.sort(key=os.path.getmtime, reverse=True)
    
    # filter out scanned images
    my_images = list(filter(lambda image: "_scanned" not in image, my_images))
    image_list.clear()
    for image in my_images:
        my_img = ImageTk.PhotoImage(loadImage(image))
        image_list.append(my_img)
    
    # initially scan one image
    scanned_img_list.clear()
    if (len(my_images) > 0):
        scanned_img1 = scan_image(my_images[0])
        scanned_img_list.append(scanned_img1)


    my_orig.grid_forget()
    my_scanned.grid_forget()
    
    if (len(my_images) > 0):
        my_orig = Label(image=image_list[0])
        my_orig.grid(row=0, column=0, columnspan=5)
    
        my_scanned = Label(image=scanned_img_list[0])
        my_scanned.grid(row=0, column=5, columnspan=5)


    button_forward.grid_forget()
    button_back.grid_forget()
    button_back = Button(control_frame, text="Back", state=DISABLED, image=back_photo, compound=RIGHT)
    if len(image_list) <= 1:
        button_forward = Button(control_frame, text="Next", state=DISABLED, image=next_photo, compound=LEFT)
    else:
        button_forward = Button(control_frame, text="Next", command=lambda: forward(2), image=next_photo, compound=LEFT)
    button_back.grid(row=1, column=1, sticky=W)
    button_forward.grid(row=1, column=2, sticky=W)

def forward(image_number):
    global my_orig
    global button_forward
    global button_back
    global image_list
    global scanned_img_list
    global my_scanned
    global my_images
    global back_photo
    global next_photo

    SIZE = len(image_list)
    current_image_name = my_images[image_number-1]
    my_orig.grid_forget()
    my_orig = Label(image=image_list[image_number-1])
    my_scanned.grid_forget()
    if not is_scanned_image(current_image_name):
        my_scanned_image = scan_image(current_image_name)
        scanned_img_list.append(my_scanned_image)
    my_scanned = Label(image=scanned_img_list[image_number-1])
    button_forward = Button(control_frame, text="Next", command=lambda: forward(image_number+1), image=next_photo, compound=LEFT)
    button_back = Button(control_frame, text="Back", command=lambda: back(image_number-1), image=back_photo, compound=RIGHT)

    if image_number == SIZE:
        button_forward = Button(control_frame, text="Next", state=DISABLED, image=next_photo, compound=RIGHT)

    my_orig.grid(row=0, column=0, columnspan=5)
    my_scanned.grid(row=0, column=5, columnspan=5)
    button_back.grid(row=1, column=1)
    button_forward.grid(row=1, column=2)
    return

def back(image_number):
    global my_orig
    global button_forward
    global button_back
    global image_list
    global scanned_img_list
    global my_scanned
    global my_images
    global control_frame

    current_image_name = my_images[image_number-1]

    my_orig.grid_forget()
    my_orig = Label(image=image_list[image_number-1])
    my_scanned.grid_forget()
    if not is_scanned_image(current_image_name):
        my_scanned_image = scan_image(current_image_name)
        scanned_img_list.append(my_scanned_image)
    my_scanned = Label(image=scanned_img_list[image_number-1])
    button_forward = Button(control_frame, text="Next", command=lambda: forward(image_number+1), image=next_photo, compound=LEFT)
    button_back = Button(control_frame, text="Back", command=lambda: back(image_number-1), image=back_photo, compound=RIGHT)

    if image_number <= 1:
        button_back = Button(control_frame, text="Back", state=DISABLED, image=back_photo, compound=RIGHT) 

    my_orig.grid(row=0, column=0, columnspan=5)
    my_scanned.grid(row=0, column=5, columnspan=5)
    button_back.grid(row=1, column=1)
    button_forward.grid(row=1, column=2)
    return

def scan_image(image_path, display_message=True):
    saved_image = image_path[:-4] + "_scanned.jpg"
    if not os.path.isfile(saved_image):
        image = cv2.imread(image_path, cv2.IMREAD_IGNORE_ORIENTATION | cv2.IMREAD_COLOR)
        ratio = image.shape[0] / 500.0
        orig = image.copy()
        image = imutils.resize(image, height = 500)
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5,5), 0)
        edged = cv2.Canny(gray, 75, 200)
        
        # print("STEP 1: Edge detection")
        
        # find the contours in the edged image, keeping only the
        # largest ones, and initialize the screen contour
        cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]
        # loop over the contours
        screenCnt = None
        for c in cnts:
        	# approximate the contour
        	peri = cv2.arcLength(c, True)
        	approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        	# if our approximated contour has four points, then we
        	# can assume that we have found our screen
        	if len(approx) == 4:
        		screenCnt = approx
        		break
        # show the contour (outline) of the piece of paper
        # print("STEP 2: Find contours of paper")
        # cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 2)
        
        # apply the four point transform to obtain a top-down
        # view of the original image
        if screenCnt is None:
            icon=resource_path('.')  + "/resources/warning.ico"
            popupMessage("Cannot scanned {}".format(saved_image), duration=3, icon=icon)
            return None
        warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)
        # convert the warped image to grayscale, then threshold it
        # to give it that 'black and white' paper effect
        warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        T = threshold_local(warped, 11, offset = 10, method = "gaussian")
        warped = (warped > T).astype("uint8") * 255
        # save to disk 
        cv2.imwrite(saved_image.replace(".png", ".jpg"), warped)
        if display_message:
            popupMessage("Scanned successfully {}".format(saved_image))
    image = ImageTk.PhotoImage(loadImage(saved_image))
    return image

def is_scanned_image(image_name):
    if "_scanned" in image_name:
        return True 
    return False

def scan_all_images(image_list):
    for image in image_list:
        scan_image(image, False)
    popupMessage("Scanned all images", duration=2)

def open_folder_button(path):
    webbrowser.open('file:///' + path)

def generate_pdf(path):
    global check_scanned
    my_pdf_name = path + "\\my_pdf_submission.pdf"
    icon_warning = resource_path('.') + "/resources/warning.ico"
    try:
        with open(my_pdf_name, "wb") as f:
            my_images = glob.glob(path+'/*.jpg')
            my_images.sort(reverse=False)
            if check_scanned.get():
                my_images = list(filter(lambda image: "_scanned" in image, my_images))
            else:
                my_images = list(filter(lambda image: "_scanned" not in image, my_images))
            if len(my_images) > 0:
                f.write(img2pdf.convert(my_images))
                popupMessage("Generated {}".format(my_pdf_name), duration=2)
            else:
                popupMessage("Could not found any *_scanned.jpg to generate", duration=2, icon=icon_warning)
            f.close()
    except: 
        popupMessage("Could not write a new pdf file, please close previous version, or check permission", duration=3, icon=icon_warning)

def show_info():
    my_text = "Copyright (c) 2020 Thien Pham"
    my_text += "\n<thien.pham@adelaide.edu.au>"
    my_text += "\n MIT LICENSE"
    my_text += "\nLibs: tkinter, numpy, opencv4, win10toast, img2pdf"
    my_text += "\nScan function: from PyImageSearch @ pyimagesearch.com"
    my_text += "\nBrowse: choose a folder containing images"
    my_text += "\nBack,Next: navigate through each image to scan it"
    my_text += "\nScan All: convert all images to scanned images"
    my_text += "\nOpen Folder: open the folder containing scanned images + pdf"
    my_text += "\nGenerate PDF: create the single pdf file from scanned images" 
    my_text += '\nScanner icon made by smalllikeart at www.flaticon.com'

    messagebox.showinfo("Info", my_text)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

root = Tk()
root.title('Image AfterScanner')
print(resource_path("."))
root.iconbitmap(resource_path(".") + '/resources/icon.ico')

folder_path = StringVar()
folder_path.set(os.getcwd()+'\images')

current_foler = folder_path.get()

# rename jpeg to jpg
jpeg_files = glob.glob(current_foler + '/*.jpeg')
for filename in jpeg_files:
    os.rename(filename, filename[:-4] + 'jpg')

my_images = glob.glob(current_foler + '/*.jpg')
my_images += glob.glob(current_foler + '/*.png')

my_images.sort(key=os.path.getmtime, reverse=True)

# filter out scanned images
my_images = list(filter(lambda image: "_scanned" not in image, my_images))
image_list = []
for image in my_images:
    my_img = ImageTk.PhotoImage(loadImage(image))
    image_list.append(my_img)

# initially scan one image
scanned_img_list = []
if (len(my_images) > 0):
    scanned_img1 = scan_image(my_images[0])
    scanned_img_list.append(scanned_img1)

my_orig = Label(image=None)
my_scanned = Label(image=None)

if (len(my_images) > 0):
    my_orig = Label(image=image_list[0])
    my_orig.grid(row=0, column=0, columnspan=5, sticky="news")

    my_scanned = Label(image=scanned_img_list[0])
    my_scanned.grid(row=0, column=5, columnspan=5, sticky="news")


path_message= Message(root, textvariable=folder_path, width=450)
path_message.config(anchor='e')
path_message.grid(row=1, column=9, columnspan=1)

control_frame = Frame(root)

button_browse = Button(control_frame, text="Browse", command=browse_button)
button_browse.grid(row=1, column=0, sticky=W)

back_photo = ImageTk.PhotoImage(Image.open(resource_path('.') + "/resources/back.ico").resize((20,20), Image.ANTIALIAS))
next_photo = ImageTk.PhotoImage(Image.open(resource_path('.') + "/resources/forward.ico").resize((20,20), Image.ANTIALIAS))

button_back = Button(control_frame, text="Back", image=back_photo, compound=RIGHT, command=back, state=DISABLED)
if len(image_list) <= 1:
    button_forward = Button(control_frame, text="Next", image=next_photo, compound=LEFT, state=DISABLED)
else:
    button_forward = Button(control_frame, text="Next", image=next_photo, compound=LEFT, command=lambda: forward(2))
button_exit = Button(control_frame, text="Exit Program", command=root.quit)


button_back.grid(row=1, column=1, sticky=W)
button_forward.grid(row=1, column=2, sticky=W)
button_exit.grid(row=1, column=7, sticky=W)


button_scanall = Button(control_frame, text="Scan All", command=lambda: scan_all_images(my_images))
button_scanall.grid(row=1, column=3, sticky=W)

button_openfolder = Button(control_frame, text="Open Folder", command=lambda: open_folder_button(folder_path.get()))
button_openfolder.grid(row=1, column=4, sticky=W)

button_generate_pdf = Button(control_frame, text="Generate PDF", command=lambda: generate_pdf(folder_path.get()))
button_generate_pdf.grid(row=1, column=5, sticky=W)
check_scanned = IntVar()
check_scanned.set(1)
button_check_scanned = Checkbutton(control_frame, text="From scanned img", variable=check_scanned)
button_check_scanned.grid(row=1, column=6, sticky=W)

button_info = Button(control_frame, text="Help", command=show_info)
button_info.grid(row=1, column=8, sticky=W)

control_frame.grid(row=1, column=0, columnspan=9, sticky="nsew")

root.resizable(False,False)

root.mainloop()