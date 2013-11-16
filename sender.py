#!/usr/bin/python
from sys import argv
from TCPStates import State
from util import setup_socket_sender, parse_input_sender, Window, Event
from select import select
from ipdb import set_trace


class TCPStateMachine(object):

    def __init__(self, file_name, udp, destination):
        super(TCPStateMachine, self).__init__()
        self.current_state = State.slow_start
        chunks = self.chunkify_file(file_name, 100)
        self.window = Window(**{"MSS": 100, "ssthresh": 1000, "max_sequence_number": 9000, "max_cwnd": 25, "timeout_length": 3.0, "state_machine": self, "chunks": chunks, "udp": udp, "destination": destination})
        self.window.transmit_as_allowed()

    def done(s):
        return s.window.no_more_segments and s.window.empty_window()

    def parse_segment(self, segment):
        return int(segment)

    def chunkify_file(self, file_name, data_size):
        chuncks = []
        with open(file_name, "r") as f:
            chuncks.append([0, f.read(data_size)])
        chuncks[-1][0] = 1
        return chuncks

    def run(self, event):
        if event.name == "ack":
            ack_num = self.parse_segment(event.data)
            event = self.window.add_ack(ack_num)


def main(argv):
    host, port, file_name = parse_input_sender(argv)
    udp, destination = setup_socket_sender(host, port)
    t = TCPStateMachine(file_name, udp, destination)

    while not t.done():
        acks, _, _ = select([udp], [], [], t.window.MSS)
        if len(acks) == 0:
            t.run(Event("timeout", None))
        else:
            for ack in acks:
                t.run(Event("ack", ack))


if __name__ == "__main__":
    main(argv[1:])
