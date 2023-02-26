# Description

<p align="center">
<img src="https://user-images.githubusercontent.com/16827679/219981995-b676bb95-2d4b-4a25-9999-f09f3dc2dbf1.png">
</p>


A GUI-based desktop app for prayer calling, made with python using pyside6 package, it uses Prayer Times API which supports all the prayer calculation methods, with many famous adhan sounds pre-included, and it supports adding even more sounds to it easily.

# Features
- Supports all the prayer times calculation methods available in Prayer Times API.
- Has a tray icon to handle showing, hiding and closing of the app.
- Caches a full month of prayers times locally to work offline.
- Has a collection of famous adhan sounds pre-included.
- Supports adding variable number of adhan sounds.
- Very simple to use.


# How To Add Adhan Sounds
Just place the .mp3 file of the adhan in the "Resources/Adhan Sounds" folder.

# How To Build From Code
1- Make a python virtual environment inside the project's folder with the name "venv" and run this command in it's shell: ```pip install pyside6 requests pywin32 playsound==1.2.2```.

> **_NOTE:_** creating a virual environment is very important here becuase in the building process, all the packages in the python enviroment get packed inside the output folder, we can add exception per package and also write code to delete spacific files for us, but we need the minimum amount of packages in the environment.

> **_NOTE:_** The command I included forces a specific version of playsound to be installed, this is because the latest version of playsound as of now, v1.3.0, is bugged, but v1.2.2 is still working perfectly, so is essential to install that specific version.

2- Open the cmd and make the project's folder is your current working directory, then run Build.bat and it will handle the building and the size optimizing processes automatically.

> **_NOTE:_** The "Build.bat" file runs the "Builder.py" file in the virtual enviroment, "Builder.py" uses cx_Freeze package to build the application, it also exceludes unused base python libraries, and it also includes custom code that removes unused parts of pyside6 library that takes alot of extra space.
