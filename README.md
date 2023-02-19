# Features
- Supports all the prayer times calculation methods available in Prayer Times API.
- Has a tray icon to handle showing, hiding and closing of the app.
- Caches a full month of prayers times locally to work offline.
- Has a collection of famous adhan sounds pre-included.
- Supports adding variable number of adhan sounds.
- Very simple to use.


# How To Add Adhan Sounds
Just place the .mp3 file of the adhan in the "Resources/Adhan Sounds" folder.

# How To Build
1- Make a python virual environment inside the project's folder with the name "venv" and run this command in it's shell: ```pip install pyside6 requests playsound```, 
creating a virual environment is very important here becuase in the building process, all the packages in the python enviroment get packed inside the output folder, we can add exception per package and also write code to delete spacific files for us, but we need the minimum amount of packages in the environment.

2- Open the cmd and make the project's folder is your current working directory, then run Build.bat and it will handle the building and the cleaning of unused python base libraries and parts of pyside6 package automatically.
