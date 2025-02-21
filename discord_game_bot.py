import discord
from discord.ext import commands, tasks
import random
import os
import time
import asyncio
import json
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

# 데이터 파일 경로
data_file = 'user_money.json'

# 가상 화폐 시스템 설정
user_money = {}  # 유저 ID: 가상돈

# 게임 결과를 저장할 리스트 추가
game_results = []

# 봇 시작 시 데이터 불러오기
def load_data():
    global user_money
    try:
        with open(data_file, 'r') as f:
            user_money = json.load(f)
    except FileNotFoundError:
        user_money = {}

# 봇 종료 시 데이터 저장
def save_data():
    with open(data_file, 'w') as f:
        json.dump(user_money, f)

# 도박 시스템 설정
last_dojang_time = {}

@client.event
async def on_ready():
    print(f'봇이 {client.user}로 로그인했습니다!')

@client.event
async def on_disconnect():
    save_data()
    print("봇이 종료되었습니다. 자산 데이터가 저장되었습니다.")    

# 배너 메시지 보내기 위한 함수
def create_embed_message(title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="이 메시지는 봇에서 자동으로 생성되었습니다.")
    return embed

# !돈줘 명령어
@client.command()
async def 돈줘(ctx):
    user_id = ctx.author.id
    current_time = time.time()

    # 30분 제한 체크
    if user_id in last_dojang_time and current_time - last_dojang_time[user_id] < 60:
        await ctx.send(embed=create_embed_message("오류", "1분이 지나지 않았습니다. 잠시 후 다시 시도해 주세요.", discord.Color.red()))
        return

    # 돈 지급
    user_money[user_id] = user_money.get(user_id, 0) + 30000
    last_dojang_time[user_id] = current_time
    await ctx.send(embed=create_embed_message("돈 지급", f"{ctx.author.mention}님에게 30,000원이 지급되었습니다!", discord.Color.green()))

# 도박 확률과 결과 보기 버튼을 위한 버튼 클래스
class GambleView(View):
    def __init__(self, bet, ctx):
        super().__init__()
        self.bet = bet
        self.ctx = ctx
        self.probability = random.randint(1, 100)  # 1에서 100 사이의 확률 값

    @discord.ui.button(label="결과 보기", style=discord.ButtonStyle.green)
    async def gamble_result(self, button: Button, interaction: discord.Interaction):
        result = random.choice(["성공", "실패"])

        if result == "성공":
            user_money[self.ctx.author.id] = user_money.get(self.ctx.author.id, 0) + (self.bet * 2)
            result_message = f"{self.ctx.author.mention}님, 도박에 성공하여 {self.bet * 1}원을 받았습니다!"
        else:
            user_money[self.ctx.author.id] = user_money.get(self.ctx.author.id, 0) - self.bet
            result_message = f"{self.ctx.author.mention}님, 도박에 실패하여 {self.bet}원이 차감되었습니다."

        await self.ctx.send(embed=create_embed_message("도박 결과", result_message, discord.Color.purple()))
        self.stop()

