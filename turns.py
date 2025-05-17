def showPressTurns(turns):
    icons = {
        'full': '◉',
        'half': '◎',
        'used': ' '
    }
    return " ".join(icons[t] for t in turns)

def initPressTurns(party_size):
    return ['full'] * party_size

def useTurn(turns):
    for i in range(len(turns)):
        if turns[i] in ['full', 'half']:
            used = turns[i]
            turns[i] = 'used'
            return used
    return None

def addHalfTurn(turns):
    for i in range(len(turns)):
        if turns[i] == 'full': 
            turns[i] = 'half'
            return
        
def addTurn(turns, usedTurn = None):
   if usedTurn == "full":
        turns.append('half')

def passTurn(turns):
    for i in range(len(turns)):
        if turns[i] == "full":
            turns[i] = "half"
            return
        elif turns[i] == "half":
            turns[i] = "used"
            return

def loseTurn(turns):
    for i in reversed(range(len(turns))):
        if turns[i] in ['full', 'half']:
            turns[i] = 'used'
            return