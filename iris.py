"""Manage iris configurations."""

def convert_decimal_string_to_bytes(decimal_string):
    """Convert a string of space-delimited decimal numbers into
    a byte-string.
    
    Mainly used for debugging."""

    decimal_string = decimal_string.rstrip()
    number_list = decimal_string.split(' ')
    number_list = [int(num) for num in number_list]
    return bytes(number_list)

def main():
    """Execute as a script."""
    pass

if __name__ == "__main__":
    main()