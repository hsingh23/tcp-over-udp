tcp-over-udp
============

Created by Harsh Singh (hsingh23) and Ziqi Peng (peng20)

Going where no one has gone before.

Instructions:
	Sender:
		python sender.py -d localhost -p 9200 -f 10000_bytes [-l 1]
		-or-
		python sender.py --domain localhost --port 9200 --file 10000_bytes 

		-l is optional -> it will allow you to save a trace and cwnd file named with the lossfile name passed in.


	Reciever:
		python reciever.py -p 9200 -f 1
		-or-
		python reciever.py --port 9200 --file 1

Running sender will create the appropriate cwnd and trace file in the corrosponding cwnd_results and trace_results directory

It will also create, a check_file - this is what the reciever reassembled. You can run diff check_file 10000_bytes to see if it was assembled correctly!

Finally I also created state_logs which will print the various states the sender goes though.

Part 2,3 of the Analysis was done in an ipython notebook and can be seen at Analysis.html included in the directory.

Part 1 is in part-1.png