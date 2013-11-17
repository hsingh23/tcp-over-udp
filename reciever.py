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
    return Header(int(seq), int(last)), data


class Reassemble(object):

    def __init__(self):
        self.buffer = {}
        self.max_buffer_size = 25
        self.max_sequence_num = 9000
        self.result = ""
        self.current_sequence = 0

    def buffer_not_full(self):
        return len(self.buffer) <= self.max_buffer_size

    def expecting(self):
        return str(8999 if self.current_sequence == 0 else self.current_sequence - 1)

    def add(self, seq, data):
        seq = seq % self.max_sequence_num

        if seq == self.current_sequence:
            self.result += data
            self.current_sequence = (self.current_sequence + 1) % self.max_sequence_num
        elif self.buffer_not_full() and seq > self.current_sequence:
            self.buffer[seq] = data
        for k, v in sorted(self.buffer.iteritems()):
            if k == self.current_sequence:
                self.result += v
                self.current_sequence += 1
                del self.buffer[k]
            else:
                break
        return self.expecting()


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
    reassembler = Reassemble()
    not_done = True
    while not_done:
        rlist, _, _ = select([udp], [], [])
        for sock in rlist:
            data, address = sock.recvfrom(4096)
            header, parsed_data = parse_segment(data)
            if d.is_valid():
                ack = reassembler.add(header.sequence_number, parsed_data)
                udp.sendto(ack, address)
                # print parsed_data
                if header.is_last == 1:
                    not_done = False
    with open("check_file", "w") as f:
        f.writelines(reassembler.result)

if __name__ == "__main__":
    main(argv[1:])
