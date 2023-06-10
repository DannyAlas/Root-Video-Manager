from math import e
from capture_devices import devices

d_list = devices.run_with_param(device_type="video", alt_name=True,list_all=True, result_=True)

# the list is ordered by device name and alternative name
# grab the device name and alternative name from the list and add them to a dictionary

d_dict = {}

for i in range(0,len(d_list),2):
    # use the alternative name as the key
    alt_name_str = d_list[i+1]
    alt_name = alt_name_str.split(":")[1].strip()
    # use the device name as the value
    device_name_str = d_list[i]
    device_name = device_name_str.split(":")[1].strip()

    d_dict[alt_name] = device_name

print(d_dict)
    

    