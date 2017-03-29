import sys
from cx_Freeze import setup, Executable

setup(
    name = "MatchPro",
    version = "1.01",
    description = "ANPR Matching Software",
    executables = [Executable("test.py", base = "Win32GUI")])