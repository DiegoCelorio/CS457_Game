
import logging
import random

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Game:
    def __init__(self):
        self.players = []
        self.started = False
        self.host = None
        self.questions = [
            {"question": "What is the capital of france?", "answer": "Paris"},
            {"question": "What is 2 + 2", "answer": "4"},
            {"question": "Who wrote Odyssey?", "answer": "Homer"},
            {"question": "What is the largest country by landmass?", "answer": "Russia"},
            {"question": "What is the most popular sport in the US", "answer": "Football"}
        ]
        random.shuffle(self.questions)
        self.current_index = 0
        self.players_correct = []
        self.correct_answers = {}


    def start_game(self, username):
        if not self.started:
            self.started = True
            self.host = username
            self.players.append(username)
            logger.info(f"Game started by {username}")
            return f"Game started by {username}. First question: {self.get_current_question()}"

        else:
            return "Game already started"
    

    def join_game(self, username):
        if username not in self.players:
            self.players.append(username)
            logger.info(f"{username} successfully joined the game")
            return f"{username} successfully joined the game" 
        
        else:
            return f"{username} is already in game"
    

    def get_current_question(self):
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]["question"]
        else:
            print("No more questions!")


    def submit_answer(self, username, answer):
        if username not in self.players:
            return f"{username} is not in game"
        
        correct_answer = self.questions[self.current_index]["answer"]
        if answer.strip().lower() == correct_answer.strip().lower():
            if username not in self.players_correct:
                self.players_correct.append(username)
            if username not in self.correct_answers:
                self.correct_answers[username] = 0
            self.correct_answers[username] += 1

            return f"Answer submitted by {username} is correct"
        
        return f"Answer submitted by {username} is incorrect"
    

    def next_question(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.players_correct = [] #empty out so ready for each round
            return self.get_current_question()
        else:
            self.started = False
            logger.info("Quiz is over")
            return f"Quiz is over! Check leaderboard"


    def get_leaderboard(self):
        leaderboard = sorted(
            self.correct_answers.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return leaderboard
    
    def get_players_correct(self):
        return self.players_correct

    
    def broadcast(self, message, sender=None):
        return