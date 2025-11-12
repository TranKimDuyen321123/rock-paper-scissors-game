

def get_result(choice1, choice2):
    """Return result for player1 relative to player2:
    'win', 'lose', or 'draw'
    """
    c1 = choice1.lower().strip()
    c2 = choice2.lower().strip()
    valid = {'rock','paper','scissors'}
    if c1 not in valid or c2 not in valid:
        # Thay vì raise ValueError, ta có thể dùng 'draw' nếu muốn game tiếp tục, 
        # nhưng giữ nguyên logic cũ để dễ debugging.
        raise ValueError('Invalid choice') 
        
    if c1 == c2:
        return 'draw'
        
    rules = {'rock':'scissors', 'scissors':'paper', 'paper':'rock'}
    return 'win' if rules[c1] == c2 else 'lose'
    