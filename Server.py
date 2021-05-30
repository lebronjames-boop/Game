import socket
import threading
import Yaniv
import time

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
print(SERVER)
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
YANIV_MESSAGE = 'yaniv'
ASAF_MESSAGE = 'asaf'
NOT_YOU_YANIV_MESSAGE = 'NYYANIV'


queue = []
clients = []
all_names = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def handle_client(conn, addr):
    print(f"THREAD [NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        data = conn.recv(1024).decode(FORMAT)
        if data == DISCONNECT_MESSAGE:
            connected = False
        queue.append(data)

    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}\n")
    count = 0
    while count < 2:
        conn, addr = server.accept()
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"\n[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        count += 1

        new_name = wait_for_msg('PN')[0][:-1]  # new name from every connected client
        print("new name in server looks like:", new_name)
        all_names.append(new_name)
        print("all names are:", all_names)

        message = f'{count}${new_name}' # sends the number of players and the last name connected
        broadcast(clients, message, 'WFP')  # number of players connected

    print(f"[FINISHED {count} CONNECTIONS]\n")

def wait_for_msg(header):
    while True:
        while len(queue) == 0:
            pass
        i = -1
        for item in queue:
            i += 1
            if item.split('&')[0] == header:
                msg = queue[i]
                queue.remove(msg)
                print("msg is", msg)
                msg = msg.split('&')[1:]
                print(msg)
                # print('msg-->', msg)
                return msg

def all_cards_used(game):
    '''the function gets a game type Yaniv
    and returns false if there are still cards in stack
    otherwise, returns true and clears the used cards into a new stack'''
    for card in game.in_use:
        if card == 0:
            return False
    # if not returned yet, means the stack is empty
    for card_num in game.out_of_use:
        game.in_use[card_num] = 0
    return True

def broadcast(clients, message, header):
    for client in clients:
        client.send(f'BROADCAST&{header}&{message}'.encode(FORMAT))

def turn(whos_turn, player, all_cards, game, last_turn_cards):
    '''the function  handles a turn. it ends only when
    the player has made a valid turn'''
    p_cards = all_cards[whos_turn]
    time.sleep(0.5)
    last_turn_cards = list_to_string(last_turn_cards)
    #print("last turn cards len:", len(last_turn_cards))
    #print("last turn cards:", last_turn_cards)
    time.sleep(1)
    player.send(f'LC&{last_turn_cards}'.encode(FORMAT))  # stringed
    print(f"[LAST TURN CARD SENT:] {last_turn_cards}")

    chosen_cards = wait_for_msg(header='CC')[0]
    print("message:", chosen_cards)
    if chosen_cards == 'VY':  # valid yaniv
        all_cards_string = ''
        for i in range(0, len(all_cards) - 1):
            stringed_cards = list_to_string(all_cards[i])
            all_cards_string += stringed_cards + '$'
        stringed_cards = list_to_string(all_cards[-1])
        all_cards_string += stringed_cards

        broadcast(clients, all_cards_string, 'PCY')
        return YANIV_MESSAGE

    #broadcast(clients, f'{chosen_cards}', 'ULC')

    chosen_cards = chosen_cards.split(' ')
    game.going_out(chosen_cards)
    for i in range(0, len(chosen_cards)):
        print("p_cards are", p_cards)
        p_cards.remove(int(chosen_cards[i]))
    print(f"[UPDATED CARDS BEFORE L/D] {p_cards}")

    last_or_deck = wait_for_msg('DL')
    print('heeeeeeeeeeeeeeeey', last_or_deck)
    print("[CHOSE]", last_or_deck)
    if last_or_deck[0] == 'DECK':
        new_card = game.deal(1)[0]
        p_cards.append(int(new_card))

    elif last_or_deck[0] == 'LAST':
        new_card = last_or_deck[1]
        print("the last card chosen:", new_card)
        game.out_of_use.remove(int(new_card))
        p_cards.append(int(new_card))

    cards_mes = list_to_string(p_cards)
    time.sleep(1)
    player.send(f'NC&{cards_mes}'.encode(FORMAT))
    print(f"[UPDATED CARDS FINAL] {p_cards}")
    return chosen_cards

def list_to_string(card_list):
    p_cards_str = ''
    for card in card_list[:-1]:
        p_cards_str += str(card) + ' '
    p_cards_str += str(card_list[-1])
    return p_cards_str

