'''
Created on Oct 2017, started with old "PlayerMain.py" @author: Gideon
Vesion 0.1
'''

import socket
import sys
import queue
sys.path.append('../') #this has been added so can be found in cmd window

TCP_PORT=50002

from G4InRow.gls import gameover
import G4InRow.gls as gls
import G4InRow.game as game
import G4InRow.connect_tcp as connect_tcp
import G4InRow.pre_gameM as pre_gameM


debug_level=gls.debug_level #0 for no debug, 1 for basic debug, 2 for details


def connect2sever (server_ip_address,destination_port):
    iserver_address = (server_ip_address, destination_port)
    # Create a TCP/IP socket
    isock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    print ('connecting to %s port %s' % iserver_address)
    try:
        isock.connect(iserver_address)
    except:    
        print ("error connecting to the server.")
        return -1
    else:    
        print ("connected to server: ", isock)
        return isock


#########################
# Start of execution    #
#########################

#Prepare TCP listener
server_ip_address = 'localhost' #program argument
destination_port = TCP_PORT
sock=connect2sever(server_ip_address,destination_port) #connection ready
if sock == -1:
    #exit game
    print ("Exiting.")
    exit(1)

# Init pre-game
data_stream = str()
rx_queue = queue.Queue(10)
##tx_queue = queue.Queue(10) #defined in gls

#read from keyboard (for now put static values)
# start game:
myPreGame = pre_gameM.player_pre_game(myName="gideon", myGame="4InRow") #create a pregame isntance
myPreGame.start_player_pre_game() #send the starting message to the server




### INIT:
#========
#????game.palyer_game_init()

#######################################
#       MAIN LOOP                     #
#######################################
# loop while not end of game: 
#    transmit_to_server if any
#    receive_from_server()
#    check for error
#    process the received


while gls.gameover==False: #game not over    
    
    #1. Send all messages in tx queue as long as queue is not empty
    while not gls.tx_queue.empty():
        txstr=gls.tx_queue.get_nowait()    
        if debug_level>1: print ('%s: sending "%s"' % (sock.getsockname(),  txstr))      
        sock.send(str.encode(txstr)) #the message must be byte encoded, utf8 is the default
        print ("message sent.")
    
    #2. Receive a single message - ***BLOCKING!***
    try:
        data = sock.recv(1024)
    except socket.error:
        print ("error in socket, should be closed")
        data=""
        #NOTE: Data is not read. socket will be closed later by the next if
    if debug_level>1: print ('%s: received "%s"' % (sock.getsockname(), data))
    
    if not data: #Server closed or error in socket
        print ('closing socket', sock.getsockname())
        sock.close()
        gls.gameover=True
    
    else:   #3. Process the received string
        #XXXno queue is needed because each message is processed.
        rxstr=data.decode("utf-8")
        data_stream, rx_queue = connect_tcp.extract_message(rxstr, data_stream, rx_queue)
        while not rx_queue.empty():
            rx_message=rx_queue.get_nowait()
            if myPreGame.game_status == 1: # pre game, waiting for confirmation from server
                myPreGame.play_player_pre_game(rx_message)
                if myPreGame.game_status == 2:
                    game.palyer_game_init()
                if myPreGame.game_status == -1:
                    gls.gameover = True
                    print("Game rejected. Exiting.")
            elif myPreGame.game_status == 2: # in game
                game.play_player(rx_message) #PROCESS THE MESSAGE
            else: #error
                gls.gameover=True
                print ("Game status error. Exiting.")

#def wait_for_kbd ():
#    a=input ("enter something to continue")
#if debug_level>1: 
#    print ("gameover=",gls.gameover,"wait...")
    #wait_for_kbd()
print ("end.")

