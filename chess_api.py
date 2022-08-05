from xml.dom.expatbuilder import theDOMImplementation
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, Column,Integer,String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
import chess
import chess.engine
import ast


app=Flask(__name__)

Base=declarative_base()
class Chess_DB(Base):
	__tablename__="chess_table"

	the_id=Column("id",Integer,primary_key=True)
	current_fen=Column("current_fen",String)
	engine_depth=Column("engine_depth",Integer)
	moves_played=Column("moves_played",String)


engine=create_engine("sqlite:///chess.db")
Base.metadata.create_all(bind=engine)
Session=sessionmaker(bind=engine)

chess_engine=chess.engine.SimpleEngine.popen_uci("./stockfish_15")

def update_board_info(current_fen=None,engine_depth=None,moves_played=None):
	session=Session()

	chess=Chess_DB()
	if current_fen!=None:
		session.query(Chess_DB).filter(chess.the_id == 0).update({'current_fen': current_fen})
		session.commit()
		
		task = session.query(Chess_DB).get(0)
		task.current_fen = current_fen
	if engine_depth!=None:
		session.query(Chess_DB).filter(chess.the_id == 0).update({'engine_depth': engine_depth})
		session.commit()

		task = session.query(Chess_DB).get(0)
		task.engine_depth = engine_depth
	
	if moves_played!=None:
		session.query(Chess_DB).filter(chess.the_id == 0).update({'moves_played': moves_played})
		session.commit()

		task = session.query(Chess_DB).get(0)
		task.moves_played = moves_played

	session.commit()
	session.close()

def get_depth():
	session=Session()

	everything=session.query(Chess_DB).all()
	for i in everything:
		the_depth=i.engine_depth
	session.close()
	
	try:
		return int(the_depth)
	except ValueError:
		print("Value error trying to return engine depth in DB")
		return 10

def get_fen():
	moves_played=""
	session=Session()

	everything=session.query(Chess_DB).all()
	for i in everything:
		moves_played=i.moves_played

	session.close()

	if not moves_played:
		moves_played=[]
	else:
		moves_played=ast.literal_eval(moves_played) #now this is a list instead of a string

	board=chess.Board()
	for i in moves_played:
		i=chess.Move.from_uci(i)
		in_san=board.san(i)
		board.push_san(in_san)

	return board.fen(),moves_played

def add_move(the_move):
	_,moves_played=get_fen()
	moves_played.append(the_move)
	update_board_info(moves_played=str(moves_played))

def is_move_legal():
	_,moves_played=get_fen()
	board=chess.Board()
	for i in moves_played:
		try:
			i=chess.Move.from_uci(i)
			board.push_san(board.san(i))
		except ValueError:
			print("Illegal move")
			return str(False)
	return str(True)

def check_checkmate():
	the_fen,_=get_fen()
	board=chess.Board(the_fen)
	return str(board.is_checkmate())

def check_check():
	the_fen,_=get_fen()
	board=chess.Board(the_fen)
	return str(board.is_check())

def game_result():
	the_fen,_=get_fen()
	board=chess.Board(the_fen)
	return board.result()

def board_reset():
	update_board_info(moves_played="")

def get_whose_turn():
	the_fen,_=get_fen()
	board=chess.Board(the_fen)
	if board.turn:
		return "white"
	return "black"

def get_the_last_move(notation="san"):
	_,moves_played=get_fen()
	if not moves_played:
		return ""
	if notation!="san":
		return moves_played[-1]

	last_one=""
	board=chess.Board()
	for i in moves_played:
		i=chess.Move.from_uci(i)
		last_one=board.san(i)
		board.push_san(last_one)
	
	return last_one

def get_number_of_moves():
	_,moves_played=get_fen()
	if (len(moves_played)%2==0):
		return str(len(moves_played)/2)
	return str(int(len(moves_played)/2)+1)

def get_all_moves(notation="san"):
	_,moves_played=get_fen()
	if notation!="san":
		return str(moves_played)
	board=chess.Board()
	record=[]
	for i in moves_played:
		i=chess.Move.from_uci(i)
		record.append(board.san(i))
		board.push_san(board.san(i))
	return str(record)

