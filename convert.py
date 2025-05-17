from PyQt5 import uic

# Specify the input .ui file and output .py file
ui_file = "mydesign2.ui"
output_file = "mydesign2.py"

# Compile the .ui file into a .py file
with open(output_file, "w") as py_file:
    uic.compileUi(ui_file, py_file)



