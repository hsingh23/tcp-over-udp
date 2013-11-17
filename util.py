import getopt
import socket
from collections import namedtuple, OrderedDict
from ipdb import set_trace
from time import time as current_time

Event = namedtuple("Event", ["name", "data"])


def setup_socket_sender(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return sock, (socket.gethostbyname(host), int(port))


def setup_socket_reciever(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((socket.gethostbyname("0.0.0.0"), int(port)))
    return sock


def parse_input_sender(argv):
    help = """To set host, type --domain=localhost or -d localhost
                To set port, type --port=9000 or -p 9000
                To set file, type --file=9000 or -f 9000"""
    try:
        opts, args = getopt.getopt(
            argv, "hd:p:f:l:", ["help", "domain=", "port=", "file=", "loss-file="])
    except getopt.GetoptError:
        print help
        exit(2)
    host, file_name, port = (-1,) * 3
    loss_file = ""
    for opt, arg in opts:
        if opt in ['-h', "help"]:
            print help
            exit(2)
        elif opt in ("-p", "--port"):
            port = int(arg)
        elif opt in ("-d", "--domain"):
            host = arg
        elif opt in ("-l", "--loss-file"):
            loss_file = "-" + arg
        elif opt in ("-f", "--file"):
            file_name = arg
    if -1 in [host, file_name, port]:
        print "OI! You didn't supply one of the required values!!!!"
        print help
        exit(2)
    return host, port, file_name, loss_file


def parse_input_reciever(argv):
    help = """To set port, type --port=9000 or -p 9000
                To set lossfile, type --file=file_name or -f file_name
            """
    try:
        opts, args = getopt.getopt(
            argv, "hd:p:f:", ["help", "port=", "file="])
    except getopt.GetoptError:
        print help
        exit(2)
    host, file_name, port = (-1,) * 3
    for opt, arg in opts:
        if opt in ['-h', "help"]:
            print help
            exit(2)
        elif opt in ("-p", "--port"):
            port = int(arg)
        elif opt in ("-f", "--file"):
            file_name = arg
    if -1 in [file_name, port]:
        print "OI! You didn't supply one of the required values!!!!"
        print help
        exit(2)
    return port, file_name


class SequenceCounter(object):

    """docstring for SequenceCounter"""

    def __init__(self, max_count):
        super(SequenceCounter, self).__init__()
        self.max_count = max_count
        self.current_count = -1

    def next(s):
        s.current_count = (s.current_count + 1) % s.max_count
        return s.current_count

    def peek_next(s):
        return (s.current_count + 1) % s.max_count

    def next_number(s, k):
        return (k + 1) % s.max_count


class Window(object):

    """Current Window"""

    def __init__(s, **kwargs):
        super(Window, s).__init__()
        s.MSS = kwargs["MSS"]
        s.ssthresh = kwargs["ssthresh"]
        s.max_cwnd = kwargs["max_cwnd"]
        s.sequence_counter = SequenceCounter(kwargs["max_sequence_number"])
        s.timeout_length = kwargs["timeout_length"]
        s.cwnd = s.MSS
        s.destination = kwargs["destination"]
        s.dup_ack_count = 0
        s.no_more_segments = False
        s.sent = OrderedDict()
        s.state_machine = kwargs["state_machine"]
        s.get_segment = None
        s.chunks = iter(kwargs["chunks"])
        s.udp = kwargs["udp"]
        s.cwnd_file = ""
        s.trace_file = ""
        s.start_time = current_time()
        s.estimated_RTT = None
        s.dev_RTT = 0.1
        s.sampling = None
        s.last_ack = None
        s.states_log = ""

    def start_sample(s, key):
        if not s.sampling:
            s.sampling = (key, current_time())

    def update_estimate(s, key):
        if s.sampling and s.sampling[0] == key:
            if s.sent[key].ack_count == 1:
                sample_RTT = current_time() - s.sampling[1]
                if s.estimated_RTT:
                    s.estimated_RTT = 0.875 * s.estimated_RTT + .125 * sample_RTT
                else:
                    s.estimated_RTT = sample_RTT
                s.dev_RTT = 0.75 * s.dev_RTT + .25 * abs(sample_RTT - s.estimated_RTT)
                s.timeout_length = s.estimated_RTT + 4 * s.dev_RTT
            s.sampling = None

    def update_trace(s, seq):
        s.trace_file += "%s %s\n" % (current_time() - s.start_time, seq)

    def update_cwnd(s, cwnd):
        s.cwnd = cwnd
        s.cwnd_file += "%s %s\n" % (current_time() - s.start_time, cwnd)

    def unused_capacity(s):
        used = len(s.sent) * s.MSS
        return int((s.cwnd - used) / s.MSS)

    def increase_cwnd(s, more_in_bytes):
        x = s.cwnd + more_in_bytes
        s.cwnd = x if x < s.max_cwnd else s.max_cwnd

    def to_segment(s, data, current_sequence_number, last):
            return "SEQ:%s,LAST:%s##%s" % (current_sequence_number, last, data)

    def add_ack(s, key):
        if s.last_ack == key:
            s.dup_ack_count += 1
            if s.dup_ack_count == 2:
                event = Event("dup_ack", key)
            else:
                event = Event("triple_ack", key)
        else:
            s.dup_ack_count = 0
            s.last_ack = key
            event = Event("new_ack", key)
            for k, v in s.sent.items():
                if k <= key:
                    del s.sent[k]
        return event

    def send_segment(s, segment):
        s.udp.sendto(segment, s.destination)

    def transmit_as_allowed(s):
        for _ in xrange(s.unused_capacity()):
            key = s.sequence_counter.next()
            try:
                last, data = s.chunks.next()
                segment = s.to_segment(data, key, last)
                s.sent[key] = segment
                s.start_sample(key)
                s.send_segment(segment)

            except StopIteration:
                s.no_more_segments = True
                break

    def retansmit_missing_segment(s, key):
        if key is not None:
            key = s.sequence_counter.next_number(key)
            if key in s.sent:
                s.send_segment(s.sent[key])
        elif s.last_ack is not None:
            set_trace()
            last_ack = s.sequence_counter.next_number(s.last_ack)
            if last_ack in s.sent:
                s.send_segment(s.sent[last_ack])
        else:
            set_trace()

    def empty_window(s):
        return len(s.sent) == 0
