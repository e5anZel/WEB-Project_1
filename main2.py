import os
import io
import re
import random
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
import chess
from chess import Board
from PIL import Image, ImageDraw, ImageFont
from config import API_TOKEN, DATABASE_URL, STOCKFISH_PATH
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, declarative_base
import chess.engine
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.BigInteger, unique=True)
    wins = sa.Column(sa.Integer, default=0)
    losses = sa.Column(sa.Integer, default=0)
    draws = sa.Column(sa.Integer, default=0)

engine = sa.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
class ChessGame(StatesGroup):
    selecting_source = State()
    selecting_target = State()
    waiting_text_move = State()

current_games = {}

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♟ Играть (с человеком)", callback_data="play")],
        [InlineKeyboardButton(text="🤖 Играть с ботом", callback_data="play_vs_bot")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📖 Правила", callback_data="rules")]
    ])

def game_keyboard(selected_square=None, with_text_input=False):
    buttons = []
    for row in range(8):
        row_buttons = []
        for col in range(8):
            square = chess.square_name(chess.square(col, 7 - row))
            emoji = "⬜" if (row + col) % 2 == 0 else "⬛"
            if selected_square and square == selected_square:
                emoji = "🟨"
            row_buttons.append(
                InlineKeyboardButton(
                    text=emoji,
                    callback_data=f"square_{square}"
                )
            )
        buttons.append(row_buttons)
    control_row = [
        InlineKeyboardButton(text="🏳 Сдаться", callback_data="resign"),
        InlineKeyboardButton(text="💡 Подсказка", callback_data="hint"),
    ]
    if selected_square:
        control_row.insert(0, InlineKeyboardButton(text="🔄 Выбрать заново", callback_data="reselect"))
    if with_text_input:
        control_row.append(InlineKeyboardButton(text="⌨️ Ввести ход текстом", callback_data="text_move"))
    buttons.append(control_row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_move_from_to(move):
    return chess.square_name(move.from_square), chess.square_name(move.to_square)
#в этой функции мы генерируем изображение доски(сначало пустое, а потом заполняем квадратами)
def generate_chess_board_image(board, selected_square=None, last_move=None, in_check=False):
    square_size = 60
    board_size = 8 * square_size
    image = Image.new('RGBA', (board_size, board_size), 'bisque')
    draw = ImageDraw.Draw(image)
    light = '#f0d9b5'
    dark = '#b58863'
    selected = '#ffe066'
    last_from = '#9ecfff'
    last_to = '#c8ff9e'
    check_color = '#ff6e6e'

    from_sq, to_sq = (None, None)
    if last_move:
        from_sq = chess.square_file(last_move.from_square), 7 - chess.square_rank(last_move.from_square)
        to_sq = chess.square_file(last_move.to_square), 7 - chess.square_rank(last_move.to_square)
    check_king_sq = None
    if in_check:
        check_king_sq = board.king(board.turn)
        check_king_coords = (chess.square_file(check_king_sq), 7 - chess.square_rank(check_king_sq))
    for row in range(8):
        for col in range(8):
            x = col * square_size
            y = row * square_size
            color = dark if (row + col) % 2 else light
            square = chess.square(col, 7 - row)
            square_name = chess.square_name(square)
            if selected_square and square_name == selected_square:
                color = selected
            if last_move:
                if (col, row) == from_sq:
                    color = last_from
                if (col, row) == to_sq:
                    color = last_to
            if in_check and check_king_sq is not None and (col, row) == check_king_coords:
                color = check_color
            draw.rectangle([x, y, x + square_size, y + square_size], fill=color)

    piece_filenames = {
        'P': 'wp.png', 'R': 'wr.png', 'N': 'wn.png', 'B': 'wb.png',
        'Q': 'wq.png', 'K': 'wk.png', 'p': 'bp.png', 'r': 'br.png',
        'n': 'bn.png', 'b': 'bb.png', 'q': 'bq.png', 'k': 'bk.png'
    }
    piece_images = {}
    pieces_dir = os.path.join(os.path.dirname(__file__), "pieces")
    for k, fname in piece_filenames.items():
        piece_path = os.path.join(pieces_dir, fname)
        piece_images[k] = Image.open(piece_path).convert("RGBA").resize((44, 44))
    for row in range(8):
        for col in range(8):
            square = chess.square(col, 7 - row)
            piece = board.piece_at(square)
            if piece:
                px = col * square_size + (square_size - 44) // 2
                py = row * square_size + (square_size - 44) // 2
                image.alpha_composite(piece_images[piece.symbol()], (px, py))
    font = None
    try:
        font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
        font = ImageFont.truetype(font_path, 14)
    except Exception:
        font = ImageFont.load_default()
    for i, l in enumerate("abcdefgh"):
        draw.text((i * square_size + 3, board_size - 18), l, fill="black", font=font)
    for i in range(8):
        draw.text((3, i * square_size + 3), str(8 - i), fill="black", font=font)

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr
#изначально тут было 14(чтобы не забыть)
def get_best_move(board, depth=18):
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            result = engine.play(board, chess.engine.Limit(depth=depth))
            move = result.move
            san = board.san(move)
            return move, san
    except Exception:
        moves = list(board.legal_moves)
        if moves:
            move = random.choice(moves)
            return move, board.san(move)
        return None, None

def get_caption(board, last_move=None, last_actor=None, last_move_san=None, last_move_uci=None):
    caption = ""
    if last_actor and last_move:
        from_sq, to_sq = get_move_from_to(last_move)
        actor = "Вы" if last_actor == "human" else "Бот"
        caption += f"{actor} походил из {from_sq} в {to_sq} ({last_move_san}, {last_move_uci})\n"
    if board.is_checkmate():
        caption += f"♚ Мат! Игра окончена. Победа {'белых' if not board.turn else 'чёрных'}!"
    elif board.is_stalemate():
        caption += "Пат! Ничья."
    elif board.is_check():
        caption += f"Шах! Ход {'белых' if board.turn else 'чёрных'}."
    else:
        caption += f"Ход {'белых' if board.turn else 'чёрных'}!"
    if board.is_game_over() and board.result() == "1/2-1/2":
        caption += " Ничья."
    return caption

async def show_board(message, board, selected_square=None, last_move=None, last_actor=None, last_move_san=None, last_move_uci=None, with_text_input=False):
    in_check = board.is_check()
    img_bytes = generate_chess_board_image(board, selected_square, last_move, in_check)
    caption = get_caption(board, last_move, last_actor, last_move_san, last_move_uci)
    await message.answer_photo(
        types.BufferedInputFile(img_bytes.read(), "chess_board.png"),
        caption=caption,
        reply_markup=game_keyboard(selected_square, with_text_input)
    )

async def start_game(user_id, is_vs_bot=False):
    board = Board()
    current_games[user_id] = {
        'board': board,
        'selected_square': None,
        'last_move': None,
        'last_actor': None,
        'last_move_san': None,
        'last_move_uci': None,
        'is_vs_bot': is_vs_bot,
        'human_color': chess.WHITE,
        'awaiting_bot_move': False
    }
    return board

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    session = SessionLocal()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    if not user:
        user = User(user_id=message.from_user.id)
        session.add(user)
        session.commit()
    session.close()
    await message.answer(
        "♟ Добро пожаловать в Chess Bot!\n"
        "Выберите режим игры: с человеком или с ботом. Можно делать ходы кнопками или текстом (например: e2e4).",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == 'play')
async def process_play(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    board = await start_game(callback_query.from_user.id, is_vs_bot=False)
    await show_board(callback_query.message, board, with_text_input=True)
    await state.set_state(ChessGame.selecting_source)

@dp.callback_query(F.data == 'play_vs_bot')
async def process_play_vs_bot(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    board = await start_game(callback_query.from_user.id, is_vs_bot=True)
    color = random.choice([chess.WHITE, chess.BLACK])
    current_games[callback_query.from_user.id]['human_color'] = color
    current_games[callback_query.from_user.id]['awaiting_bot_move'] = False
    if color == chess.WHITE:
        await show_board(callback_query.message, board, with_text_input=True)
        await state.set_state(ChessGame.selecting_source)
    else:
        game_data = current_games[callback_query.from_user.id]
        move, san = get_best_move(board)
        if move:
            move_uci = move.uci()
            board.push(move)
            game_data['last_move'] = move
            game_data['last_actor'] = "bot"
            game_data['last_move_san'] = san
            game_data['last_move_uci'] = move_uci
        await show_board(
            callback_query.message, board, last_move=move, last_actor="bot",
            last_move_san=san, last_move_uci=move.uci(), with_text_input=True
        )
        await state.set_state(ChessGame.selecting_source)

@dp.callback_query(F.data == 'stats')
async def show_stats(callback_query: types.CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter(User.user_id == callback_query.from_user.id).first()
    await callback_query.message.answer(
        f"📊 Ваша статистика:\n"
        f"🏆 Побед: {user.wins}\n"
        f"❌ Поражений: {user.losses}\n"
        f"🤝 Ничьих: {user.draws}"
    )
    session.close()

@dp.callback_query(F.data == 'rules')
async def show_rules(callback_query: types.CallbackQuery):
    rules = (
        "♟ <b>Правила шахмат</b>:\n"
        "1. Играют два игрока, по очереди.\n"
        "2. Цель — поставить мат королю соперника.\n"
        "3. Ходы фигур:\n"
        "   • Пешка — вперед\n"
        "   • Конь — буквой Г\n"
        "   • Слон — по диагонали\n"
        "   • Ладья — по прямой\n"
        "   • Ферзь — по прямой и диагонали(Universal)\n"
        "   • Король — на одну клетку в любую сторону(Ферзь/8)\n"
        "4. Можно делать ходы кнопками или текстом (например: e2e4, e7e5, g1f3)\n"
        "5. Подсказка покажет лучший ход по мнению движка Stockfish!"
    )
    await callback_query.message.answer(rules, parse_mode="HTML")

@dp.callback_query(F.data == 'reselect')
async def reselect_source(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id in current_games:
        current_games[user_id]['selected_square'] = None
        board = current_games[user_id]['board']
        last_move = current_games[user_id].get('last_move')
        last_actor = current_games[user_id].get('last_actor')
        last_move_san = current_games[user_id].get('last_move_san')
        last_move_uci = current_games[user_id].get('last_move_uci')
        await show_board(callback_query.message, board, last_move=last_move, last_actor=last_actor, last_move_san=last_move_san, last_move_uci=last_move_uci, with_text_input=True)
        await state.set_state(ChessGame.selecting_source)
    await callback_query.answer("Выберите фигуру заново!")

@dp.callback_query(F.data == 'text_move')
async def enable_text_move(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Введите ход в сообщении(например: e2e4 или e7e5)")
    await callback_query.message.answer("Введите ход (например: e2e4 или e7e5):")
    await state.set_state(ChessGame.waiting_text_move)

def parse_user_move(text):
    txt = text.lower().replace(" ", "")
    if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", txt):
        return txt
    match = re.fullmatch(r"([a-h][1-8])([a-h][1-8])([qrbn]?)", txt)
    if match:
        return "".join(match.groups())
    return None

@dp.message(ChessGame.waiting_text_move)
async def handle_text_move(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in current_games:
        await message.answer("Нет активной игры! Нажмите /start")
        await state.clear()
        return
    game_data = current_games[user_id]
    board = game_data['board']
    is_vs_bot = game_data.get('is_vs_bot', False)
    human_color = game_data.get('human_color', chess.WHITE)
    if is_vs_bot and board.turn != human_color:
        await message.answer("Сейчас ходит бот. Пожалуйста, дождитесь своего хода, будьте терпеливыми")
        return
    move_str = parse_user_move(message.text)
    if not move_str:
        await message.answer("Некорректный ввод. Введите, например, e2e4, e7e5 или g1f3")
        return
    move = chess.Move.from_uci(move_str)
    if move not in board.legal_moves:
        await message.answer("Нелегальный ход! Попробуйте снова")
        return
    move_san = board.san(move)
    move_uci = move.uci()
    board.push(move)
    game_data['last_move'] = move
    game_data['last_actor'] = "human"
    game_data['last_move_san'] = move_san
    game_data['last_move_uci'] = move_uci
    if board.is_game_over():
        session = SessionLocal()
        user = session.query(User).filter(User.user_id == user_id).first()
        msg = None
        if board.is_checkmate():
            if is_vs_bot:
                if human_color == (not board.turn):
                    user.wins += 1
                    msg = f"♚ Мат! Победа игрока!"
                else:
                    user.losses += 1
                    msg = f"♚ Мат! Победа бота!"
            else:
                if not board.turn:
                    #user.wins += 1
                    msg = f"♚ Мат! Победа белых!"
                else:
                    #user.losses += 1
                    msg = f"♚ Мат! Победа чёрных!"
        elif board.is_stalemate():
            user.draws += 1
            msg = "Пат! Ничья"
        elif board.is_insufficient_material():
            user.draws += 1
            msg = "Ничья: недостаточно фигур"
        elif board.is_seventyfive_moves() or board.is_fivefold_repetition():
            user.draws += 1
            msg = "Ничья по правилам"
        session.commit()
        session.close()
        await show_board(message, board, last_move=move, last_actor="human", last_move_san=move_san, last_move_uci=move_uci)
        del current_games[user_id]
        await state.clear()
        return
    if is_vs_bot:
        game_data['awaiting_bot_move'] = True
        move_bot, san = get_best_move(board)
        if move_bot:
            move_bot_san = board.san(move_bot)
            move_bot_uci = move_bot.uci()
            board.push(move_bot)
            game_data['last_move'] = move_bot
            game_data['last_actor'] = "bot"
            game_data['last_move_san'] = move_bot_san
            game_data['last_move_uci'] = move_bot_uci
            if board.is_game_over():
                session = SessionLocal()
                user = session.query(User).filter(User.user_id == user_id).first()
                msg = None
                if board.is_checkmate():
                    user.losses += 1
                    msg = "♚ Мат! Победа бота!"
                elif board.is_stalemate():
                    user.draws += 1
                    msg = "Пат! Ничья"
                elif board.is_insufficient_material():
                    user.draws += 1
                    msg = "Ничья: недостаточно фигур"
                elif board.is_seventyfive_moves() or board.is_fivefold_repetition():
                    user.draws += 1
                    msg = "Ничья по правилам"
                session.commit()
                session.close()
                await show_board(message, board, last_move=move_bot, last_actor="bot", last_move_san=move_bot_san, last_move_uci=move_bot_uci)
                del current_games[user_id]
                await state.clear()
                return
        game_data['awaiting_bot_move'] = False
        await show_board(message, board, last_move=move_bot, last_actor="bot", last_move_san=move_bot_san, last_move_uci=move_bot_uci, with_text_input=True)
        await state.set_state(ChessGame.selecting_source)
    else:
        await show_board(message, board, last_move=move, last_actor="human", last_move_san=move_san, last_move_uci=move_uci, with_text_input=True)
        await state.set_state(ChessGame.selecting_source)

@dp.callback_query(F.data.startswith('square_'))
async def process_square(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    square = callback_query.data.split('_')[1]
    if user_id not in current_games:
        await callback_query.answer("Начните новую игру!")
        return
    game_data = current_games[user_id]
    board = game_data['board']
    last_move = game_data.get('last_move')
    is_vs_bot = game_data.get('is_vs_bot', False)
    human_color = game_data.get('human_color', chess.WHITE)
    current_state = await state.get_state()

    if is_vs_bot and board.turn != human_color:
        await callback_query.answer("Сейчас ходит бот( не вы :^) ). Дождитесь своего хода!")
        return

    if current_state == ChessGame.selecting_source.state:
        piece = board.piece_at(chess.parse_square(square))
        if piece and piece.color == board.turn:
            game_data['selected_square'] = square
            last_move = game_data.get('last_move')
            last_actor = game_data.get('last_actor')
            last_move_san = game_data.get('last_move_san')
            last_move_uci = game_data.get('last_move_uci')
            await show_board(
                callback_query.message, board, selected_square=square, last_move=last_move,
                last_actor=last_actor, last_move_san=last_move_san, last_move_uci=last_move_uci, with_text_input=True
            )
            await state.set_state(ChessGame.selecting_target)
        else:
            await callback_query.answer("Выберите свою фигуру!")
    elif current_state == ChessGame.selecting_target.state:
        if not game_data.get('selected_square'):
            await callback_query.answer("Выберите фигуру заново!")
            return
        source = game_data['selected_square']
        move = chess.Move.from_uci(f"{source}{square}")
        if move in board.legal_moves:
            move_san = board.san(move)
            move_uci = move.uci()
            board.push(move)
            game_data['last_move'] = move
            game_data['last_actor'] = "human"
            game_data['last_move_san'] = move_san
            game_data['last_move_uci'] = move_uci
            game_data['selected_square'] = None
            if board.is_game_over():
                session = SessionLocal()
                user = session.query(User).filter(User.user_id == user_id).first()
                msg = None
                if board.is_checkmate():
                    if is_vs_bot:
                        if human_color == (not board.turn):
                            user.wins += 1
                            msg = "♚ Мат! Победа игрока!"
                        else:
                            user.losses += 1
                            msg = "♚ Мат! Победа бота!"
                    else:
                        if not board.turn:
                            #user.wins += 1
                            msg = "♚ Мат! Победа белых!"
                        else:
                            #user.losses += 1
                            msg = "♚ Мат! Победа чёрных!"
                elif board.is_stalemate():
                    user.draws += 1
                    msg = "Пат! Ничья"
                elif board.is_insufficient_material():
                    user.draws += 1
                    msg = "Ничья: недостаточно фигур"
                elif board.is_seventyfive_moves() or board.is_fivefold_repetition():
                    user.draws += 1
                    msg = "Ничья по правилам"
                session.commit()
                session.close()
                await show_board(
                    callback_query.message, board, last_move=move, last_actor="human", last_move_san=move_san, last_move_uci=move_uci
                )
                del current_games[user_id]
                await state.clear()
                return
            if is_vs_bot:
                move_bot, san = get_best_move(board)
                if move_bot:
                    move_bot_san = board.san(move_bot)
                    move_bot_uci = move_bot.uci()
                    board.push(move_bot)
                    game_data['last_move'] = move_bot
                    game_data['last_actor'] = "bot"
                    game_data['last_move_san'] = move_bot_san
                    game_data['last_move_uci'] = move_bot_uci
                    if board.is_game_over():
                        session = SessionLocal()
                        user = session.query(User).filter(User.user_id == user_id).first()
                        msg = None
                        if board.is_checkmate():
                            user.losses += 1
                            msg = "♚ Мат! Победа бота!"
                        elif board.is_stalemate():
                            user.draws += 1
                            msg = "Пат! Ничья"
                        elif board.is_insufficient_material():
                            user.draws += 1
                            msg = "Ничья: недостаточно фигур"
                        elif board.is_seventyfive_moves() or board.is_fivefold_repetition():
                            user.draws += 1
                            msg = "Ничья по правилам"
                        session.commit()
                        session.close()
                        await show_board(
                            callback_query.message, board,
                            last_move=move_bot, last_actor="bot", last_move_san=move_bot_san, last_move_uci=move_bot_uci
                        )
                        del current_games[user_id]
                        await state.clear()
                        return
                await show_board(
                    callback_query.message, board,
                    last_move=move_bot, last_actor="bot", last_move_san=move_bot_san, last_move_uci=move_bot_uci, with_text_input=True
                )
                await state.set_state(ChessGame.selecting_source)
            else:
                await show_board(
                    callback_query.message, board,
                    last_move=move, last_actor="human", last_move_san=move_san, last_move_uci=move_uci, with_text_input=True
                )
                await state.set_state(ChessGame.selecting_source)
        else:
            await callback_query.answer("Нелегальный ход!")

@dp.callback_query(F.data == 'resign')
async def resign_game(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id in current_games:
        session = SessionLocal()
        user = session.query(User).filter(User.user_id == user_id).first()
        user.losses += 1
        session.commit()
        session.close()
        del current_games[user_id]
    await callback_query.answer("Вы сдались 🏳")
    await callback_query.message.answer("Игра окончена, вы сдались.")
    await state.clear()

@dp.callback_query(F.data == 'hint')
async def give_hint(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in current_games:
        await callback_query.answer("Нет активной игры!")
        return
    board = current_games[user_id]['board']
    move, san = get_best_move(board)
    if not move:
        await callback_query.answer("Нет доступных ходов!")
        return
    move_uci = move.uci()
    from_sq, to_sq = get_move_from_to(move)
    msg = f"💡 Лучший ход: {san} ({from_sq} -> {to_sq})"
    await callback_query.answer(msg, show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
