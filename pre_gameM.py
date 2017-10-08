'''
Created on Jun 5, 2015 @author: Gideon, updated on Oct 2017

The player:
    Initializes the pre_game, sends his info to the server, and on getting confirmation starts the game.
The server:
    Initialize the game class with PREGAME type.
    When a new client is connected, the server processes it as for a pre-game.
       It sends a TBD message to the client and then sends the start of game message.

'''

#import G4InRow.roomsM_3 as roomsM
import G4InRow.gls as gls
import G4InRow.tlv as tlvM

class player_pre_game:
    """
    Game status state machine:
     On init: 0
     After the connection is accepted and the game is init, move to 1.
     When a frame is received from the server, if it is a confirmation then move to game.
    """

    def __init__(self,myName="myName",myGame="4InRow"):
        self.game_status = 0 # 0=not started 1=started 10=end
        self.myName= myName
        self.myGame= myGame

    def start_player_pre_game(self):
        if gls.debug_level >1: print ("Sending my info")
        tlv_to_send = tlvM.tlv(tlvM.my_info,self.myName,self.myGame) #
        str_to_send = tlv_to_send.tlv2str()
        gls.tx_queue.put_nowait(str_to_send)
        self.game_status = 1
        return self.game_status

    def play_player_pre_game(self,rxstr):
        # the "game" is simply receiving a message and moving to the game status AS IF we received a real confimation
        rxtlv = tlvM.tlv()
        rxtlv.str2tlv(rxstr)  # convert to fill up the tlv fields
        if gls.debug_level>0: print ("Pre-game message from server:",rxstr)
        if rxtlv.tlv_value1 == "Okay" and rxtlv.tlv_value2 == "4InRow":
            print ("4InRow confirmed.")
            self.game_status = 2 #signifies that the real game has started
        else:
            print ("Game request rejected.")
            self.game_status = -1 #
        return self.game_status


#class server_pre_game:
    """ Array of pre game for each client the server processes
    """
#    def __init__(self):
#        return
#
#    def server_pre_game (room_index, rx_message_from_client):
#        #





#def server_pre_game_init(pre_game):
#    """currently no init
#    """
#    return



# Server part
#==============


def server_pre_game(pre_game,rx_message_from_client): #get a game object and the message
    """let's start with auto /dummy confirmation
    pre_game is the game_instance (srooms.games[room_index]) 
    """
    if pre_game.game_type == gls.PREGAME_type: #wait for cliebt authentication
        #process the message from the client
        clients_list = pre_game.get_players_list()  # the client index of the player
        client_index = clients_list[0] # there must be a single player
        rxtlv = tlvM.tlv()
        rxtlv.str2tlv(rx_message_from_client)
        if rxtlv.tlv_type == tlvM.my_info:
            #get the required game name
            if rxtlv.tlv_value2 == "4InRow":
                print ("A client requests 4InRow")
                #pre_game. *** ADDZZZ"
        else: #error
            print ("error in message from client")

    if True:
        pre_game.game_state = 10 #successful authentication
        #now move it to a real game

    """    
    if pre_game.game_state==10: #move to the real game
        #delete the old game and empty the room. Then find a new empty room /add to an existig one

        pre_game_room_number = pre_game.room_number #get the old room number
        
        #del pre_game
        ###pre_game.room_status = 0 # the room is empty again
        
        #set the client to a new room per game
        # XXXXX client_index=pre_game.players[0]
        new_game_type = gls.G4INROW_type #in the future may be requested by client
        result = move_to_real_game (client_index,new_game_type)
    """
    return pre_game.game_state


# ********* testing *********
if __name__ == '__main__':
    # Client test
    myPreGame = player_pre_game(myName="gideon", myGame="4InRow")  # create a pregame isntance
    myPreGame.start_player_pre_game()  # send the starting message to the server
    rx_message = '0,10,Okay,4InRow'
    myPreGame.play_player_pre_game(rx_message)
    print ("Status= ",myPreGame.game_status)


