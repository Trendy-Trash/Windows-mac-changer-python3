with open(file="mac_addresses.txt", mode="w") as file:

    mac = '5800E3'
    for number in range(16**6):
        hex_num = hex(number)[2:].zfill(6)
        current_mac="{}{}{}{}{}{}{}".format(mac,*hex_num)
        print(current_mac)
        #file.write("jeje")
        file.write(current_mac + "\n")

file.close()
