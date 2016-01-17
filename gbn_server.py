import thread
from threading import *
import socket
from socket import *
import time
import os
import random
import sys

def checksum(msg):
    total = 0
    for i in range(0,len(msg),16):
        int_num = int(msg[i:i+16],2)
        total = total + int_num;
        if (total >= 65535):
            total -= 65535
    if(total == 0):
        return 1
    else:
        return 0

def write_data(message):
    fd = open(file_name, "a");
    iterations = len(message)/8
    #print "Received message is %s" % message
    write_data = ""
    for i in range(0,iterations):
        bit_data = str(message[i*8:(i+1)*8])
        char_data = chr(int(bit_data, 2))
        write_data = write_data + char_data
    #print "Data being written in file is %s" % write_data
    fd.write(write_data)
    #print "File was written"
    fd.close()


#print 'Number of arguments:', len(sys.argv)
#print 'Argument List:', str(sys.argv)

server_hostname = str(sys.argv[1]);
server_port = int(sys.argv[2]);
file_name = str(sys.argv[3]);
prob = float(sys.argv[4])
prob_int = int(prob*100);

#print server_hostname
#print server_port
#print file_name
#print probability

if(os.path.isfile(file_name)):
    os.remove(file_name)


sock = socket(AF_INET,SOCK_DGRAM);                         
sock.bind((server_hostname, server_port));        

data,address = sock.recvfrom(32768)
#print data

global seq_num
seq_num = 0

while True:
    data, address = sock.recvfrom(32768);
    if(data == "File_sent"):
        break;
    
    if((int(data[0:32],2)) == seq_num):
        randum =  random.randint(0,99); 
        if(randum>=prob_int):
            if(checksum(data)):
                recv_seq_num = int(data[0:32],2);
                if(recv_seq_num == seq_num):
                    #print "Message received and recv seq num is %d" % recv_seq_num
                    seq_num += 1
                    new_data = data[64:]
                    #print "New data is %s" % new_data
                    write_data(new_data)
                    send_seq_num = '{0:032b}'.format(seq_num)
                    msg_to_be_sent = send_seq_num + '0'*16 + '10'*8
                    #print "ack sent is %d" % seq_num
                    #print msg_to_be_sent
                    sock.sendto(msg_to_be_sent, address)          
            else:
                seq = int(data[0:32],2)
                print "Checksum failed, sequence number = %d" % seq
        else:
            seq = int(data[0:32],2)
            print "Packet loss, sequence number = %d" % seq
    else:
        if((int(data[0:32],2)) < seq_num):
            seq = int(data[0:32],2)
            print "Received duplicate packet with sequence number = %d" % seq
        else:
            seq = int(data[0:32],2)
            #print "Received future packet with sequence number = %d" % seq
print "File received successfully"

    
    
    
    
    




