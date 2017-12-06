"""Manage iris configurations."""

# Built-in modules
from contextlib import contextmanager

# Third-Party modules
import serial
from serial.tools.list_ports import comports as list_serial_ports

# Protobuf
import iris_pb2 as pb


def enumerate_irises():
    """Return a generator to iterate over all connected iris devices."""
    serial_ports = list_serial_ports()
    for port in serial_ports:
        # These VIDs and PIDs are the ones used by Arduino Micros
        # They need to be changed for the production version!
        if port.vid == 0x2341 and port.pid == 0x8037:
            yield port

@contextmanager
def open_iris(port_info):
    """Open an iris device for the duration of a with statement."""
    device_name = port_info.device
    try:
        # Configure and open serial port
        serial_port = serial.Serial(port=device_name,
                                    baudrate=9600,
                                    timeout=1,
                                    write_timeout=1)
        yield serial_port
    finally:
        serial_port.close()

def read_all(port, chunk_size=200):
    """Read all characters on the serial port and return them."""
    if not port.timeout:
        raise TypeError('Port needs to have a timeout set!')

    read_buffer = b''

    while True:
        # Read in chunks. Each chunk will wait as long as specified by
        # timeout. Increase chunk_size to fail quicker
        byte_chunk = port.read(size=chunk_size)
        read_buffer += byte_chunk
        if not len(byte_chunk) == chunk_size:
            break

    return read_buffer

def send_message(port, message):
    """Send message to Arduino."""
    port.write(message.SerializeToString())

def send_signal(port, signal):
    """Send signal to Arduino."""
    request = pb.MessageData()
    request.signal = signal
    send_message(port, request)

def is_string_message(byte_string):
    """Check if bytes are a string message."""
    # See lib-iris/iris.proto for details
    return byte_string[0] == 4

def decode_string(byte_string):
    """Decode string message from byte string."""
    if not is_string_message(byte_string):
        raise TypeError('`{}` is not a valid string message!'
                        .format(byte_string))

    return byte_string[1:].decode('utf-8')

def receive_message(port):
    """Receive message from Arduino and return it."""
    response_bytes = read_all(port)

    # If a string was sent, an error occurred on the Iris
    # and the string contains error info
    if is_string_message(response_bytes):
        raise RuntimeError(decode_string(response_bytes))

    response = pb.MessageData()
    try:
        response.ParseFromString(response_bytes)
    except Exception as ex:
        ex.args = ex.args + (response_bytes,)
        raise

    return response

def get_info(port):
    """Request info and return response."""
    request = pb.MessageData()
    request.signal = pb.MessageData.RequestInfo
    send_message(port, request)

    response_bytes = read_all(port)
    # Response will be a byte-string with leading \x04
    response = decode_string(response_bytes)

    return response

def download_configuration(port):
    """Download configuration from iris."""
    configuration = pb.Configuration()

    send_signal(port, pb.MessageData.DownloadConfiguration)

    # In this case, it is required that cues and schedules are sent in-
    # order. However, we don't care whether cues or schedules are sent
    # first, and they could be sent interlaced as well
    while True:
        response = receive_message(port)
        if response.HasField('cue'):
            configuration.all_cues.extend([response.cue])

        elif response.HasField('schedule'):
            configuration.all_schedules.extend([response.schedule])

        elif response.signal == pb.MessageData.Confirm:
            return configuration

        else:
            raise RuntimeError(response)

        send_signal(port, pb.MessageData.RequestNext)

def main():
    """Execute as a script."""
    # Get the first iris that's found
    current_iris = next(enumerate_irises())
    with open_iris(current_iris) as active_iris:
        print('Initial data on serial output:')
        print(read_all(active_iris))

        print('Info Response:')
        print(get_info(active_iris))

        print('Confirm Response:')
        send_signal(active_iris, pb.MessageData.Confirm)
        print(receive_message(active_iris))

        print('RequestNext Response:')
        send_signal(active_iris, pb.MessageData.RequestNext)
        try:
            receive_message(active_iris)
        except RuntimeError as ex:
            print(ex.args[0])

        print('DownloadConfiguration Response:')
        print(download_configuration(active_iris))

if __name__ == "__main__":
    main()
