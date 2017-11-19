"""Manage iris configurations."""

from enum import Enum
import struct
import itertools

def get_bit_as_bool(number, bit_index):
    """Extract a bit from number and return it as a boolean."""
    return True if number >> bit_index & 1 == 1 else False

class RampType(Enum):
    """Specify types of ramping functions."""
    linearHSL = 0
    linearRGB = 1
    jump = 2

class Color:
    """Model a Color."""

    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    # Paramters for structure packing and unpacking
    _format = '<BBB'
    _format_size = struct.calcsize(_format)

    @classmethod
    def from_bytes(cls, bytes_iter):
        # Read out necessary bytes from iterator
        byte_list = bytes(itertools.islice(bytes_iter, 0, cls._format_size))

        # Load bytes into attributes
        return cls(*struct.unpack(cls._format, byte_list))

class Cue:
    """Model a Cue."""

    #pylint: disable=R0902
    # We need a lot of attributes in this class

    def __init__(self, #pylint: disable=R0913
                 channels=[False for _ in range(12)],
                 reverse=False,
                 wrap_hue=False,
                 time_divisor=12,
                 delay=0,
                 duration=1000,
                 ramp_type=RampType.jump,
                 ramp_parameter=1000,
                 start_color=Color(0,0,0),
                 end_color=Color(0,0,0),
                 offset_color=Color(0,0,0)
        ):
        #Format H - 2 bytes (values are bits)
        self.channels = channels
        self.reverse = reverse
        self.wrap_hue = wrap_hue
        # Format B - 1 byte
        self.time_divisor = time_divisor
        # Format H - 2 bytes
        self.delay = delay
        # Fomrat L - 4 bytes
        self.duration = duration
        # Format B - 1 bytes
        self.ramp_type = ramp_type
        # Format L - 4 bytes
        self.ramp_parameter = ramp_parameter
        # Colors are read with their own formatter
        self.start_color = start_color
        self.end_color = end_color
        self.offset_color = offset_color


    # Parameters for structure packing and unpacking
    _format = '<HBHLBL' # See __init__
    _format_size = struct.calcsize(_format)

    @classmethod
    def from_bytes(cls, bytes_iter):
        """Construct from iterator over byte string."""

        # Read out necessary bytes from iterator
        byte_list = bytes(itertools.islice(bytes_iter, 0, cls._format_size))

        # Unpack to tuple
        argument_tuple = struct.unpack(cls._format, byte_list)
        # Split tuple into two parts
        channels_reverse_wrap = argument_tuple[0]
        argument_tuple = argument_tuple[1:]

        # Extract channels by iterating over bits
        channels = []
        for i in range(12):
            bit_value = get_bit_as_bool(channels_reverse_wrap, i)
            channels.append(bit_value)

        # Extract other flags
        reverse = get_bit_as_bool(channels_reverse_wrap, 12)
        wrap_hue = get_bit_as_bool(channels_reverse_wrap, 13)

        # Read colors
        start_color = Color.from_bytes(bytes_iter)
        end_color = Color.from_bytes(bytes_iter)
        offset_color = Color.from_bytes(bytes_iter)

        print(*argument_tuple)

        return cls(channels,
                   reverse,
                   wrap_hue,
                   *argument_tuple,
                   start_color,
                   end_color,
                   offset_color)

class Period:
    """Model a Period."""

    def __init__(self, cue_id, delays=[]):
        self.cue_id = cue_id
        self.delays = delays

class Header:
    """Model the header of a binary configuration."""

    def __init__(self, number_of_cues=0, number_of_schedule_elements=0):
        self.number_of_cues = number_of_cues
        self.number_of_schedule_elements = number_of_schedule_elements

    # Parameters for structure packing and unpacking
    _format = '<2H'
    _format_size = struct.calcsize(_format)

    @classmethod
    def from_bytes(cls, bytes_iter):
        """Construct from iterator over byte string."""

        # Read out necessary bytes from iterator
        byte_list = list(itertools.islice(bytes_iter, 0, cls._format_size))

        # Load bytes into attributes
        return cls(*struct.unpack(cls._format, byte_list))


def load_from_bytes(byte_string):
    """Load a configuration from binary source.
    
    This will likely come from an Iris itself."""

    bytes_iter = iter(byte_string)

    # Load header
    header = Header.from_bytes(bytes_iter)

    # Load Cues
    all_cues = []
    for i in range(header.number_of_cues):
        all_cues.append(Cue.from_bytes(bytes_iter))

    return header, all_cues


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
    byte_string = iris.convert_decimal_string_to_bytes(input_string)
    header, all_cues = load_from_bytes(byte_string)

if __name__ == "__main__":
    main()