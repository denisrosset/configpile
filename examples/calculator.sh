#!/bin/sh

echo
echo This works
echo ----------
echo 

DIGITS=2 python calculator6.py --config calculator.ini  1 2

echo
echo This displays all the errors
echo ----------------------------
echo 

DIGITS=-2 python calculator6.py 2 3 4 5 oij oqww --operation test

echo
echo Errors in INI files as well
echo ---------------------------
echo 
python calculator6.py --config calculator_invalid.ini 2 3 4 5 