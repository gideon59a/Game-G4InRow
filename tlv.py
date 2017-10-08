'''
Created on Oct 2017, copied from 2015's game.py
'''

import sys

# xx from G4InRow.Server_2 import clients_list
sys.path.append('../')  # this has been added so can be found in cmd window

####from G4InRow.Server_2 import game_instance

'''
Created on May 8, 2015 @author: Gideon
Flow (what each entity sends, marked with "(O)" ):
 Player A             Player B              Server
 ========             ========              ======
 connect
 (O)my_info                                   
                                        (O) my_info (confirmation)
                                        to A your_role=A (to B your_role=B)
                                        (O)to A game_status=W (wait for opponent)
                     connect
                     (O)my_info               
                                        (O)to A&B game_status=S (started)
                                        (O)to A&B game_info=players (names,...)
                                        to A&B play_command=A to play (so game starts)
 my_move (okay)
                                        to A&B game_board
                                        to A&B play_command=B to play
 my_move with error                                       
                                        send message to A
                                        to A&B play_command=A to play
 my_move (ends game)
                                        to A&B play_command=A is the winner (game over)


TLV Type,        len,   Value1 and          Value2:
===================================================
from server:
-----------
your_role,       len,   A or B,             null
(O)game_status,  len,   W (wait)            null
(O)game_status,  len,   S (started),        null
game_status,     len,   Z (game over),      A or B or T (tie) or E (error)
play_command,    len,   A (meaning A play), null
play_command,    len,   B (meaning B play), null
game_board,      len,   last move details,  board string
text_message,    len,   text line,          text line : Note: text must not include "," ! because is a delimiter... 

form player:
-----------
my_info,        len,   name,                 game requested
my_move,        len,   A or B,               column

'''

import re
import queue
from G4InRow import boardClass
# from FourInRowGame.boardClass import Board
import G4InRow.gls as gls

# from FourInRowGame.gls import turn_is as turn_is
####from G4InRow.Server_2 import clients

######################################################################################################################
# enumerations of the tlv_type
my_info = 0  # info the client sends to the server, as well as the rsponse to the client
my_move = 1
play_command = 2
game_board = 3
players_info = 4
your_role = 5
game_status = 6
text_message = 7
tlv_value_fieldLen = {my_info: 10, my_move: 2, play_command: 2, game_board: 56, players_info: 20, your_role: 2,
                      game_status: 6, text_message: 100}  # TLV value len per tlv_type

debug_level = gls.debug_level


class tlv:
    """
    The tlv has 4 "values" (fields): type, len (of values), value 1 and value2
    """

    # global my_info, play_command, my_move, game_board, end_command
    # (my_info, play_command, my_move, game_board, end_command) = (range(5)) #TLV types enumeration

    # print ("tlv class:",myinfo, tlv_value_fieldLen[my_info]) #debug
    def __init__(self, tlv_type=0, tlv_value1="", tlv_value2=""):
        self.tlv_type = tlv_type  # An integer for enumeration
        # if tlv_len==0:
        #    self.tlv_len=self.tlv_value_fieldLen[self.tlv_type] # An integer for enumeration
        # else: #if len is received when tlv is created
        #    self.tlv_len=tlv_len
        self.tlv_len = tlv_value_fieldLen[self.tlv_type]
        self.tlv_value1 = tlv_value1  # string
        self.tlv_value2 = tlv_value2  # string

    def print_tlv(self):
        if debug_level > 1: print("Type=", self.tlv_type, "Len=", self.tlv_len, "Val1=", self.tlv_value1, "val2=",
                                  self.tlv_value2)

    def tlv2str(self):
        # strset=str(type)+","+str(self.tlv_value_fieldLen[type])+","+str(value1)+","+str(value2)
        strset = str(self.tlv_type) + "," + str(self.tlv_len) + "," + str(self.tlv_value1) + "," + str(self.tlv_value2)
        strset = gls.SOM + strset + gls.EOM  # encapsulate message string with SOM and EOM
        return strset

    def str2tlv(self, istr):
        rxtlv_list = re.split(',', istr)  # convert the received string to a list (of characters)
        if debug_level > 0: print("rxtlv_list", rxtlv_list)
        self.tlv_type = int(rxtlv_list[0])
        self.tlv_len = int(rxtlv_list[1])
        self.tlv_value1 = rxtlv_list[2]
        self.tlv_value2 = rxtlv_list[3]

# ********* testing *********
if __name__ == '__main__':
    # test number 1
    test_tx_queue = queue.Queue(10) # create a queues that emulates the queue to send
    test_rx_queue = queue.Queue(10) # create a queue that emulates the rx queue that contains the message to process

    test1_tlv_to_send = tlv(my_info,"myName","4InRow")
    print ("tx tlv: ")
    test1_tlv_to_send.print_tlv()
    test1_str_to_send = test1_tlv_to_send.tlv2str()
    print ("tx tlv in string format:",test1_str_to_send)

    test_tx_queue.put_nowait(test1_str_to_send)  # put the string in the queue
    # at this point the tx queue has a message with the delimiters

    # Now the reverse direction, i.e. get the message from the queue and print it
    rx_raw_message = test_tx_queue.get_nowait()  # get the string from the queue. It includes the delimiters
    # Extract the message from the queue, without the message delimiters
    import connect_tcp
    # data_stream, rx_queue = connect_tcp.extract_message(rxstr, data_stream, rx_queue)
    data_stream, test_queue = connect_tcp.extract_message("", rx_raw_message, test_rx_queue)
    rx_clean_message = test_rx_queue.get_nowait()

    rxtlv = tlv()
    rxtlv.str2tlv(rx_clean_message)
    print ("the received message:")
    rxtlv.print_tlv()
    #print (gls.SOM+rx_clean_message+gls.EOM)
    #print (test1_str_to_send)
    if (gls.SOM+rx_clean_message+gls.EOM) == test1_str_to_send :
        print ("test 1 succeded")
    else: print ("test 1 failed")

    pass