def undo_last_move():
	_,moves_played=get_fen()
	if not moves_played:
		return ""
	else:
		update_board_info(moves_played=str(moves_played[:-1]))
		return moves_played[-1]

def check_if_is_capture():
	_,moves_played=get_fen()
	board=chess.Board()
	captured=False
	for i in moves_played:
		i=chess.Move.from_uci(i)
		captured=board.is_capture(i)
		board.push_san(board.san(i))
	return str(captured)

def check_if_is_castling():
	_,moves_played=get_fen()
	board=chess.Board()
	castling=False
	for i in moves_played:
		i=chess.Move.from_uci(i)
		castling=board.is_castling(i)
		board.push_san(board.san(i))
	return str(castling)

def piece_legal_moves(the_input):
	_,moves_played=get_fen()
	board=chess.Board()
	for i in moves_played:
		i=chess.Move.from_uci(i)
		board.push_san(board.san(i))

	legal_moves=[str(i) for i in list(board.legal_moves)]
	num=chess.parse_square(the_input)


	legal_squares=[]
	attacked_squares=board.attacks(num)
	square_nums=list(attacked_squares)

	for i in square_nums:
		legal_squares.append(chess.square_name(i))
	for index,i in enumerate(legal_squares):
		legal_squares[index]="{}{}".format(the_input,i)

	the_piece=board.piece_at(num)
	if str(the_piece).lower()=="p": #a pawn
		legal_squares.extend([the_input+the_input[0]+str(int(the_input[1])+1),
		the_input+the_input[0]+str(int(the_input[1])+2),the_input+the_input[0]+str(int(the_input[1])-1),
		the_input+the_input[0]+str(int(the_input[1])-2)])

	for index,i in enumerate(legal_moves):
		if len(i)==5:
			legal_moves[index]=i[0:4]

	real_legal_moves=list(set(legal_squares) & set(legal_moves))

	return str(real_legal_moves)

def get_king_square(side):
	_,moves_played=get_fen()
	board=chess.Board()
	for i in moves_played:
		i=chess.Move.from_uci(i)
		board.push_san(board.san(i))
	one,two=board.king(chess.WHITE),board.king(chess.BLACK)
	three,four=chess.square_name(one),chess.square_name(two)
	if side.lower()=="white":
		return str(three)
	return str(four)
	
def position_to_fen(pos_array):
	pos_array=ast.literal_eval(pos_array)
	split_array=_split_list(pos_array,16)
	for index,i in enumerate(split_array):
		i.reverse()
		split_array[index]=i

	new_arr=[]
	for i,k in zip(split_array[0::2], split_array[1::2]):
		new_arr+=k
		new_arr+=i

	my_fen=_get_fen_pieces(new_arr)
	try:
		chess.Board(my_fen)
	except Exception as e:
		return "Error: {}".format(e)

	update_board_info(current_fen=my_fen)

	return my_fen



def _get_fen_pieces(board):
	"""
	Read board and return piece locations in fen format.
	"""
	ret = None
	cnt = 0  # counter for successive empty cell along the row
	save = []  # temp container

	board = board[::-1]  # reverse first

	for i, v in enumerate(board):
		if v == ' ':
			cnt += 1

		# sum up the successive empty cell and update save
			if cnt > 1:
				save[len(save)-1] = str(cnt)
			else:
				save.append(str(cnt))  # add
		else:
			save.append(v)  # add
			cnt = 0  # reset, there is no successive number

		if (i+1)%8 == 0:  # end of row
			save.append('/')
			cnt = 0

	ret = ''.join(save)  # convert list to string
	ret=ret[:-1]
	ret+=' w KQkq - 0 1'

	return ret

def _split_list(alist, wanted_parts=8):
	length = len(alist)
	return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
			for i in range(wanted_parts) ]

def start_engine():
	global chess_engine
	chess_engine=chess.engine.SimpleEngine.popen_uci("./stockfish_15")

def stop_engine():
	try:
		chess_engine.quit()
		del chess_engine
	except Exception as e:
		print("Exception quitting engine ",e)

