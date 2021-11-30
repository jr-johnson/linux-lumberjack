#!/usr/bin/python3
from shutil import copyfile
from shutil import move
from os import remove
from os import environ
import os
import os.path
import sys
import subprocess

homedir = os.environ['HOME']
bash_target_file = homedir + "/.bashrc"
bash_backup_file = homedir + "/.backup-bashrc"
bash_new_file = homedir + "/.newbashrc"
interfaces = []

def get_network_interfaces():
        for line in open('/proc/net/dev', 'r'):
                if line.find(":") != -1 and line.find("lo") == -1:
                        interfaces.append(line.split(":")[0].strip())

def modify_bash_terminal_line(selected_interface):
        with open(bash_new_file, "w") as newfile:
                with open (bash_target_file) as oldfile:
                        for line in oldfile:
                                if line.find("PS1") != -1 and not line.strip().startswith("#"):
                                        ### This modifies the terminal to show timestamp, IP, and current directory inline
                                        newfile.write("PS1=\'[`date  +\"%d-%b-%y %T\"`]\\[\\033[01;31m\\] `ifconfig " + selected_interface + " 2>/dev/null | sed -n 2,2p | cut -d\" \" -f 10`\\[\\033[00m\\] \\[\\033[01;34m\\]\\W\\[\\033[00m\\] > \'" + "\n")
                                else:
                                        newfile.write(line)
        remove(bash_target_file)
        move(bash_new_file, bash_target_file)

def add_log_file_creation():
        with open(bash_target_file, "a") as f:
                ### Add a line to the .bashrc file to create a new log file and log all shell commands
                f.write("test \"$(ps -ocommand= -p $PPID | awk \'{print $1}\')\" == \'script\' || (script -f $HOME/$(date +\"%d-%b-%y_%H-%M-%S\")_shell.log)")

def zsh_log_file_creation(user):
        zsh_filename = "/" + user + "/.zshrc"
        with open(zsh_filename, "a") as file:
                file.write("precmd() { eval 'RETRN_VAL=$?;logger -p local6.debug \"$(whoami) [$$]: $(history | tail -n1 | sed \"s/^[ ]*[0-9]\+[ ]*//\" ) [$RETRN_VAL]\"' }")


def main():
        if ("zsh" in environ['SHELL']):
                with open("/etc/rsyslog.d/commands.conf", "w") as commands:
                        commands.write("local6.*    /var/log/commands.log")

                result = subprocess.run(["service", "rsyslog restart"], capture_output=True, text=True)

                # Make modifications to .zshrc
                if os.path.isfile("/root/.zshrc"):
                        copyfile("/root/.zshrc", "/root/.backup_zshrc") ### make a back-up just in case :)
                        zsh_log_file_creation("root")
                else:
                        print("Something's wrong... there's no \".zshrc\" file for root!")

                if os.path.isfile("/home/kali/.zshrc"):
                        copyfile("/home/kali/.zshrc", "/home/kali/.backup_zshrc") ### make a back-up just in case :)
                        zsh_log_file_creation("home/kali")
                else:
                        print("Something's wrong... there's no \".zshrc\" file for kali!")
        else:
                if os.path.isfile(bash_target_file):
                        ### Figure out what network interfaces are available
                        selected_interface = None
                        get_network_interfaces()

                        ### If there is only one interface, don't bother asking the user - just set that
                        if len(interfaces) != 0 and len(interfaces) == 1:
                                selected_interface = interfaces[0]
                        else: ### Otherwise, ask the user to select from the available network interfaces
                                while selected_interface not in interfaces:
                                        selected_interface = raw_input("Choose your active interface: " + ' '.join(interfaces) + "\n")

                        copyfile(bash_target_file, bash_backup_file) ### make a back-up of the .bashrc - just in case :)
                        modify_bash_terminal_line(selected_interface)
                        add_log_file_creation()
                else:
                        print("Something's wrong... there's no \".bashrc\" file!")

if __name__ == "__main__":
        main()
