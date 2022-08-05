#this file is used to make tests. It is not used in the API
import chess
import chess.engine
import requests


moves_played=["e4","f5","exf5","g5"]
board=chess.Board()
for i in moves_played:
    try:
        i=chess.Move.from_uci(i)
        board.push(i)
    except:
        board.push_san(i)



engine=chess.engine.SimpleEngine.popen_uci("./stockfish_15")

info = engine.analyse(board, chess.engine.Limit(depth=17))
# print(info["povScore"])
pos_eval=info.get("score").relative
best_move=info.get("pv")[0]
print(str(best_move))
print(pos_eval,type(pos_eval),pos_eval.score())


engine.quit()
print("Quit engine")

session=requests.Session()
endpoint="king_position"
moves=["e2e4","f7f5","e4f5","g7g5"]
data=[]
for i in moves:
    data.append({"new_move":i})

# a=session.get("https://chessyapi.herokuapp.com/reset_board")
# print(a)
# for i in data:
#     req=session.post("https://chessyapi.herokuapp.com/"+endpoint,json=i)
#     print(req.content.decode("utf-8"))
req=session.post("https://chessyapi.herokuapp.com/"+endpoint,json={"side":"white"})
print(req.content.decode("utf-8"))

print(len("https://chessyapi.herokuapp.com/")+len("legal_moves_touched_piece"))