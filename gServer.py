'''
This is the game server module to run
Created on May 21, 2015 @author: Gideon updated on Oct2017

This module is the server part for games, each game is between two remote players.
The purpose of this module is to connect to player pairs, put data received from a player
into a queue which the game object processes, and send traffic that process put in a queue to 
the player the queue is allocated for.
Note that the module is agnostic to the game rules and process.
The server code is heavily based on http://pymotw.com/2/select/ 

The advantage of using select is that it waits for receive/transmit/error events, so no need
to e.g. separately manage the listener and each connection with a client using separated threads,    
'''

TCP_PORT=50002

import select
import socket
import queue
import time

import sys
sys.path.append('../') #this has been added so can be found in cmd window

#from G4InRow.OLDServerMain import s_index

import G4InRow.gls as gls
import G4InRow.roomsM_3 as roomsM
from G4InRow.game import server_game_start
from G4InRow.game import play_server
from G4InRow.game import server_move2game_message
#import G4InRow.game.play_server as game_play_server
import G4InRow.boardClass as boardClass
import G4InRow.connect_tcp as connect_tcp

from G4InRow.pre_gameM import server_pre_game
import G4InRow.pre_gameM as pre_gameM

debug_level=gls.debug_level #0 for no debug, 1 for basic debug, 2 for details


class clients_pool:
    """ Instance name is "clients"
    Allocate an entry in the pool for each client.
    Use of client index - for the use of both the connection manager and the game
    """
    max_clients=gls.max_clients #should be >=  MAX_ROOMS*2
    def __init__(self):
        #self.status = [0 for i in range (self.max_clients)]
        self.status         = [0]*self.max_clients # 0- not allocated, 1-allocated
        self.connection     = [0]*self.max_clients #contains the sockets
        self.client_address = [0]*self.max_clients
        self.croom_number   = [-1]*self.max_clients # for clarity, because there is room number 0
        self.data_stream    = [str()]*self.max_clients #the TCP rx data stream buffer
        #self.tx_queue       = [queue.Queue(10)]*self.max_clients # MOVED TO gls module
        self.game_type   = [0]*self.max_clients #see codes in gls module   # ??? what is it for?
        
    def register_client(self,conn,client_addr,room_num):
        """ It is assumed that there is an available room. Register the client in the pool.
        """
        try:
            index=self.status.index(0) #look for unallocated entry
        except:
            return -1
        if index >= 0: #found
            self.status[index]=1 #allocated
            self.connection[index]      = conn
            self.client_address[index]  = client_addr
            self.croom_number[index]    = room_num
        return index
    
    def get_socket2client (self, connection):
        if gls.debug_level>1: print ("***connection=",connection)
        client_index = self.connection.index(connection)
        room_index =   self.croom_number[client_index]
        return room_index,client_index


def handle_new_connection (connection,client_address):
    """When a new connection request is received, check first if there is room for that new client.
        Process: Find a pre-game room. If found, allocate resources, else return client_index=-1 
        so the caller will close the connection.
        Note that after the pre-game, a client has a connection, so doesn't pass via this procedure,
        but instead goes to "move_to_real_game"
    """
    global srooms,clients

    room_status_found, room_number = srooms.find_available_room(gls.PREGAME_type) #find a  room
    client_index = -1 # Init client_index
    if room_number >= 0: #room found, handle the new client and allocate resources
        client_index = clients.register_client(connection, client_address, room_number)
        srooms.games[room_number] = roomsM.gameC(gls.PREGAME_type) #create a pre-game session instance
        srooms.games[room_number].room_number=room_number #update the session instance with the room number
    return room_number, client_index


def find_room (client_index,game_type): # find a room for 4InRow game
    """When a new connection request is received, check first if there is room for that new client.
        Process: Find a pre-game room. If found, allocate resources, else return client_index=-1
        so the caller will close the connection.
    """
    global srooms, clients

    room_status_found, room_number = srooms.find_available_room(game_type)  # find a room
    if room_number >= 0:  # room found, handle the new client and allocate resources
        #deleted: if srooms.games[room_number].num_of_players = 0
        if room_status_found == 0: #an empty room
            # The first player in the room, create a game
            srooms.games[room_number] = roomsM.gameC(game_type)  # create a game instance
            srooms.games[room_number].room_number = room_number  # update the session instance with the room number
            srooms.games[room_number].players[0]=client_index  #
        elif room_status_found == 1: #a room with already a player
            print (".... just have to add the player to the game ")
            srooms.games[room_number].players[1]=client_index
        #*ADD* else the room number is -1, i.e. no room

    return room_number

