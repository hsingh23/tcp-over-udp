#!/usr/bin/python
from sys import argv
from TCPStates import State
from util import setup_socket, consumer, parse_input_sender, Window, Event
from select import select


class TCPStateMachine(object):

    def __init__(self, file_name, udp):
        super(TCPStateMachine, self).__init__()
        self.udp = udp
        self.current_state = State.slow_start
        self.file_name = file_name
        self.no_more_segments = False
        self.window = Window({"MSS": 100, "ssthresh": 1000, "max_seq": 9000, "max_cwnd": 25, "timeout_length": 3.0, "state_machine": self})

    def done(s):
        return s.no_more_segments and s.window.empty_window

    def to_segment(self, data, last):
        segment = "SEQ:%s,LAST:%s##%s" % self.current_sequence_number, self.last
        self.current_sequence_number += 1
        return segment

    def parse_segment(self, segment):
        return int(segment)

    def send_segment(self, segment):
        self.udp.sendall(segment)

    def get_segment(self):
        def is_not_last(x, y):
            return len(y) != 0
        with open(self.file_name, "r") as f:
            x = f.read(self.window.MSS)
            y = f.read(self.window.MSS)
            while is_not_last(x, y):
                yield self.to_segment(x, 0)
                x = y
                y = f.read(self.window.MSS)
            yield self.to_segment(x, 1)
            self.no_more_segments = True

    @consumer
    def run(self):
        try:
            while True:
                event = (yield)
                if event.name == "ack":
                    ack_num = self.parse_segment(event.data)
                    event = self.window.add_ack(ack_num)
                self.current_state = self.current_state.next(event, self.current_state)

        except GeneratorExit:
            print "Done"


def main(argv):
    host, port, file_name = parse_input_sender(argv)
    udp = setup_socket(host, port)
    t = TCPStateMachine(file_name, udp)

    while not t.done():
        acks, _, _ = select([udp], [], [], t.current.timeout_length)
        if len(acks) == 0:
            t.run(Event("timeout", None))
        else:
            for ack in acks:
                t.run(Event("ack", ack))


if __name__ == "__main__":
    main(argv[1:])
