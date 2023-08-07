def get_binary_from_string(s):
    return ''.join(format(ord(i), '08b') for i in s)

def get_string_from_binary(bin_data):
    str_data = ""
    for i in range(0, len(bin_data), 8):
        decimal_data = int(bin_data[i:i + 8], 2)
        str_data = str_data + chr(decimal_data)
    return str_data

def get_binary_from_decimal(dec_data):
    from math import ceil
    b_str =  bin(dec_data).replace("0b", "")
    length = ceil(len(b_str)/8)*8
    return ("0"* (length-len(b_str))) + b_str

def get_decimal_from_binary(bin_data):
    return int(bin_data, 2)