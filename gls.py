'''
Created on May 10, 2015 @author: Gideon

Contains globals + init that has to be moved from here!
'''
import queue

#GAME SCALE
#==========
max_clients=4
MAX_ROOMS = 5

debug_level=0 #0 for no debug, 1 for basic debug, 2 for details

SOM="[[[" #Start of message delimiter
EOM="]]]" #End of message delimiter
sub_delimiter = "--" #TLV sub string delimiter

#game types
#=============
PREGAME_type   = 1 #the pre-game stage
G4INROW_type   = 2


#for players (not server)
tx_queue=queue.Queue(4) #used only by the player
my_role = "" #A client can have role of "A" or "B" (for server="S" but actually not used).
gameover=False
turn_is = "A"

#for server only
server_tx_queues= [queue.Queue(10) for i in range(max_clients)] #List of queues at server, one per each client

print ("gls has been imported...")

    