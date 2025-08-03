This is a collection of the tools that I made to easy my life. Too many good things I want to do but only with limited time. Therefore, it is important to sharpen the tool usage. Althogh I know AI becomes easier, so that means I can generate more tools than what I expected. Actually I don't know if there's any building the same wheel as others, but I believe some of the useful small tools should benifit others at some level.

## Useful tips

### Example
pyinstaller --upx-dir "C:\Downloads\upx-4.2.4-win64" -F "AS_GUI_Ranalysis\main.py" --add-data "lemon.gif;." -i "lemon.ico" -w --clean

### Compress Method
pyinstaller --upx-dir "C:\Downloads\upx-4.2.4-win64" -F "AS_GUI_Ranalysis\main.py"  --upx-exclude=python3.dll --clean
