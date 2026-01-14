from garth.http import client
from getpass import getpass
from os.path import abspath, dirname, join

email = input("Enter email address: ")
password = getpass("Enter password: ")
client.login(email, password)
path = join(abspath(dirname(__file__)), "../tmp/garmin.txt")
with open(path, "w+") as file:
    file.write(client.dumps())