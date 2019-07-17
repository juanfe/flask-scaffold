# -*- coding: utf-8 -*-

import sys
import os
import argparse
import jinja2
import codecs
import subprocess
import shutil
import platform

if sys.version_info < (3, 0):
    from shutilwhich import which
else:
    from shutil import which


# Globals #

cwd = os.getcwd()
script_dir = os.path.dirname(os.path.realpath(__file__))

# Jinja2 environment
template_loader = jinja2.FileSystemLoader(
    searchpath=os.path.join(script_dir, "templates"))
template_env = jinja2.Environment(loader=template_loader)


def get_arguments(argv):
    parser = argparse.ArgumentParser(description='Scaffold a Flask Skeleton.')
    parser.add_argument('appname', help='The application name')
    parser.add_argument('-s', '--skeleton', help='The skeleton folder to use.')
    parser.add_argument('-b', '--bower', help='Install dependencies via bower')
    parser.add_argument('-y', '--yarn', help='Install dependencies via bower')
    parser.add_argument('-v', '--virtualenv', action='store_true')
    parser.add_argument('-g', '--git', action='store_true')
    args = parser.parse_args()
    return args


def generate_brief(args):
    template_var = {
        'pyversion': platform.python_version(),
        'appname': args.appname,
        'bower': args.bower,
        'yarn': args.yarn,
        'virtualenv': args.virtualenv,
        'skeleton': args.skeleton,
        'path': os.path.join(cwd, args.appname),
        'git': args.git
    }
    template = template_env.get_template('brief.jinja2')
    return template.render(template_var)


