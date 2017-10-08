'''
Created on Jun 5, 2015 @author: Gideon

Room_array: Instanciated as "srooms"
    A rooms array with room status and the games it has.
gameC:
    the game
    When a game is created, a gameC object is created and added to the room e.g. by
      "srooms.games[room_number] = roomsM.gameC(gls.PREGAME_type)"
    The game object within the room array can be reset simply by setting it to 0 integer

'''

import sys
sys.path.append('../') #this has been added so can be found in cmd window

import queue

import G4InRow.gls as gls
import G4InRow.boardClass as boardClass

#----------------------------------------------------------------------------

class Rooms_array: #instance name = srooms
    """ contains the rooms, with the room status and info.
        
    When a new connection is received:
    - Check if there is a room which is not full. 
    if there is a room which is not full 
        Gets its index.
    if this index has no game class initiated, then create and init
    if the index has a game then validate the new player as done in prev version  
        
    """
    max_rooms = gls.MAX_ROOMS
    def __init__(self):
        self.room_status    = [0 for i in range (self.max_rooms)] # status= 0(Empty), 1(available), 2(full)
        self.games          = [0 for i in range (self.max_rooms)] # games is a class (inherits from Room_session) set by gServer.
                                                  
    def find_available_room(self, game_type):
        """
        if found return the index of the room. Look first for an already initialized room 
        if no room then return -1
        """
        room_index = -1 #init
        if game_type == gls.PREGAME_type:
            if self.room_status.count(0) > 0: #look for an empty room (value=0)
                room_index = self.room_status.index(0) #the empty room number
                room_status_found = 0
            else: room_status_found = -1 #no room found
        elif game_type == gls.G4INROW_type: #G4InRow game        
            if self.room_status.count(1) > 0: #look first for a non-empty yet available room (value=1)
                room_index = self.room_status.index(1)
                room_status_found = 1
            elif self.room_status.count(0) > 0: #look for an empty room (value=0)
                room_index = self.room_status.index(0)
                room_status_found = 0
            else: room_status_found = -1 #no room found
        return room_status_found, room_index
    
    def reset_room(self,room_number):
        self.room_status[room_number] = 0
        self.games [room_number] = 0

#============================================================================
#----------------------------------------------------------------------------

class Room_Session:
    """ Room instance with a session  that can be pre-game or any game
        Session types are defined in gls module
    """
    def __init__(self):
        self.num_of_players=0
        self.room_number=-1 #no room number before allocated
        self.rx_queue = queue.Queue(10)        
    
    def add_player(self,client_index):
        ''' returns the player index 0 or 1 if succeeds to add the client to the game
            else return -1
            Note that in pre-game the index is always 0
        '''
        #if self.full(): print ("BUG if full")
        print ("clinet index type=",type(client_index))
        self.players[self.num_of_players] = client_index         
        self.num_of_players +=1
        
        if self.num_of_players==1: print("The first client/player is connected")
        else:                      print ("The second player is connected, start game")
       
        return self.num_of_players-1 #return the player index 0 or 1
        
    def get_player_index(self,s):
        return self.sockets.index(s)
    
    def get_players_list(self):
        plist = []
        for i in range(self.num_of_players):
            plist.append(self.players[i])
        return plist
        ##return self.players
        
    def get_client_index (self,player_index):
        return self.players[player_index]

    def reset_common (self): # ???
        self.num_of_players=0
        self.room_number=-1 #no room number before allocated
        self.rx_queue.queue.clear()

#----------------------------------------------------------------------------

class pre_gameCXXX(Room_Session):
    
    max_players =1
    def __init__(self):
        Room_Session.__init__(self)
        self.game_type= gls.PREGAME_type #init to client validation process
        self.state = 0 # start validation state
        self.players = [0] #will contain the client index
    
    def full (self):
        if self.num_of_players == self.max_players:
            return True
        else: 
            return False

    #def reset_instance (self):
    #    self.session_type= gls.PREGAME_type #init to client validation process
    #    self.state = 0 # start validation state
    #    self.players = 0

#----------------------------------------------------------------------------

class gameC(Room_Session):
    #index - 0 for "A", 1" for "B"
    #XXX max_players =2
        
    def __init__(self,game_type):
        Room_Session.__init__(self)
        self.game_type = game_type
        self.game_state = 0
        self.max_players = 2 #??? fails ottherwise
        if self.game_type == gls.PREGAME_type:
            self.max_players =1
        else: # =gls.G4INROW_type
            max_players = 2
        self.players   =[0 for i in range (self.max_players)] #list of  players' client(!) indices
        if self.game_type == gls.G4INROW_type:
            self.turn_is = "A"
            self.board = boardClass.Board()
            self.gameover=False
    
    def full (self):
        if self.num_of_players == self.max_players:
            return True
        else: 
            return False    
        
    def swap_turn(self):
        if self.turn_is=="A": 
            self.turn_is="B" 
        else: self.turn_is="A"   

    def get_player_turn2index (self):
        if self.turn_is=="A": return 0
        else: return 1

    def reset_instance(self):
        Room_Session.reset_common(self)
        self.game_state = 0
        self.players   =[0 for i in range (self.max_players)]
        self.turn_is = "A"
        self.board = boardClass.Board()
        self.gameover=False


