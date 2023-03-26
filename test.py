import os
from shutil import move
from tempfile import NamedTemporaryFile

# Take off the first line which has the system call and params
file_path = 'test.txt'
temp_path = None
with open(file_path, 'r') as f_in:
    first_line = f_in.readline()
    with NamedTemporaryFile(mode='w', delete=False) as f_out:
        temp_path = f_out.name
        #next(f_in)  # skip first line
        for line in f_in:
            f_out.write(line)
        f_out.write(first_line)


os.remove(file_path)
move(temp_path, file_path)





