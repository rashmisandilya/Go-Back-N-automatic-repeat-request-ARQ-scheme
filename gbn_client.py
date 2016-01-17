import os
import sys
import socket
from socket import *
import thread
from threading import *
import time
from time import *

global lock
lock = Lock()
global timerlock
timerlock = Lock()
global seq_num
global curr_seq_num
seq_num = 0
global recv_seq_num
global window
global mss
global total_packets
global gbntimer
global timeout
timeout = 0
global timerange
timerange = 0.5
global index
index = 0

server_hostname = str(sys.argv[1])
server_port = int(sys.argv[2])
file_name = str(sys.argv[3])
window = int(sys.argv[4])
mss = int(sys.argv[5])

start_time = time()
print start_time

sock = socket(AF_INET, SOCK_DGRAM)
sock.sendto("This is first message",(server_hostname, server_port))

def add_checksum(message):
    total = 0
    for i in range(0,len(message),16):
        data = message[i:i+16]
        int_num = int(data,2)
        total = total + int_num;
        if (total >= 65535):
            total -= 65535
    total = 65535 - total
    checksum_bits = '{0:016b}'.format(total)
    msg_header= message[0:32]+checksum_bits+message[48:]
    return msg_header

def formmsg(sequence, msg):
    data = ""
    for i in range(0,len(msg)):
        data_character = msg[i]
        data_byte = '{0:08b}'.format(ord(data_character))
        data = data + data_byte
    sequence_bits = '{0:032b}'.format(sequence)
    message = sequence_bits + "0"*16 + "01"*8 + data
    msg_checksum = add_checksum(message)
    return msg_checksum

def recv_data():
    global seq_num
    global gbntimer
    global index
    while True:
        #print "Receiving thread is running"
        (data, server) = sock.recvfrom(8240)
        lock.acquire()
        ackstr = "10"*8
        #print "data received"
        if(data[48:64] == ackstr):
            pass
        else:
            print "Discarding packet as this is not ack"
        recv_seq_num = int(data[0:32],2)
        if(recv_seq_num == (total_packets+1)):
            seq_num = recv_seq_num
            sock.sendto("File_sent", server);
            print "File is successfully sent"
            lock.release()
            break
        if(recv_seq_num > seq_num):
            diff = recv_seq_num - seq_num
            index = index - diff
            seq_num = recv_seq_num
            #print "Received seq number is %d and timer restarted" % recv_seq_num
            gbntimer.cancel()
            gbntimer = Timer(timerange, handle_timeout)
            gbntimer.start()
            lock.release()
        else:
            #print "Duplicate ack received. No action"
            lock.release()

    
def handle_timeout():
    global total_packets
    global timeout
    if(seq_num<=total_packets):
        print "Timeout, sequence number is %d" % seq_num
    timeout = 1


t1 = Thread(target=recv_data, args=())
t1.start()

if not os.path.isfile(file_name):
    print "File not present in the given path"
    exit
   
gbntimer = Timer(timerange, handle_timeout)

fo = open(file_name, "r")
total_file = fo.read()
total_packets = len(total_file)/mss

curr_seq_num = seq_num;

#print "Before gbntimerstart near main"
gbntimer.start()
while(t1.isAlive()):
    #print "Receiving thread is alive"
    #global seq_num
    #global curr_seq_num
    #global timerange
    #global handle_timeout
    #global timeout
    #print "Index is %d and window is %d" % (index,window)
    while(index<window):
        fo = open(file_name, "r")
        #print "lock not acquired"
        lock.acquire()
        #print "lock is acquired in main"
        if(curr_seq_num == seq_num):
            curr_seq_num = seq_num
            temp_index = index
            lock.release();
            #print "should be seeked"
            fo.seek((curr_seq_num+temp_index)*mss, 0)
            msgs = fo.read(mss)
            counter = msgs.count('\n')
            msg = msgs[0:(mss-counter)]
            fo.close()
            #print "Message is %s" % msg
            if(len(msg) != 0):
                #print "Message formed first"
                msg_final = formmsg((temp_index+curr_seq_num), msg)
                index = index + 1
                #print "message sent first and index is %d" % index
                sock.sendto(msg_final,(server_hostname, server_port))
            else:
                break
        else:
            curr_seq_num = seq_num
            temp_index = index
            lock.release();
            fo.seek((curr_seq_num+temp_index)*mss, 0)
            msgs = fo.read(mss)
            counter = msgs.count('\n')
            msg = msgs[0:(mss-counter)]
            fo.close()
            #print "Message is %s" % msg
            if(len(msg) != 0):
                #print "Message formed second"
                msg_final = formmsg((temp_index+curr_seq_num), msg)
                index = index + 1
                #print "message sent second and index is %d" % index
                sock.sendto(msg_final,(server_hostname, server_port))
            else:
                break
                
    if(timeout == 1):
        #print "In timeout, resetting index"
        index = 0
        gbntimer = Timer(timerange, handle_timeout)
        gbntimer.start()
        timeout = 0

sock.close()
stop_time = time()
print stop_time
print stop_time - start_time


