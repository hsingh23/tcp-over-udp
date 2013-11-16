#!/usr/bin/python
from sys import argv
from util import setup_socket_reciever, parse_input_reciever
from select import select
from ipdb import set_trace


def parse_segment(segment):
    header, _, data = segment.partition("##")
    seq, last = ((k.split(":")[1]) for k in header.split(","))
    return (seq, last), data


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

    while True:
        segments, _, _ = select([udp], [], [])
        for segment in segments:
            set_trace()
            print "GOT", segment
            header, data = parse_segment(segment)
            if d.is_valid():
                udp.sendto(header[0])
                print data, d.rsn
                if int(header[1]) == 1:
                    break


if __name__ == "__main__":
    main(argv[1:])
