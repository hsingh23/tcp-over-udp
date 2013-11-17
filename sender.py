#!/usr/bin/python
from sys import argv
from TCPStates import State
from util import setup_socket_sender, parse_input_sender, Window, Event
from select import select
from ipdb import set_trace
from time import time as current_time


class TCPStateMachine(object):

    def __init__(s, file_name, udp, destination):
        super(TCPStateMachine, s).__init__()
        s.current_state = State.slow_start
        s.ack_count = 0
        chunks = s.chunkify_file(file_name, 100)
        s.window = Window(**{"MSS": 100.0, "ssthresh": 1000.0, "max_sequence_number": 9000, "max_cwnd": 25, "timeout_length": 1.0, "state_machine": s, "chunks": chunks, "udp": udp, "destination": destination})
        s.window.transmit_as_allowed()

    def done(s):
        return s.window.no_more_segments and s.window.empty_window()

    def parse_segment(s, segment):
        return int(segment)

    def chunkify_file(s, file_name, data_size):
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

    def run(s, event):
        if event.name == "ack":
            ack_num = s.parse_segment(event.data)
            event = s.window.add_ack(ack_num)
            if event:
                s.ack_count += 1
        if event:
            # if event.name == "timeout":
            #     print s.window.timeout_length
            s.current_state = s.current_state.next(event, s.window)


def main(argv):
    host, port, file_name, loss_file = parse_input_sender(argv)
    udp, destination = setup_socket_sender(host, port)
    t = TCPStateMachine(file_name, udp, destination)

    while not t.done():
        rlist, _, _ = select([udp], [], [], t.window.timeout_length)
        if len(rlist) == 0:
            t.run(Event("timeout", None))
        else:
            for sock in rlist:
                ack, addr = sock.recvfrom(4096)
                t.run(Event("ack", ack))
    with open("./trace_results/trace-%s%s" % (file_name, loss_file), "w") as f:
        f.writelines(t.window.trace_file)
    with open("./cwnd_results/cwnd-%s%s" % (file_name, loss_file), "w") as f:
        f.writelines(t.window.cwnd_file)
    print t.ack_count * 100 * 8 / (current_time() - t.window.start_time)

if __name__ == "__main__":
    main(argv[1:])
