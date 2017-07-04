import os
import sys
import subprocess

python_path = 'C:\\python36\\python.exe'

def install_req(venv_bin, fullpath):
    print("Install requirements.txt")
    output, error = subprocess.Popen(
        [
            os.path.join(venv_bin, 'pip'),
            'install',
            '-r',
            os.path.join(fullpath, 'requirements.txt')
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).communicate()
    if error:
        with open('pip_error.log', 'w') as fd:
            fd.write(error.decode('utf-8'))
            sys.exit(2)

def init_venv():
    
    bin_path = 'Scripts' if sys.platform == 'win32' else 'bin'

    fullpath = os.getcwd()
    _, project_name = os.path.split(fullpath)
    venv_path = os.path.join(os.environ['USERPROFILE'], '.virtualenvs', project_name)
    print("venv_path ", venv_path)
    
    output, error = subprocess.Popen(
        [python_path, "-m", "venv", venv_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).communicate()
    
    if error:
        with open('virtualenv_error.log', 'w') as fd:
            fd.write(error.decode('utf-8'))
            print("An error occurred with virtualenv")
            sys.exit(2)
    

    venv_bin = os.path.join(venv_path, bin_path)

    print(os.path.join(venv_bin, "activate.bat"))
    if sys.platform == "win32":
        output, error = subprocess.Popen(
            ["cmd", "/c", "mklink", "activate_venv.bat", os.path.join(venv_bin, "activate.bat")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
    
    if error:
        print('Couldn\'t create symbolic link')

    install_req(venv_bin, fullpath)


if __name__ == "__main__":
    print("Start process")
    init_venv()