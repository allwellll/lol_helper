 #-*-coding:GBK -*- 
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from lcu_driver import Connector
connector = Connector()


import json
class GameMember:
    def __init__(self, game):
        self.name = game['person']['player']['summonerName']
        self.accountid = game['person']['player']['accountId']
        self.championId = game['detail']['championId']
        self.kills = game['detail']['stats']['kills']
        self.deaths = game['detail']['stats']['deaths']
        self.assists = game['detail']['stats']['assists']
    
        

class Game:
    def __init__(self, game_json):
        self.participantIdentities = game_json.get('participantIdentities')
        self.participants = game_json.get('participants')
        self.origin_members = [{ 'person': x[0],
                         'detail': x[1]
                        } for x in zip(self.participantIdentities, self.participants)]
        self.members = [GameMember(x) for x in self.origin_members]
    
    
class Player:
    def __init__(self, data):
        if 'accountId' in data:
            self.accountId = int(data['accountId'])
        else:
            self.accountId = -1
        self.name = data['summonerName']
        self.kda = -1
        self.max_kill = -1
    
    async def load(self, connection):
        #print(f"load: {self.name}\t{self.accountId}")
        if self.accountId != -1:
            #print ("hit")	
            self.kda, self.max_kill = await get_player_info(connection, self.accountId)
        


async def get_history(connection):
    his = await connection.request('GET', '/lol-career-stats/v1/summoner-games/06712581-6f34-5dab-97bf-50f046cb8166')
    data = await his.json()
    # print(data)


async def get_recent_games(connection, account_id):
    game_data = await connection.request('get', f"/lol-match-history/v3/matchlist/account/{account_id}?begIndex=0&endIndex=3")
    game_data = await game_data.json()
#     print(game_data)
#     print(game_data['games']['games'])
    games = [ x['gameId'] for x in game_data['games']['games']]
    #print(f"games ids {games}")
    return games

async def get_game_info(connection, gameid):
    data = await connection.request('get', f"/lol-match-history/v1/games/{gameid}")
    data = await data.json()
    
    n = len(data['participantIdentities'])
    #for i in range(n):
    #    print(f"{data['participantIdentities'][i]['player']['summonerName']}\t{data['participants'][i]['stats']['win']}")
    game = Game(data)
    return game
    

async def get_person_info(connection, accountId = 4006324864):
    games = await get_recent_games(connection, accountId)
    game_detail = []
    for gid in games:
        game = await get_game_info(connection, gid)
        target = [x for x in game.members if x.accountid == accountId]
        if target:
            # print(f"{target[0].name}\t{target[0].kills}\t{target[0].deaths}\t{target[0].assists}")
            info = target[0]
            kda = (info.kills + info.assists) * 1.0 / max(info.deaths, 0.5)
            game_detail.append([info.kills, info.deaths, info.assists, kda])
    return game_detail


async def get_all_player(connect):
    data = await connection.request('get', f"/lol-gameflow/v1/session")
    data = await data.json()
    
    if 'gameData' not in data:
        print("not gaming")
        return
    
    team1 = data['gameData']['teamOne']
    team2 = data['gameData']['teamTwo']
    
    team1_players = [Player(x) for x in team1]
    team2_players = [Player(x) for x in team2]
    for p in team1_players:
        p.load(connect)
    for p in team2_players:
        p.load(connect)
    team1_players.sorted(key = lambda x : x.kda)
    team2_players.sorted(key = lambda x : x.kda)
    
# @connector.ready
async def get_player_info(connection, accountId = 4006324864):
    person_info = await get_person_info(connection, accountId)
    avg_kda =  round(sum([x[3] for x in person_info]) * 1.0 / (len(person_info)), 2)
    max_kill = max(x[1] for x in person_info)
    # print(f"avg_kda:{avg_kda}\tmax_kill:{max_kill}")
    return [avg_kda, max_kill]

@connector.ready
async def get_all_player(connect):
    data = await connect.request('get', f"/lol-gameflow/v1/session")
    data = await data.json()
    
    team1 = data['gameData']['teamOne']
    team2 = data['gameData']['teamTwo']
    
    team1_players = [Player(x) for x in team1]
    team2_players = [Player(x) for x in team2]
    for p in team1_players:
        await p.load(connect)
        #print(p.name, p.kda)
    for p in team2_players:
        await p.load(connect)
    team1_players.sort(key = lambda x : x.kda)
    team2_players.sort(key = lambda x : x.kda)
    print("以下数据根据最近三场比赛统计:")
    print(f"team1 上等马:{team1_players[-1].name}\t历史平均kda:{team1_players[-1].kda}\t历史最高击杀:{team1_players[-1].max_kill}")
    print(f"team2 上等马:{team2_players[-1].name}\t历史平均kda:{team2_players[-1].kda}\t历史最高击杀:{team2_players[-1].max_kill}")
    print("")
    print(f"team1 下等马:{team1_players[0].name}\t历史平均kda:{team1_players[0].kda}\t历史最高击杀:{team1_players[0].max_kill}")
    print(f"team1 下等马:{team2_players[0].name}\t历史平均kda:{team2_players[0].kda}\t历史最高击杀:{team2_players[0].max_kill}")

print("本软件仅为个人调研, 使用LOL 公开LCUAPI, 符合英雄联盟的使用规范。未做传播等用途。如有出现任何问题，概不负责\n")
connector.start()

a = input()
print("exiting")


    