def git_init(arg, fullpath, name=None, email=None):
    if arg:
        output = subprocess.Popen(
            ['git', 'init', fullpath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        error = output.communicate()[1]
        if error:
            with open('git_error.log', 'w') as fd:
                fd.write(error.decode('utf-8'))
                print("Error with git init")
                sys.exit(2)
        if name != '':
            output.wait()
            output2 = subprocess.Popen(
                ['git', 'config', '--local', 'user.name', name, fullpath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=fullpath
            )
            error2 = output2.communicate()[1]
        if email != '':
            if name != '':
                output2.wait()
            else:
                output.wait()
            output3 = subprocess.Popen(
                ['git', 'config', '--local', 'user.email', email, fullpath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=fullpath
            )
            error3 = output3.communicate()[1]
        if (name != '' and error2) or (email != '' and error3):
            with open('git_error.log', 'w') as fd:
                fd.write(error.decode('utf-8'))
                print("Error with git config")
                sys.exit(2)
        shutil.copyfile(
            os.path.join(script_dir, 'templates', '.gitignore'),
            os.path.join(fullpath, '.gitignore')
        )


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


def add_yarn_or_bower(args, fullpath):
    if args.yarn:
        print("Adding yarn dependencies...")
        yarn = args.yarn.split(',')
        yarn_exe = which('yarn')
        if yarn_exe:
            os.chdir(os.path.join(fullpath, 'project', 'client', 'static'))
            output, error = subprocess.Popen(
                [yarn_exe, 'init', '-y'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=fullpath
            ).communicate()
            if error:
                print("An error occurred at init Yarn, please check the "
                      "package.json file.")
                print(error.decode('ascii'))
            for dependency in yarn:
                output, error = subprocess.Popen(
                    [yarn_exe, 'add', dependency],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=fullpath
                ).communicate()
                if error:
                    print("An error occurred with Yarn")
                    print(error.decode('ascii'))
        else:
            print("Could not find yarn. Ignoring.")
    elif args.bower:
        print("Adding bower dependencies...")
        bower = args.bower.split(',')
        bower_exe = which('bower')
        if bower_exe:
            os.chdir(os.path.join(fullpath, 'project', 'client', 'static'))
            for dependency in bower:
                output, error = subprocess.Popen(
                    [bower_exe, 'install', dependency],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                ).communicate()
                if error:
                    print("An error occurred with Bower")
                    print(error)
        else:
            print("Could not find bower. Ignoring.")


def add_virtualenv(args, fullpath, appname):
    bin_path = 'bin'
    if sys.platform == 'win32':
        bin_path = 'Scripts'

    virtualenv = args.virtualenv
    if virtualenv:
        print("Adding a virtualenv...")
        virtualenv_exe = which('pyvenv')
        if virtualenv_exe:
            output, error = subprocess.Popen(
                [virtualenv_exe, os.path.join(fullpath, 'env')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate()
            if error:
                with open('virtualenv_error.log', 'w') as fd:
                    fd.write(error.decode('utf-8'))
                    print("An error occurred with virtualenv")
                    sys.exit(2)
            venv_bin = os.path.join(fullpath, 'env', bin_path)
            install_req(venv_bin, fullpath)
        elif which('venvs'):
            print("Could not find virtualenv executable. Try venv")
            _, l_appname = os.path.split(appname)
            try:
                venv_path = os.path.join(os.environ['USERPROFILE'],
                                         '.virtualenvs', l_appname)
            except KeyError:
                print(80*"*")
                print("Please define variable USERPROFILE.")
                print(80*"*")
                raise
            print("venv_path ", venv_path)
            output, error = subprocess.Popen(
                ["python.exe", "-m", "venv", venv_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate()
            if error:
                with open('virtualenv_error.log', 'w') as fd:
                    fd.write(error.decode('utf-8'))
                    print("An error occurred with virtualenv")
                    sys.exit(2)
            venv_bin = os.path.join(venv_path, bin_path)

            if sys.platform == "win32":
                output, error = subprocess.Popen(
                    ["cmd", "/c", "mklink", os.path.join(fullpath,
                                                         "activate_venv.bat"),
                     os.path.join(venv_bin, "activate.bat")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                ).communicate()

            if error:
                print('Couldn\'t create symbolic link')

            install_req(venv_bin, fullpath)
        else:
            print("Could not find virtualenv executable, Try with "
                  "virtualenvwrapper or other. Ignoring.")


def main(args):

    print("\nScaffolding...")

    # Variables #

    appname = args.appname
    fullpath = os.path.join(cwd, appname)
    skeleton_dir = args.skeleton

    # Tasks #

    # Copy files and folders
    print("Copying files and folders...")
    try:
        shutil.copytree(os.path.join(script_dir, skeleton_dir), fullpath)
    except FileExistsError:
        shutil.rmtree(fullpath)
        shutil.copytree(os.path.join(script_dir, skeleton_dir), fullpath)
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    # Create config.py
    print("Creating the config...")
    secret_key = codecs.encode(os.urandom(32), 'hex').decode('utf-8')
    template = template_env.get_template('config.jinja2')
    template_var = {
        'secret_key': secret_key,
    }
    with open(os.path.join(fullpath, 'project', 'config.py'), 'w') as fd:
        fd.write(template.render(template_var))

    # Add bower dependencies
    add_yarn_or_bower(args, fullpath)
    # Add a virtualenv
    add_virtualenv(args, fullpath, appname)
    # Git init
    git_init(args.git, fullpath, args.name, args.email)


if __name__ == '__main__':
    arguments = get_arguments(sys.argv)
    print(generate_brief(arguments))
    if sys.version_info < (3, 0):
        input = raw_input
    if arguments.git:
        arguments.name = input("\nGive me your full name: (Enter for None) ")
        arguments.email = input("\nGive me your email: (Enter for None) ")
    proceed = input("\nProceed (yes/no)? ")
    valid = ["yes", "y", "no", "n"]
    while True:
        if proceed.lower() in valid:
            if proceed.lower() == "yes" or proceed.lower() == "y":
                main(arguments)
                print("Done!")
                break
            else:
                print("Goodbye!")
                break
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")
            proceed = input("\nProceed (yes/no)? ")
