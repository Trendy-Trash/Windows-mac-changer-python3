#!/usr/bin/env python3
from randmac import RandMac
import subprocess
import winreg
import re

# import os
# from shutil import move
# from tempfile import NamedTemporaryFile

# regular expression (regex) for MAC addresses.
MAC_ADD_REGEX = re.compile(r"([A-Za-z0-9]{2}[:-]){5}([A-Za-z0-9]{2})")

# regex for the transport names.
TRANSPORT_NAME = re.compile("({.+})")

# regex to pick out the adapter index
ADAPTER_INDEX = re.compile("([0-9]+)")


def choose_mac():
    mac_addresses = list()  # empty list to store all the MAC addresses.
    getmac_output = subprocess.run("getmac", capture_output=True).stdout.decode('latin', errors='ignore').split('\n')

    # loop through the output
    for macAdd in getmac_output:
        mac_find = MAC_ADD_REGEX.search(macAdd)
        transport_find = TRANSPORT_NAME.search(macAdd)
        # If you don't find a Mac Address or Transport name the option won't be listed.
        if mac_find is None or transport_find is None:
            continue
        # append a tuple with the Mac Address and the Transport name to a list.
        mac_addresses.append((mac_find.group(0), transport_find.group(0)))

    ###################################################################################################################
    # Uncomment this part if you have different adapters connected and you want to choose between them

    # # Create a simple menu to select which Mac Address the user want to update.
    # print("Which MAC Address do you want to update?")
    # for index, item in enumerate(mac_addresses):
    #     print(f"{index} - Mac Address: {item[0]} - Transport Name: {item[1]}")
    #
    # # Prompt the user to select Mac Address they want to update.
    # option = input("Select the menu item number corresponding to the MAC that you want to change:")

    ###################################################################################################################

    return mac_addresses

# this part is to use a file with addresses, reading and moving the mac readed to the end, se we dont repeat.
# def mac_rolling():
#     file_path = 'mac_addresses.txt'
#     temp_path = None
#     with open(file_path, 'r') as f_in:
#         first_line = f_in.readline()
#         with NamedTemporaryFile(mode='w', delete=False) as f_out:
#             temp_path = f_out.name
#             # next(f_in)  # skip first line
#             for line in f_in:
#                 f_out.write(line)
#             f_out.write(first_line)
#
#     os.remove(file_path)
#     move(temp_path, file_path)
#     return first_line


def mac_changer(mac_to_change_to, mac_addresses):
    # We know the first part of the key, we'll append the folders where we'll search the values
    controller_key_part = r"SYSTEM\ControlSet001\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"

    # connect to the HKEY_LOCAL_MACHINE registry.
    # If we specify None, connect to local machine's registry.
    with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
        # Create a list for the 21 folders. I used a list comprehension. The expression part of the list comprehension
        # makes use of a ternary operator. The transport value for your Mac Address should fall within this range.
        # You could write multiple lines.
        controller_key_folders = [("\\000" + str(item) if item < 10 else "\\00" + str(item)) for item in range(0, 21)]
        # We now iterate through the list of folders we created.
        for key_folder in controller_key_folders:
            # We try to open the key. If we can't, we just except and pass. But it shouldn't be a problem.
            try:
                # We have to specify the registry we connected to, the controller key
                # (This is made up of the controller_key_part we know and the folder(key) name we created
                # with the list comprehension).
                with winreg.OpenKey(hkey, controller_key_part + key_folder, 0, winreg.KEY_ALL_ACCESS) as regkey:
                    # We will now look at the Values under each key and see if we can find the "NetCfgInstanceId"
                    # with the same Transport ID as the one we selected.
                    try:
                        # Values start at 0 in the registry and we have to count through them.
                        # This will continue until we get a WindowsError (Where we will then just pass)
                        # then we'll start with the next folder until we find the correct key which contains
                        # the value we're looking for.
                        count = 0
                        while True:
                            # We unpack each individual winreg value into name, value and type.
                            name, value, type = winreg.EnumValue(regkey, count)
                            # To go to the next value if we didn't find what we're looking for we increment count.
                            count = count + 1
                            # We check to see if our "NetCfgInstanceId" is equal to our Transport number for our
                            # selected Mac Address.
                            if name == "NetCfgInstanceId" and value == mac_addresses[0][1]:
                                new_mac_address = mac_to_change_to
                                winreg.SetValueEx(regkey, "NetworkAddress", 0, winreg.REG_SZ, new_mac_address)
                                # print("Successly matched Transport Number")
                                # get list of adapters and find index of adapter you want to disable.
                                break
                    except WindowsError:
                        pass
            except:
                pass


def restart_adapters(mac_to_change_to):
    # Code to disable and enable Wireless devices

    while True:

        # Code to disable and enable the network adapters
        # We get a list of all network adapters. You have to ignore errors,
        # as it doesn't like the format the command returns the data in.
        network_adapters = subprocess.run(["wmic", "nic", "get", "name,index"], capture_output=True).stdout.decode(
            'utf-8', errors="ignore").split('\r\r\n')
        for adapter in network_adapters:
            # We get the index for each adapter
            adapter_index_find = ADAPTER_INDEX.search(adapter.lstrip())
            # If there is an index and the adapter has wireless in description, disable and enable the adapter
            if adapter_index_find and "Wireless" in adapter:
                disable = subprocess.run(
                    ["wmic", "path", "win32_networkadapter", "where", f"index={adapter_index_find.group(0)}", "call",
                     "disable"], capture_output=True)
                # If the return code is 0, it means that we successfully disabled the adapter
                if disable.returncode == 0:
                    print(f"Disabled {adapter.lstrip()}")
                # We now enable the network adapter again.
                enable = subprocess.run(
                    ["wmic", "path", f"win32_networkadapter", "where", f"index={adapter_index_find.group(0)}", "call",
                     "enable"], capture_output=True)
                # If the return code is 0, it means that we successfully enabled the adapter
                if enable.returncode == 0:
                    print(f"Enabled {adapter.lstrip()}")

        # run the getmac command again
        getmac_output = subprocess.run("getmac", capture_output=True).stdout.decode(errors='ignore')
        # recreate the Mac Address as it shows up in getmac XX-XX-XX-XX-XX-XX format
        mac_add = "-".join([(mac_to_change_to[i:i + 2]) for i in
                            range(0, len(mac_to_change_to) - 1, 2)])
        # check if Mac Address is in getmac output
        if mac_add.upper() in getmac_output:
            print("Mac Address Success")
        else:
            print("FAIL")
        break


def main():
    macAddresses = choose_mac()
    mac_in = "1ee7:6900:0000"
    # print(mac_addresses)
    mac_out = str(RandMac(mac_in, True))
    print(f"Changing mac address to: {mac_out.upper()}")
    mac_up = mac_out.upper()
    # print(mac_up)
    mac_changer(mac_up, macAddresses)
    restart_adapters(mac_out)


main()