def game(clients):

    all_cards = []
    all_sums = []

    #broadcast(clients, all_names, 'FN')  # final names
    for i in range(0, len(clients)):
        all_sums.append(5)

    game = Yaniv.Yaniv()# New game created

    players = 0
    for player in clients:
        p_cards = game.deal(5)
        print("p_cards immedeatly after dealing:", p_cards) # dealing cards in lists
        all_cards.append(p_cards)  # adding to all cards

        #cards_str = list_to_string(p_cards)
        print(f"[P{players + 1}]'S CARDS] {p_cards}")

        cards_stringed = list_to_string(p_cards)
        all_names_stringed = list_to_string(all_names)

        print("stringed is", cards_stringed)
        player.send(f'SGC&{cards_stringed}${all_names_stringed}'.encode(FORMAT))
        print('message sent OH:', f'SGC&{cards_stringed}${all_names_stringed}')
        time.sleep(1)
        players += 1

    who_starts = game.who_starts(len(clients) - 1)

    last_cards = game.deal(1)
    print("first last cards are:", last_cards)
    game.going_out(last_cards)

    match = True
    while match:
        last_cards_string = list_to_string(last_cards)
        all_sums_string = list_to_string(all_sums)
        all_sums_for_send = []

        # if who_starts == 0:
        #     for i in range(0, len(all_sums) - 1):
        #         all_sums_for_send.append(all_sums[i])
        # else:
        #     last_index = who_starts - 1
        #     if last_index == 0:
        #         for i in range(1, len(all_sums)):
        #             all_sums_for_send.append(all_sums[i])
        #     else:
        #         for i in range(last_index + 1, len(all_sums)):
        #             all_sums_for_send.append(all_sums[i])
        #         for i in range(0, last_index):
        #             all_sums_for_send.append(all_sums[i])

        # if who_starts != 0:  # if the current player is not the last in the clients list
        #     print("if ")
        #     for i in range((who_starts - 1) + 1, len(all_sums)):
        #         all_sums_for_send.append(all_sums[i])
        #     for i in range(0, (who_starts - 1)):
        #         all_sums_for_send.append(all_sums[i])
        # else:  # the current p[layer is the last client in the list
        #     print('else')
        #     for i in range(0, len(all_sums) - 1):
        #         all_sums_for_send.append(all_sums[i])

        #print("all sums:", all_sums, '\nall sums to send:', all_sums_for_send)
        #all_sums_string = list_to_string(all_sums_for_send)
        broadcast(clients, f'{last_cards_string}${all_sums_string}', 'ULC')  # ULC = Updated Last Cards

        last_cards = turn(who_starts, clients[who_starts], all_cards, game, last_cards)

        # after this line, the last cards saves the current turn chosen cards.
        all_sums[who_starts] -= len(last_cards)
        all_sums[who_starts] += 1

        #time.sleep(0.5)
        #broadcast(clients, all_sums, 'AS')  # All Sums
        who_starts += 1

        if last_cards == YANIV_MESSAGE:
            who_starts -= 1
            match = False

        if who_starts == (len(clients)):
            who_starts = 0

        is_empty_stack = all_cards_used(game)
        if is_empty_stack:
            broadcast(clients, '\n[[[ReNeWiNg StAcK]]]\n', 'RS')  # rs = renewing stack
            last_cards = game.deal(1)
            game.going_out(last_cards)

    # now sending for all
    winner = [game.sum_cards(all_cards[who_starts]), who_starts]  # [sum, index]
    for i in range(0, len(clients)):
        if i != who_starts:  # everything except the "winner"
            #clients[i].send(NOT_YOU_YANIV_MESSAGE.encode(FORMAT))
            if game.sum_cards(all_cards[i]) <= winner[0]:  # if someones sum is smaller or equal to "winner"
                winner = [game.sum_cards(all_cards[i]), i]

    if winner[1] == who_starts:  # the caller for yaniv is indeed the winner
        for i in range(0, len(clients)):
            if i != who_starts:
                clients[i].send("LC&EML".encode(FORMAT))  # final end message
            elif i == who_starts:
                clients[i].send("EM&CONGRATULATIONS YOU are the WINNER".encode(FORMAT))
    else:  # there is an asaf
        for i in range(0, len(clients)):
            if i == winner[1]:
                clients[i].send("LC&EMA".encode(FORMAT))  # final end message assaf, the final winner
            elif i == who_starts:
                clients[i].send("EM&Oops, seems like you got ASAFed...".encode(FORMAT))
            else:
                clients[i].send("LC&EML".encode(FORMAT))


print("[STARTING] server is starting...")
start()
print("now what")
game(clients)

#game_between_two(clients[0], clients[1])