# !도박 명령어
@client.command()
async def 도박(ctx, bet: int):
    if bet <= 0:
        await ctx.send(embed=create_embed_message("오류", "배팅 금액은 1원 이상이어야 합니다.", discord.Color.red()))
        return

    # 확률 메시지와 결과 보기 버튼을 포함한 임베드 메시지
    probability = random.randint(1, 100)
    embed = create_embed_message(
        title="도박 확률",
        description=f"{ctx.author.mention}님, 현재 도박 성공 확률은 {probability}%입니다.\n'결과 보기' 버튼을 눌러 결과를 확인하세요!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=GambleView(bet, ctx))

# 가위바위보 버튼을 위한 버튼 정의
class RockPaperScissors(View):
    def __init__(self, bet, ctx):
        super().__init__()
        self.bet = bet
        self.ctx = ctx
        self.choices = ["가위", "바위", "보"]
        self.user_choice = None
        self.bot_choice = random.choice(self.choices)

    @discord.ui.button(label="가위", style=discord.ButtonStyle.green)
    async def rock(self, button: Button, interaction: discord.Interaction):
        if self.user_choice:
            return
        self.user_choice = "가위"
        await self.check_winner()

    @discord.ui.button(label="바위", style=discord.ButtonStyle.green)
    async def paper(self, button: Button, interaction: discord.Interaction):
        if self.user_choice:
            return
        self.user_choice = "바위"
        await self.check_winner()

    @discord.ui.button(label="보", style=discord.ButtonStyle.green)
    async def scissors(self, button: Button, interaction: discord.Interaction):
        if self.user_choice:
            return
        self.user_choice = "보"
        await self.check_winner()

    async def check_winner(self):
        if not self.user_choice:
            return
        
        result_message = f"봇은 {self.bot_choice}를 선택했습니다.\n"
        
        if self.user_choice == self.bot_choice:
            result_message += "무승부입니다!"
        elif (self.user_choice == "가위" and self.bot_choice == "보") or \
             (self.user_choice == "바위" and self.bot_choice == "가위") or \
             (self.user_choice == "보" and self.bot_choice == "바위"):
            result_message += f"승리하셨습니다! {self.bet * 2}원을 받았습니다."
            user_money[self.ctx.author.id] = user_money.get(self.ctx.author.id, 0) + (self.bet * 2)
        else:
            result_message += f"패배하셨습니다. {self.bet}원이 차감되었습니다."
            user_money[self.ctx.author.id] = user_money.get(self.ctx.author.id, 0) - self.bet
        
        await self.ctx.send(embed=create_embed_message("가위바위보 결과", result_message, discord.Color.purple()))
        self.stop()

# !가위바위보 명령어
@client.command()
async def 가위바위보(ctx, bet: int):
    if bet <= 0:
        await ctx.send(embed=create_embed_message("오류", "배팅 금액은 1원 이상이어야 합니다.", discord.Color.red()))
        return

    # 임베드로 가위바위보 게임 안내
    embed = create_embed_message(
        title="가위 바위 보 게임",
        description=f"{ctx.author.mention}님, 가위, 바위, 보 중 하나를 선택하세요!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=RockPaperScissors(bet, ctx))

# !바카라 명령어 수정 (무승부 처리)
@client.command()
async def 바카라(ctx, bet_type: str, bet: int):
    if bet <= 0:
        await ctx.send(embed=create_embed_message("오류", "배팅 금액은 1원 이상이어야 합니다.", discord.Color.red()))
        return

    if user_money.get(ctx.author.id, 0) < bet:
        await ctx.send(embed=create_embed_message("오류", f"{ctx.author.mention}님은 배팅 금액만큼의 자금이 부족합니다.", discord.Color.red()))
        return

    if bet_type not in ['플', '뱅']:
        await ctx.send(embed=create_embed_message("오류", "배팅은 '플' 또는 '뱅'으로만 가능합니다.", discord.Color.red()))
        return

    # 플레이어와 딜러의 카드 값 결정 (각각 두 장의 카드)
    player_card1 = random.randint(1, 9)
    player_card2 = random.randint(1, 9)
    dealer_card1 = random.randint(1, 9)
    dealer_card2 = random.randint(1, 9)

    # 카드 합 계산, 두 자릿수가 나올 경우 첫 번째 자리는 버림 (단, 두 자리 수일 경우 마지막 자리만 사용)
    player_total = (player_card1 + player_card2) % 10
    dealer_total = (dealer_card1 + dealer_card2) % 10

    result_message = f"플레이어 카드: {player_card1}, {player_card2} (합: {player_total})\n"
    result_message += f"딜러 카드: {dealer_card1}, {dealer_card2} (합: {dealer_total})\n"

    if player_total == dealer_total:
        result_message += "무승부입니다!"
        game_results.append(f"무승부: 플레이어({player_total}) vs 딜러({dealer_total})")
    elif bet_type == '플':  # 플레이어 배팅
        if player_total > dealer_total:
            user_money[ctx.author.id] = user_money.get(ctx.author.id, 0) + (bet * 2)
            result_message += f"{ctx.author.mention}님이 승리하여 {bet * 1}원을 받았습니다!"
            game_results.append(f"플레이어 승: 플레이어({player_total}) vs 딜러({dealer_total})")
        else:
            user_money[ctx.author.id] = user_money.get(ctx.author.id, 0) - bet
            result_message += f"딜러가 승리하여 {bet}원이 차감되었습니다."
            game_results.append(f"딜러 승: 플레이어({player_total}) vs 딜러({dealer_total})")
    elif bet_type == '뱅':  # 딜러 배팅
        if dealer_total > player_total:
            user_money[ctx.author.id] = user_money.get(ctx.author.id, 0) + (bet * 2)
            result_message += f"{ctx.author.mention}님이 승리하여 {bet * 2}원을 받았습니다!"
            game_results.append(f"딜러 승: 플레이어({player_total}) vs 딜러({dealer_total})")
        else:
            user_money[ctx.author.id] = user_money.get(ctx.author.id, 0) - bet
            result_message += f"플레이어가 승리하여 {bet}원이 차감되었습니다."
            game_results.append(f"플레이어 승: 플레이어({player_total}) vs 딜러({dealer_total})")

    await ctx.send(embed=create_embed_message("바카라 결과", result_message, discord.Color.purple()))

# !그림장 명령어 추가
@client.command()
async def 그림장(ctx):
    if not game_results:
        await ctx.send(embed=create_embed_message("결과 없음", "아직 게임 결과가 없습니다.", discord.Color.red()))
        return
    
    results_message = "지금까지 나온 바카라 결과:\n"
    for result in game_results:
        results_message += f"- {result}\n"
    
    await ctx.send(embed=create_embed_message("바카라 게임 결과", results_message, discord.Color.blue()))

# !돈순위 명령어
@client.command()
async def 돈순위(ctx):
    sorted_users = sorted(user_money.items(), key=lambda x: x[1], reverse=True)
    rank_message = "서버 개인 자산 순위:\n"
    for idx, (user_id, money) in enumerate(sorted_users[:10]):
        rank_message += f"{idx+1}. <@{user_id}>: {money}원\n"

    await ctx.send(embed=create_embed_message("자산 순위", rank_message, discord.Color.blue()))

# 데이터 파일 경로
data_file = 'user_money.json'

# 가상 화폐 시스템 설정
user_money = {}  # 유저 ID: 가상돈
user_stats = {}  # 유저 게임별 성적

# 봇 시작 시 데이터 불러오기
def load_data():
    global user_money, user_stats
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
            user_money = data.get("money", {})
            user_stats = data.get("stats", {})
    except FileNotFoundError:
        user_money = {}
        user_stats = {}

# 봇 종료 시 데이터 저장
def save_data():
    with open(data_file, 'w') as f:
        json.dump({"money": user_money, "stats": user_stats}, f)

@client.event
async def on_ready():
    print(f'봇이 {client.user}로 로그인했습니다!')

@client.event
async def on_disconnect():
    save_data()
    print("봇이 종료되었습니다. 자산 데이터가 저장되었습니다.")    

# 배너 메시지 보내기 위한 함수
def create_embed_message(title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="이 메시지는 봇에서 자동으로 생성되었습니다.")
    return embed

# !잔액 명령어
@client.command()
async def 잔액(ctx):
    user_id = ctx.author.id
    money = user_money.get(user_id, 0)
    await ctx.send(embed=create_embed_message(f"{ctx.author.name}님의 잔액", f"현재 잔액은 {money}원입니다.", discord.Color.green()))

# 게임 성적 관리 시스템
@client.command()
async def 게임성적(ctx, game_name: str):
    user_id = ctx.author.id
    if user_id not in user_stats:
        user_stats[user_id] = {"가위바위보": {"승리": 0, "패배": 0}, "도박": {"승리": 0, "패배": 0}, "용호": {"승리": 0, "패배": 0}}

    if game_name not in user_stats[user_id]:
        await ctx.send(embed=create_embed_message("오류", f"{game_name}은 등록된 게임이 아닙니다.", discord.Color.red()))
        return

    stats = user_stats[user_id][game_name]
    stats_message = f"{game_name} 게임 성적:\n승리: {stats['승리']}회\n패배: {stats['패배']}회"
    await ctx.send(embed=create_embed_message(f"{ctx.author.name}님의 {game_name} 성적", stats_message, discord.Color.green()))

# 봇과의 채팅 기능
@client.command()
async def 오늘기분(ctx):
    await ctx.send("오늘의 기분은 어때요? 😊")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        response = await client.wait_for('message', timeout=30.0, check=check)

        if "좋" in response.content:
            await ctx.send(f"오늘도 좋은 하루가 될 거예요, {ctx.author.mention}! 🎉")
            # 보상 예시
            user_money[ctx.author.id] = user_money.get(ctx.author.id, 0) + 1000
        elif "나쁘" in response.content:
            await ctx.send(f"힘든 날일 수도 있죠, {ctx.author.mention}. 괜찮아요, 잘 될 거예요! 💪")
        else:
            await ctx.send(f"그럼 {ctx.author.mention}, 좋은 하루 되세요! 🌞")

    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention}, 답변 시간이 초과되었습니다. 다시 시도해 주세요!")

# !재생 명령어 (YouTube 재생)
@client.command()
async def 재생(ctx, *, title: str):
    await ctx.send(embed=create_embed_message("재생", f"{ctx.author.mention}님이 요청한 '{title}'를 재생합니다!", discord.Color.orange()))
    # 여기에 유튜브 동영상 재생 코드 추가 (youtube_dl 사용)

# !스킵 명령어
@client.command()
async def 스킵(ctx):
    await ctx.send(embed=create_embed_message("스킵", f"{ctx.author.mention}님이 영상을 건너뜁니다.", discord.Color.yellow()))
    # 여기에 영상 건너뛰는 코드 추가

# 게임 결과를 저장할 리스트 추가 (용호 게임 결과)
yongho_results = []

# 카드 값 매핑 (A는 1, K는 13으로 처리)
card_values = {
    'A': 1, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 
    'J': 11, 'Q': 12, 'K': 13
}

# !용호 명령어 추가
@client.command()
async def 용호(ctx, choice: str, bet: int):
    if bet <= 0:
        await ctx.send(embed=create_embed_message("오류", "배팅 금액은 1원 이상이어야 합니다.", discord.Color.red()))
        return

    if user_money.get(ctx.author.id, 0) < bet:
        await ctx.send(embed=create_embed_message("오류", f"{ctx.author.mention}님은 배팅 금액만큼의 자금이 부족합니다.", discord.Color.red()))
        return

    # choice가 '용' 또는 '호'인지 확인
    if choice not in ['용', '호']:
        await ctx.send(embed=create_embed_message("오류", "배팅은 '용' 또는 '호'로만 가능합니다.", discord.Color.red()))
        return

    # 카드 값 결정 (용과 호에 각각 한 장씩 카드 지급)
    player_card = random.choice(list(card_values.keys()))
    dealer_card = random.choice(list(card_values.keys()))

    player_card_value = card_values[player_card]
    dealer_card_value = card_values[dealer_card]

    # 카드 값과 결과 메시지 생성
    result_message = f"{ctx.author.mention}님이 선택한 카드는 '{player_card}'입니다.\n"
    result_message += f"상대의 카드는 '{dealer_card}'입니다.\n"
    result_message += f"플레이어 카드 값: {player_card_value}, 딜러 카드 값: {dealer_card_value}\n"

    # 승패 결정
    if player_card_value > dealer_card_value:
        user_money[ctx.author.id] = user_money.get(ctx.author.id, 0) + (bet * 1)
        result_message += f"{ctx.author.mention}님이 승리하여 {bet * 2}원을 받았습니다!"
        yongho_results.append(f"{ctx.author.mention}님 승리: {player_card} vs {dealer_card}")
    elif player_card_value < dealer_card_value:
        user_money[ctx.author.id] = user_money.get(ctx.author.id, 0) - bet
        result_message += f"딜러가 승리하여 {bet}원이 차감되었습니다."
        yongho_results.append(f"{ctx.author.mention}님 패배: {player_card} vs {dealer_card}")
    else:
        result_message += "무승부입니다!"
        yongho_results.append(f"무승부: {player_card} vs {dealer_card}")

    await ctx.send(embed=create_embed_message("용호 결과", result_message, discord.Color.purple()))

# !용호 그림장 명령어 추가
@client.command()
async def 용호그림장(ctx):
    if not yongho_results:
        await ctx.send(embed=create_embed_message("결과 없음", "아직 용호 게임 결과가 없습니다.", discord.Color.red()))
        return
    
    results_message = "지금까지 나온 용호 게임 결과:\n"
    for result in yongho_results:
        results_message += f"- {result}\n"
    
    await ctx.send(embed=create_embed_message("용호 게임 결과", results_message, discord.Color.blue()))

# !오무진 명령어
@client.command()
async def 오무진(ctx):
    await ctx.send("👊")  # 주먹 이모티콘을 보냅니다.

# !이현석 명령어
@client.command()
async def 이현석(ctx):
    await ctx.send("규형이의 썩은 자지가 재희의 보지속으로 들어간다 우흥흥")  # 주먹 이모티콘을 보냅니다.

# !김슉슉어
@client.command()
async def 김슉(ctx)
    await ctx.send("백슉쌈밥 커몬 베이베")

# !도움말 명령어
@client.command()
async def 도움말(ctx):
    help_message = """
    **사용할 수 있는 명령어들:**

    **!돈줘** - 유저에게 30,000원을 지급합니다. (30분에 한 번만 사용 가능)
    **!도박 <배팅금액>** - 도박을 시도하고 성공 시 배팅 금액의 2배를 받습니다.
    **!가위바위보 <배팅금액>** - 가위바위보 게임을 하고 승리 시 배팅 금액의 2배를 받습니다.
    **!돈순위** - 서버 내 개인 자산 순위를 보여줍니다.
    **!재생 <제목>** - 유튜브 영상을 음성 채널에서 재생합니다.
    **!스킵** - 현재 재생 중인 유튜브 영상을 건너뜁니다.
    **!잔액** - 현제 잔액을 볼수있다다
    **!바카라** - 바카라를 할수있다 용호는 용호 할수있음 ㅇㅇ
    **!그림장** - 그림장임 용호그림장 하면 용호도 볼수있음 ㅇㅇ
    **오무진 섹스 
    **오무진 하이퍼 차지지
    """
    await ctx.send(embed=create_embed_message("도움말", help_message, discord.Color.green()))

access_token = os.environ["MTM0MjEzMDM4OTU3MjkxNTIwMA.G-nVET.fuCNd62BRfstcYz_5TSod0LnrayvuEjVLkxDWk"]
# 봇 토큰으로 로그인
client.run('access_token')