def handle_new_player (client_index, game_type):
    """ Find a room and set for the new player, for the pre-game
    """
    global srooms,clients 
      
    room_number = srooms.find_available_room(gls.PREGAME_type) #find a  room
    if room_number >= 0: #room found
        #the client is already registered in clients, so one have just to update it
        srooms.games[room_number] = roomsM.gameC() #create a game instance
        srooms.games[room_number].room_number=room_number #update the session instance with the room number
    return room_number
    
def handle_new_client (room_number, client_index):
    """Add the new client to the room game (room has already been found and allocated in srooms!).
       In the game instance add the clients indexes
       Update room status
       In the clients add the room number
       Note that client_index =0,1,2,3,... while player index is the index WITHIN the game
    """
    global srooms,clients
    #Add player to the game (room) found
    player_index = srooms.games[room_number].add_player(client_index) #add client to game.
    # The player index is the index within the game (0 or 1)
    
    clients.croom_number[client_index] = room_number

    if srooms.games[room_number].game_type == gls.PREGAME_type:
        srooms.room_status[room_number] = 2 #room is full (per client validation)
        # just init the game with the type. No message to process now.
        ### ???
        ###ZZZ ??? server_pre_game(srooms.games[room_number], rx_message_from_client) ### check location ZZZ
        ## CHANGED XXX pre_gameM.server_pre_game_init(srooms.games[room_number]) #no much to do because the clients starts

    ### ZZZ WILL NEVER GET HERE
    else: #real game
        srooms.room_status[room_number] = player_index+1 #first player changes the status to 1,
                                            #the second changes to 2 which designates Full.
        #if room is full (so ready for game) then start the game  
        if  srooms.games[room_number].full(): #this is the second player, start game
            server_game_start(srooms.games[room_number])

def  move_to_real_game (client_index, new_game_type):
    """
    Find a new room.
    Leave the old room and reset/delete what needed.
    Input: The client index and the requested game type
    """

    room_number = find_room(client_index,new_game_type)
    server_move2game_message(client_index) # send the confirmation message to the client
    handle_new_client(room_number, client_index)

    # send the message to the client A
    # ***ADD***
    return room_number

def update_select_outputs(outputs,clients_list):
    """  Check the tx queues and if there is an entry there for a socket, add the socket to the select's
         outputs list, so it will wait for this socket to be ready for write. tx queue is not changed. 
    """
    #outputs: is passed by reference thanks to the append!!!
    #check both clients tx queues
    
    for i in clients_list: #the two clients
        if not gls.server_tx_queues[i].empty():
            # Add the socket we wants to send to, into select's "outputs"
            # the specific socket is found per the index i  
            socket_to_send  = clients.connection[i]
            if debug_level>1: print ("has to send to socket",socket_to_send)  
            if socket_to_send not in outputs:
                # If we want to send to a remote client, we should add the connection to that
                #client to "select's outputs". The select will wait until the connection is ready to send.   
                if debug_level>1: print ("Add to 'outputs' the socket of the connection from which we received "  )
                outputs.append(socket_to_send)

###def reset_game(room_index):
def reset_sockets(room_index):
    global rooms   ### ??? it was deleted. WHY???
    clients_list = srooms.games[room_index].get_players_list()
    
    for i in clients_list: #(if there is a single player, num=1 so only index 0 is processed)
        socket_to_remove= clients.connection[i] #get socket of the index       
        if socket_to_remove in outputs:
            outputs.remove(socket_to_remove) #clean outputs list
        inputs.remove(socket_to_remove) #clean inputs list
        socket_to_remove.close() #close socket
        clients.status[i] = 0 #the client is not allocated   ## ***ADD*** consider reseting the client instance
    
    ### ***Verify***
    ### ***TRY to delete this line*** ### srooms.games[room_index].reset_instance()
    ####srooms.games[room_index] = 0 # Delete the game in the room

def reset_gameC(room_index):
    srooms.games[room_index] = 0
    srooms.room_status[room_index] = 0

def get_room_for_new_connection(connection, client_address):
    room_number, client_index = handle_new_connection(connection, client_address)  # check if there is an available room
    if client_index >= 0:  # there is room for the new client, allocated the player
        handle_new_client(room_number, client_index)
        clients_list = srooms.games[room_number].get_players_list()
        update_select_outputs(outputs, clients_list)  # ???is it needed here?
        inputs.append(connection)  # this is added to the "select" probing process, starting at next while loop
    else:  # no room for the client
        print("no room for the new client from", client_address)
        connection.close()
        # deleted: handle_new_client (game_1,connection,client_address)
    return room_number