def get_best_move():
	the_fen,_=get_fen()
	new_board=chess.Board(the_fen)
	try:
		info = chess_engine.analyse(new_board, chess.engine.Limit(depth=get_depth()))
		best_move=str(info.get("pv")[0])
		return best_move
	except NameError as e:
		print("Error. Probably the engine object doesn't exist. ",e)
		stop_engine()
		start_engine()
		get_best_move()
	except Exception as e:
		print("Other unknown error: ",e)

def change_engine_depth(depth):
	update_board_info(engine_depth=int(depth))


#a comment
@app.route("/",methods=["GET","POST"])
def index():
	#this is an example of how to determine whether a request is GET or POST
	if request.method=="POST": 
		val_posted=request.get_json()
		return jsonify({"value posted":val_posted}),200
	else: #a get request
		return "<h1>Welcome to the Chessy API</h1>"

@app.route("/update_board",methods=["POST"])
def update_board():
	data = request.get_json()
	new_move = data.get('new_move', '')
	add_move(new_move)
	return jsonify({"move": new_move})

@app.route("/board_fen")
def board_fen():
	return jsonify({"fen": get_fen()[0]})

@app.route("/is_legal")
def is_legal():
	return jsonify({"legal": is_move_legal()})

@app.route("/is_checkmate")
def is_checkmate():
	return jsonify({"checkmate": check_checkmate()})

@app.route("/is_check")
def is_check():
	return jsonify({"check": check_check()})

@app.route("/check_result")
def check_result():
	return jsonify({"result": game_result()})

@app.route("/reset_board")
def reset_board():
	board_reset()
	return jsonify({"reset": "game_reset"})

@app.route("/whose_turn")
def whose_turn():
	return jsonify({"turn": get_whose_turn()})

@app.route("/last_move",methods=["POST"])
def last_move():
	data = request.get_json()
	the_type = data.get('the_type', '')
	return jsonify({"last_move": get_the_last_move(the_type)})

@app.route("/num_moves")
def num_moves():
	return jsonify({"number_of_moves": get_number_of_moves()})

@app.route("/all_moves",methods=["POST"])
def all_moves():
	data = request.get_json()
	the_type = data.get('the_type', '')
	return jsonify({"all_moves": get_all_moves(the_type)})

@app.route("/undo_move")
def undo_move():
	return jsonify({"move_undone": undo_last_move()})

@app.route("/is_capture")
def is_capture():
	return jsonify({"is_capture": check_if_is_capture()})

@app.route("/is_castling")
def is_castling():
	return jsonify({"is_castling": check_if_is_castling()})

@app.route("/legal_moves_touched_piece",methods=["POST"])
def legal_moves_touched_piece():
	data = request.get_json()
	square = data.get('square', '')
	return jsonify({"piece_legal_moves": piece_legal_moves(square)})

@app.route("/king_position",methods=["POST"])
def king_position():
	data = request.get_json()
	side = data.get('side', '')
	return jsonify({"king_square": get_king_square(side)})

@app.route("/board_to_fen",methods=["POST"])
def board_to_fen():
	data = request.get_json()
	curr_board = data.get('board', '')
	return jsonify({"fen": position_to_fen(curr_board)})

@app.route("/engine_interface/<string:option>")
def engine_interface(option):
	if option=="start":
		start_engine()
		return jsonify({"engine":"start"})
	elif option=="stop":
		stop_engine()
		return jsonify({"engine":"stop"})
	elif option=="best_move":
		return jsonify({"engine":get_best_move()})
	else:
		return jsonify({"Error":"Option {} is not recognized".format(option)})
	
@app.route("/engine_depth",methods=["POST"])
def engine_depth():
	data = request.get_json()
	depth = data.get('depth', '')
	change_engine_depth(depth)
	return jsonify({"depth": depth})


if __name__=="__main__":

	try:
		session=Session()
		chess_obj=Chess_DB()
		chess_obj.the_id=0
		chess_obj.current_fen="None"
		chess_obj.engine_depth=10
		chess_obj.moves_played=""
		session.add(chess_obj)
		session.commit()
		session.close()
	except IntegrityError:
		print("Error trying to make the DB. Most likely it is already created :)")

	app.run(host='0.0.0.0',debug=True)

