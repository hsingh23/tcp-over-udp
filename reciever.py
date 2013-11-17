#!/usr/bin/python
from sys import argv
from util import setup_socket_reciever, parse_input_reciever
from select import select
from collections import namedtuple
from ipdb import set_trace

Header = namedtuple("Header", ["sequence_number", "is_last"])


def parse_segment(segment):
    header, _, data = segment.partition("##")
    seq, last = ((k.split(":")[1]) for k in header.split(","))
    return Header(seq, int(last)), data


class Decider(object):

    """docstring for Decider"""

    def __init__(self, lossfile):
        super(Decider, self).__init__()
        self.rsn = 0
        x = lossfile.split()
        if x[0] == 0:
            self.is_valid = self.yes
        elif x[0] == 1:
            self.discard = x[1]
            self.is_valid = self.repeated
        else:
            self.discard = set(x[1:])
            self.is_valid = self.selected

    def yes(s):
        return True

    def repeated(s):
        s.rsn += 1
        return True if s.rsn % s.discard != 0 else False

    def selected(s):
        s.rsn += 1
        return True if s.rsn not in s.discard else False


def main(argv):
    port, file_name = parse_input_reciever(argv)
    udp = setup_socket_reciever(port)
    with open(file_name, "r") as f:
        d = Decider(f.read())
    not_done = True
    while not_done:
        rlist, _, _ = select([udp], [], [])
        for sock in rlist:
            data, address = sock.recvfrom(4096)
            header, parsed_data = parse_segment(data)
            if d.is_valid():
                udp.sendto(header.sequence_number, address)
                # print parsed_data
                if header.is_last == 1:
                    not_done = False


if __name__ == "__main__":
    main(argv[1:])
