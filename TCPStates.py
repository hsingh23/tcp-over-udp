from math import ceil
from time import time as current_time


class State(object):
    pass


class SlowStart(object):

    @staticmethod
    def next(event, window):
        window.states_log += "%s,SlowStart,%s,%s,%s\n" % ((current_time() - window.start_time), event.name, event.data, window.dup_ack_count)
        if event.name == "timeout":
            window.ssthresh = ceil(window.cwnd / 2)
            window.update_cwnd(window.MSS)
            window.dup_ack_count = 0
            window.retansmit_missing_segment(event.data)
            return State.slow_start

        elif event.name == "new_ack":
            window.update_cwnd(window.cwnd + window.MSS)
            window.transmit_as_allowed()
            window.update_trace(event.data)
            if window.cwnd >= window.ssthresh:
                return State.congestion_avoidance
            return State.slow_start

        elif event.name == "dup_ack":
            return State.slow_start

        elif event.name == "triple_ack":
            window.ssthresh = ceil(window.cwnd / 2)
            window.update_cwnd(window.ssthresh + 3 * window.MSS)
            window.retansmit_missing_segment(event.data)
            return State.fast_recovery
        raise Exception("Slow start got weird event")


class CongestionAvoidance(object):

    @staticmethod
    def next(event, window):
        window.states_log += "%s,CongestionAvoidance,%s,%s,%s\n" % ((current_time() - window.start_time), event.name, event.data, window.dup_ack_count)
        if event.name == "timeout":
            window.ssthresh = ceil(window.cwnd / 2)
            window.update_cwnd(window.MSS)
            window.dup_ack_count = 0
            window.retansmit_missing_segment(event.data)
            return State.slow_start

        elif event.name == "new_ack":
            window.update_cwnd(window.cwnd + (window.MSS * round(window.MSS / window.cwnd, -1)))
            window.update_trace(event.data)
            window.transmit_as_allowed()
            return State.congestion_avoidance

        elif event.name == "dup_ack":
            return State.congestion_avoidance

        elif event.name == "triple_ack":
            window.ssthresh = ceil(window.cwnd / 2)
            window.update_cwnd(window.ssthresh + 3 * window.MSS)
            window.retansmit_missing_segment(event.data)
            return State.fast_recovery

        raise Exception("Slow start got weird event")


class FastRecovery(object):

    @staticmethod
    def next(event, window):
        window.states_log += "%s,FastRecovery,%s,%s,%s\n" % ((current_time() - window.start_time), event.name, event.data, window.dup_ack_count)
        if event.name == "timeout":
            window.ssthresh = ceil(window.cwnd / 2)
            window.update_cwnd(window.MSS)
            window.dup_ack_count = 0
            window.retansmit_missing_segment(event.data)
            return State.slow_start

        elif event.name == "new_ack":
            window.update_cwnd(window.ssthresh)
            window.update_trace(event.data)
            window.transmit_as_allowed()
            return State.congestion_avoidance

        elif event.name == "dup_ack":
            window.update_cwnd(window.cwnd + window.MSS)
            return State.fast_recovery

        elif event.name == "triple_ack":
            window.update_cwnd(window.cwnd + window.MSS)
            return State.fast_recovery

State.slow_start = SlowStart()
State.congestion_avoidance = CongestionAvoidance()
State.fast_recovery = FastRecovery()
