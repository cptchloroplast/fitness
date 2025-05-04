from garth.http import client
from getpass import getpass

email = input("Enter email address: ")
password = getpass("Enter password: ")
client.login(email, password)
with open("../tmp/garmin.txt", "w") as file:
    file.write(client.dumps())