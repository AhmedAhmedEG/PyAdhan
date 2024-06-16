# Description

<p align="center">
<img src="https://github.com/AhmedAhmedEG/PyAdhan/assets/16827679/662ba3fb-d53f-4560-af08-cff943d55a14">
</p>

A desktop app for prayer calling, fully written in Python, featuring a modern interface and accurate prayer time measurments using IP geolocation and Prayer Times API.

If you love the project, any support from you will help to keep the project alive, you can support me on Paypal from here: https://paypal.me/AhmedAhmedEG?country.x=EG&locale.x=en_US

# Features
- Supports automatic detection for the correct prayer timings based on user location.
- Has a tray icon to handle showing, hiding and closing of the app.
- Caches a full month of prayers times locally to work offline.
- Has a collection of famous adhan callers pre-included.
- Can be added to the startup with a single click.
- Supports adding extra adhan callers.
- Provides toast notifications.


# How To Add Adhan Sounds
Just place the .mp3 file of the adhan in the "Resources/Adhan Callers" folder.

# How To Build From Code
1- Make a python virtual environment inside the project's folder with the name "venv" and run this command in it's shell: ```pip install pyside6 requests pywin32 public-ip cx_Freeze```.

> **_NOTE:_** creating a virual environment is very important here becuase in the building process, all the packages in the python enviroment get packed inside the output folder, we can add exception per package and also write code to delete spacific files for us, but we need the minimum amount of packages in the environment.

2- Open the cmd and set the project's folder as your current working directory, then run Build.bat and it will handle the building and the size optimizing processes automatically.

> **_NOTE:_** The "Build.bat" file runs the "Builder.py" file in the virtual enviroment, "Builder.py" uses cx_Freeze package to build the application, it also exceludes unused base python libraries, and it also includes custom code that removes unused parts of pyside6 library that takes alot of extra space.
