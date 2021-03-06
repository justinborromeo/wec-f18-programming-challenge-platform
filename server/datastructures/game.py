# current timestamp
# board state

# a 2d array that stores either players or walls
from .models import Games, Game_state, Teams
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

class Game:
    def build_grid(self, _size): 
        """ Build a dictionary grid. The key will be a position string (e.g. "1,1")
        the value will be what is occupying the space (options for that are:
        'wall', player_id1, player_id2, 'trail', and '' (for nothing)."""
        _size += 2 # to allow for walls to be added on the periphery
        game_grid = {}
        for i in range(_size):
            for j in range(_size):
                val = ""
                if i == 0 or j == 0 or i == _size-1 or j == _size-1:
                    val = "wall"
                game_grid.update({str(i)+","+str(j):val})                
        return game_grid
    
    def __init__(self, _size):
        self.game_grid = self.build_grid(_size)
        self.started = False
        self._size = _size
        self.team1 = None
        self.team2 = None
        
        ############## create DB session and add game to it
        engine = engine = create_engine('postgresql://postgres:q1w2e3@localhost/WEC.db')
        Session = sessionmaker(bind=engine) # need to execute these lines to create a queriable session
        self.session = Session()
        try:
            self.current_game = Games(team1_id=None,team2_id=None)
            self.session.add(self.current_game)
            self.session.commit()
            self.game_state = Game_state(game_id=self.current_game.id, turn=0, game_state=self.game_grid)
            self.session.add(self.game_state)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(e)
        #################
        

    def spawn_player(self, team_id):
        row = int(self._size/2)
        col = 2
        position = 1
        if self.game_grid[str(row)+","+str(col)] != "": #if the first player has already been put in
            col = self._size - 1
            position = 2
        logging.info("Player " + str(team_id) + " spawned at " + str(row) + ","  + str(col))
        self.game_grid.update({str(row)+","+str(col):team_id})
        ##################
        try:
            if position == 1:
                self.current_game.team1_id = team_id
                self.team1 = self.session.query(Teams).filter_by(team_id=team_id).first()
                self.team1.games_played += 1
                self.session.add(self.team1)
            else:
                self.current_game.team2_id = team_id
                self.team2 = self.session.query(Teams).filter_by(team_id=team_id).first()
                self.team2.games_played += 1
                self.session.add(self.team2)
            
            self.game_state.game_state = self.game_grid
            self.session.add(self.current_game)
            self.session.add(self.game_state)
            
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(e)
        ###################
        

    def start(self):
        self.started = True
        
    def finish(self, winning_team_id):
        try:
            self.current_game.is_complete = True
            """if winning_team_id == self.team1.id:
                self.team1.games_won += 1
                self.session.add(self.team1)
            elif winning_team_id == self.team2.id:
                self.team2.games_won += 1
                self.session.add(self.team2)
            """# else team won = None
            self.current_game.victor = winning_team_id
            self.session.add(self.current_game)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(e)
        # The below should not be needed but for some reason the commented out code
        # above does not work. So this hack will have to do.
        if winning_team_id == None:
            return # if no team wins, add no winning team ids
        engine = engine = create_engine('postgresql://postgres:q1w2e3@localhost/WEC.db')
        Session = sessionmaker(bind=engine)
        session1 = Session()
        try:
            winner = session1.query(Teams).filter_by(team_id=winning_team_id).first()
            winner.games_won += 1
            session1.add(winner)
            session1.commit()
        except Exception as e:
            print(e)
            session1.rollback()
        session1.close()

    def stop(self):
        self.started = False
        self.session.close() # close the connection to the db

    def reset_game(self):
        self.game_grid = self.build_grid(self._size)
        self.started = False
        self.team1 = None
        self.team2 = None
        
        ############## create DB session and add game to it
        engine = engine = create_engine('postgresql://postgres:q1w2e3@localhost/WEC.db')
        Session = sessionmaker(bind=engine) # need to execute these lines to create a queriable session
        self.session = Session()
        try:
            self.current_game = Games(team1_id=None,team2_id=None)
            self.session.add(self.current_game)
            self.session.commit()
            self.game_state = Game_state(game_id=self.current_game.id, turn=0, game_state=self.game_grid)
            self.session.add(self.game_state)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(e)
        #################
        
    def update_game_state(self, update):
        """ Updates the game_grid with the inputed update variable. update should
        be a dictionary containing as many updates as desired (separated by commas) in the format:
        {"i,j":val, "1,2":team_id, ...} where i and j are the row and column position to be updated
        and val is the new string value to give that position. """
        self.game_grid.update(update)
        ##################
        try:
            self.game_state.game_state = self.game_grid
            self.game_state.turn += 1
            self.game_state.game_state
            self.session.add(self.game_state)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(e)
        ##################