#####################################################################################################
# Create a TCP/IP socket
#=======================
#the first socket is just for the listening. The connection with each remote client is handled separately.
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4 TCP socket
server_sock.setblocking(0) #no blocking at socket operation. This is important because the  
#       "select" handles many sockets and events, so they must be non-blocking.                       
# Bind the socket to the port
server_address = ('localhost', TCP_PORT) #the server runs on the local host
print ('starting up on %s port %s' % server_address)
server_sock.bind(server_address)
server_sock.listen(5) #listen for incoming connections on the port defined in "server_address".

#prepare "select"
#===============
inputs = [ server_sock ] # Sockets from which we expect to read: The listening socket and the connection 
    #                 sockets. It is initialized just with the server listening socket.
outputs = [ ] # Sockets to which we expect to write

#global clients 
clients = clients_pool()

#init game
global srooms

srooms= roomsM.Rooms_array() #create the room array


#The main portion of the Server program loops, calling select() to block and for network activity event.
#*******************************************************************************************************
while inputs:
    if debug_level>1: print ("inputs at start of while:  ",inputs) #for debug only
    if debug_level>1: print ("outputs at start of while: ",outputs) #for debug only
    #Example for socket reult:
    #Starting just with the server socket as an input, it looks like: 
    #        <socket.socket fd=268, family=AddressFamily.AF_INET, type=SocketType.SOCK_STREAM, 
    #        proto=0, laddr=('127.0.0.1', 50003)>
    #        It has rx port but not any TX client destination or client port
    
    # Wait (blocking) for at least one of the sockets to be ready for processing
    if debug_level>1: print ( '\nwaiting for the next event...') #for debug only
    readable, writable, exceptional = select.select(inputs, outputs, inputs)
    #***********************************************************************
    #the select returns the sockets for which there is an event 
    #readable - sockets ready for receive  
    #writable - sockets ready to write 
    #exceptional - sockets with some exception (error event)
    
    # Handle "exceptional conditions" fisrt. if there is an error with a socket then close it.
    for s in exceptional:
        print ("handling exceptional condition for", s.getpeername())
        print ("CODE FOR THAT IS NOT DONE....")
        # Stop listening for input on / sending to this connection
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()
    
    # Handle "inputs" events, i.e. ready to receive 
    #==============================================
    for s in readable: 
        if debug_level>1: print ("Process the event for: ",s) #debug
        #There are two types of sockets in readable: Either the server that listens,
        #or a connection with a remote traffic that want so send traffic 
        if s is server_sock: #"server" is the server socket created above that just listens
            # *** A NEW CONNECTION ***
            # An event on this socket indicates a remote client wants to connect and server socket is
            # ready to accept a connection
            connection, client_address = s.accept() #get a connection socket & its address={IP address, port}
            connection.setblocking(0) #non blocking on recv for this socket - events are handled by select.
            print ('new connection from', client_address) #Note that the created connection (socket) has                                         #different ID and has also a remote address.   
            if debug_level>2: print ("new connection: ",connection) #debug 
            
            if debug_level>2: print ("inputs after appending the new connection:",inputs) #Debug. 
            #Any new connection socket is added to the "inputs" to be watched by "select" 

            room_number = get_room_for_new_connection(connection, client_address)
            """"###[***CHANGE***] The aboved replaced the following.
            ### that class gets the connection and client address as inputs
            room_number, client_index = handle_new_connection(connection, client_address) # check if there is an available room
            if client_index >=0 : # there is room for the new client, allocated the player
                handle_new_client(room_number, client_index)
                clients_list =  srooms.games[room_number].get_players_list()
                update_select_outputs(outputs, clients_list)#???is it needed here? 
                inputs.append(connection) #this is added to the "select" probing process, starting at next while loop
            else: #no room for the client
                print ("no room for the new client from",client_address)
                connection.close()
            #deleted: handle_new_client (game_1,connection,client_address)
            """
            # check if need to ADD (maybe done above): If room_number == -1 : # EXIT...

        else: #readable returns the connection socket, so ready to receive data from this socket
            if debug_level>1: print ("receive data...")
            try: 
                data = s.recv(1024)
            except socket.error:
                print ("error in socket, should be closed")
                data=""
                #NOTE: Data is not read. socket will be closed later by the next if 
            
            if data: # A readable client socket has data
                rx_str_from_client = data.decode("utf-8") #read the received message and convert/decode to string
                if debug_level>2: print ('********* received "%s" from %s' % (data, s.getpeername()))
                #the data received may be a multiple / fraction of a message, so extract the message from the
                # aggregated data stream.
                # Having the received socket ID, get the client index and room number
                room_index,client_index = clients.get_socket2client(s)
                if gls.debug_level>1: print ("now processing game", room_index)
                if client_index==-1: print ("BUG ServerMain readable of",s)

                # The received frame is not sync with the message, but is a data stream. Therefore get update that
                # datastream with the received frame and extract a full message if any:
                clients.data_stream[client_index] , srooms.games[room_index].rx_queue = \
                    connect_tcp.extract_message(rx_str_from_client, \
                    clients.data_stream[client_index] , srooms.games[room_index].rx_queue)
                                
                #if there is complete message in the queue extract and process it
                if not srooms.games[room_index].rx_queue.empty(): #???????? why queue is not per client???
                    rx_message_from_client= srooms.games[room_index].rx_queue.get_nowait()

                    ### process the message:
                    """ ZZZ
                    """
                    if   srooms.games[room_index].game_type == gls.PREGAME_type:
                        pre_game_state = server_pre_game(srooms.games[room_index],rx_message_from_client)
                        if pre_game_state == 10 :#when ends allocate the client to a real game room
                            #clear the previous room
                            #del srooms.games[room_index]
                            srooms.reset_room(room_index) #reset the room state and game object?
                            room_index = move_to_real_game(client_index, gls.G4INROW_type ) #the new(!) room number
                            if room_index == -1: #no room found
                                print ("Error, no room found. Rejecting new client")
                                ### ***ADD*** The following may share the same function
                                ### Send a rejection message to the client
                                ### Then close socket
                                exit(2)

                    elif srooms.games[room_index].game_type == gls.G4INROW_type:
                        play_server(srooms.games[room_index], rx_message_from_client)
                    
                    #As a result of game processing, there may be clients which we want to send to.
                    #So check tx queues and update select's "outputs" list accordingly.

                    clients_list =  srooms.games[room_index].get_players_list()
                    update_select_outputs(outputs, clients_list) 
            
            #A readable socket without data available is from a client that has disconnected, 
            # and the stream is ready to be closed
            else: #Event from readable socket with no data. Indicates the peer has closed the connection
                #print ("empty data: = ",data) #debug2
                # Interpret empty result as "peer has closed connection"
                print ('closing', client_address, 'after reading no data (peer has closed connection)')
                #find whether it is one of the active players
                room_index, client_index = clients.get_socket2client(s)
                if client_index != -1:
                    print ("An active client has closed his connection... game over!")
                    srooms.games[room_index].gameover = True
                    #### reset_game(room_index) ***CHANGED***
                    #gls.gameover=True #due to error, although the game has not gracefully ended
                    #this will cause game reset at the end of the loop
                    
                else: #client is not part of a game
                    # Stop listening for input on the connection
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
            
    #OUTPUTS:
    ########
    #If there is data in the queue for a connection, the next message is sent. 
    #Otherwise, the connection is removed from the list of output connections so that the next
    # time through the loop select() does not indicate that the socket is ready to send data.
    # Handle outputs:
    for s in writable:
        if debug_level>1: print ("there is a writable, i.e. the peer is ready to get data.")
        #find who's socket is s:
        room_index, client_index=clients.get_socket2client(s) #the index of the clients and its tx_queue
        try: #instead of "try" I could simply check if the queue is empty...
            next_msg = gls.server_tx_queues[client_index].get_nowait()
        except queue.Empty:
            # No messages waiting so stop checking for writability for this socket.
            if debug_level>1: print ('output queue for', s.getpeername(), 'is empty')
            outputs.remove(s)
        else:#get from queue provides a string to send
            if debug_level>1: print ('sending "%s" to %s' % (next_msg, s.getpeername()))
            s.send(str.encode(next_msg) ) #send the message to the remote client
            #time.sleep(0.2)
            #NOTE: the socket is not deleted from outputs because the queue
            #to send may be not empty. So only on queue empty (the "except"
            #that appears above) the socket will be removed from outputs!

    #if gameover then reset game, provided that there is no data to send!
    #note that this is done only for player's socket, not for the listener socket
    if s != server_sock: # The event was from an already connected client
        room_index, client_index=clients.get_socket2client(s)
        if srooms.games[room_index].gameover == True: #GAME IS OVER
            #reset game only after tx queues are empty
            queue_empty=True #init value for the check
            clients_list =  srooms.games[room_index].get_players_list()
            for i in clients_list: #the two clients
                if not gls.server_tx_queues[i].empty():
                    queue_empty=False
            if queue_empty==True: #nothing to send, close all game connections and reset game
                reset_sockets(room_index) # close all connections
                reset_gameC(room_index)
                ###replaced:   reset_game(room_index) #close all connections and reset game
                ###replaced:   srooms.games[room_index] = 0
                ###replaced:   srooms.room_status[room_index] = 0
    
        if debug_level>1: print ("End of events. Loop again.")

print ("end.")

