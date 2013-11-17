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
        self.window = Window(**{"MSS": 100.0, "ssthresh": 1000.0, "max_sequence_number": 9000, "max_cwnd": 25, "timeout_length": 1.0, "state_machine": self, "chunks": chunks, "udp": udp, "destination": destination})
        self.window.transmit_as_allowed()

    def done(s):
        return s.window.no_more_segments and s.window.empty_window()

    def parse_segment(self, segment):
        return int(segment)

    def chunkify_file(self, file_name, data_size):
        chunks = []
        with open(file_name, "r") as f:
            while True:
                x = f.read(data_size)
                if len(x) > 0:
                    chunks.append([0, x])
                else:
                    break
        chunks[-1][0] = 1
        return chunks

    def run(self, event):
        if event.name == "ack":
            ack_num = self.parse_segment(event.data)
            event = self.window.add_ack(ack_num)
        self.current_state = self.current_state.next(event, self.window)


def main(argv):
    host, port, file_name = parse_input_sender(argv)
    udp, destination = setup_socket_sender(host, port)
    t = TCPStateMachine(file_name, udp, destination)

    while not t.done():
        rlist, _, _ = select([udp], [], [], t.window.MSS)
        if len(rlist) == 0:
            t.run(Event("timeout", None))
        else:
            for sock in rlist:
                ack, addr = sock.recvfrom(4096)
                t.run(Event("ack", ack))
    with open("trace-%s" % file_name, "w") as f:
        f.writelines(t.window.trace_file)
    with open("cwnd-%s" % file_name, "w") as f:
        f.writelines(t.window.cwnd_file)


if __name__ == "__main__":
    main(argv[1:])
