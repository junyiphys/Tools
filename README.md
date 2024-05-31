## Useful tips

### Example
pyinstaller --upx-dir "C:\Downloads\upx-4.2.4-win64" -F "AS_GUI_Ranalysis\main.py" --add-data "lemon.gif;." -i "lemon.ico" -w --clean

### Compress Method
pyinstaller --upx-dir "C:\Downloads\upx-4.2.4-win64" -F "AS_GUI_Ranalysis\main.py"  --upx-exclude=python3.dll --clean
