#!/bin/sh

echo
echo This works
echo ----------
echo 

DIGITS=2 python calculator.py --config calculator.ini  1 2

echo
echo This displays all the errors
echo ----------------------------
echo 

DIGITS=-2 python calculator.py 2 3 4 5 oij oqww --operation test

echo
echo Errors in INI files as well
echo ---------------------------
echo 
python calculator.py --config calculator_invalid.ini 2 3 4 5 