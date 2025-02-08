import discord
from discord.ext import commands
import random
import math

prog_langs = ["C++", "Rust", "Python", "JavaScript", "Go", "Java", "TypeScript", "Swift", "Kotlin", "PHP", "Ruby"]
nice_lang = {"C++": "Rust", "Rust": "Python", "Python": "JavaScript", "JavaScript": "Go", "Go": "Java", "Java": "TypeScript", "TypeScript": "Swift", "Swift": "Kotlin", "Kotlin": "PHP", "PHP": "Ruby", "Ruby": "C++"}
bad_lang = {"Rust": "C++", "Python": "Rust", "JavaScript": "Python", "Go": "JavaScript", "Java": "Go", "TypeScript": "Java", "Swift": "TypeScript", "Kotlin": "Swift", "PHP": "Kotlin", "Ruby": "PHP", "C++": "Ruby"}

class LoveCalculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="love-calculator", description="2人のユーザーを選択して愛の相性を計算します")
    async def love_calculator(self, interaction: discord.Interaction, user1: discord.User, user2: discord.User):
        if user1 == user2:
            embed = discord.Embed(title="💖 Love Calculator 💖", color=discord.Color.pink())
            embed.add_field(name="メッセージ", value="1人目と2人目で同じユーザーが選択されています。", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            name1 = user1.name
            name2 = user2.name
            love_score = self.K7LoveCalc(name1, name2)
            message = self.get_love_message(name1, name2, love_score[0], love_score[1], love_score[2])
            embed = discord.Embed(title="💖 Love Calculator 💖", color=discord.Color.pink())
            #embed.add_field(name="ユーザー1", value=name1, inline=True)
            #embed.add_field(name="ユーザー2", value=name2, inline=True)
            embed.add_field(name=name1+"→"+name2, value=f"好感度：{love_score[1]}% 性欲：{love_score[3]}", inline=False)
            embed.add_field(name=name2+"→"+name1, value=f"好感度：{love_score[2]}% 性欲：{love_score[4]}", inline=False)
            embed.add_field(name="総合相性（好感度平均）", value=f"{love_score[0]}%", inline=False)
            embed.add_field(name="メッセージ", value=message, inline=False)
            await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name="fantasy-status", description="特定の人の装備品、攻撃力、守備力、体力を表示する")
    async def fantasy_status(self, interaction: discord.Interaction, user: discord.User):
        name = user.name
        stats = self.K7StatsCalc(name)
        embed = discord.Embed(title="⚔ 異世界ステータスジェネレーター ⚔", color=discord.Color.blue())
        embed.add_field(name="名前", value=name, inline=False)
        embed.add_field(name="装備", value=stats[0], inline=True)
        embed.add_field(name="攻撃力", value=stats[1], inline=True)
        embed.add_field(name="守備力", value=stats[2], inline=True)
        embed.add_field(name="最大HP", value=stats[3], inline=True)
        embed.add_field(name="相性の良い言語（攻撃力 x1.2）", value=nice_lang[stats[0]], inline=True)
        embed.add_field(name="相性の悪い言語（攻撃力 x0.87）", value=bad_lang[stats[0]], inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="versus", description="fantasy-statusのステータスをもとに対戦させます。ステータスは固定ですがそれ以外はランダム。")
    async def versus(self, interaction: discord.Interaction, user1: discord.User, user2: discord.User):
        random.seed()
        if user1 == user2:
            embed = discord.Embed(title="⚔ Versus ⚔", color=discord.Color.dark_red())
            embed.add_field(name="メッセージ", value="1人目と2人目で同じユーザーが選択されています。", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            name1 = user1.name
            name2 = user2.name
            stats1 = self.K7StatsCalc(name1)
            stats2 = self.K7StatsCalc(name2)
            hp1 = stats1[3]
            hp2 = stats2[3]
            embed = discord.Embed(title="⚔ Versus ⚔", color=discord.Color.dark_red())
            turn = random.randint(0,1)
            for i in range(20):
                crit = False
                crit_chance = 0.1
                if turn:
                    turn_atk = stats1[1]
                    turn_def = stats2[2]
                    if nice_lang[stats1[0]] == stats2[0]:
                        crit_chance = 0.2
                        turn_atk *= 1.2
                    elif bad_lang[stats1[0]] == stats2[0]:
                        crit_chance = 0.05
                        turn_atk *= 0.87
                    if random.random() <= crit_chance:
                        turn_atk *= 2
                        turn_def = 0
                        crit = True
                    damage = math.floor(max(0, turn_atk*(1-(turn_def/100))))
                    hp2 -= damage
                    if crit:
                        embed.add_field(name=name1+"のターン", value="クリティカルヒット！"+name2+"に"+str(damage)+"のダメージ！残りHP："+str(hp2), inline=False)
                    else:
                        embed.add_field(name=name1+"のターン", value=name2+"に"+str(damage)+"のダメージ！残りHP："+str(hp2), inline=False)
                    if hp2 <= 0:
                        embed.add_field(name=name1+"の勝利！", value=name1+"は"+str(hp1)+"の体力を残して勝利した！", inline=False)
                        break
                else:
                    turn_atk = stats2[1]
                    crit_chance = 0.1
                    turn_def = stats1[2]
                    if nice_lang[stats2[0]] == stats1[0]:
                        crit_chance = 0.2
                        turn_atk *= 1.2
                    elif bad_lang[stats2[0]] == stats1[0]:
                        crit_chance = 0.05
                        turn_atk *= 0.87
                    if random.random() <= crit_chance:
                        turn_atk *= 2
                        turn_def = 0
                        crit = True
                    damage = math.floor(max(0, turn_atk*(1-(turn_def/100))))
                    hp1 -= damage
                    if crit:
                        embed.add_field(name=name2+"のターン", value="クリティカルヒット！"+name1+"に"+str(damage)+"のダメージ！残りHP："+str(hp1), inline=False)
                    else:
                        embed.add_field(name=name2+"のターン", value=name1+"に"+str(damage)+"のダメージ！残りHP："+str(hp1), inline=False)
                    if hp1 <= 0:
                        embed.add_field(name=name2+"の勝利！", value=name2+"は"+str(hp2)+"の体力を残して勝利した！", inline=False)
                        break
                turn = not turn
            if hp1 > 0 and hp2 > 0:
                embed.add_field(name="引き分け", value="10ターン以内に戦いが終わらなかった。\n"+name1+"の体力："+str(hp1)+"/n"+name2+"の体力："+str(hp2), inline=False)
            await interaction.response.send_message(embed=embed)
        
    def K7LoveCalc(self, name1: str, name2: str):
        if name1 > name2:
            combined_names = name1 + name2
        else:
            combined_names = name2 + name1
        random.seed(combined_names)
        user1_to_user2_friend = random.randint(0, 100)
        user2_to_user1_friend = random.randint(0, 100)
        user1_to_user2_sex = random.randint(0, user1_to_user2_friend)
        user2_to_user1_sex = random.randint(0, user2_to_user1_friend)
        love_score = (user1_to_user2_friend + user2_to_user1_friend) // 2
        if name1 > name2:
            return [love_score, user1_to_user2_friend, user2_to_user1_friend, user1_to_user2_sex, user2_to_user1_sex]
        else:
            return [love_score, user2_to_user1_friend, user1_to_user2_friend, user2_to_user1_sex, user1_to_user2_sex]
        
    def K7StatsCalc(self, name: str):
        random.seed(name)
        weapon = random.choice(prog_langs)
        attack = random.randint(0, 100)
        defence = random.randint(0, 100)
        hp = random.randint(attack+defence, 300)
        return [weapon, attack, defence, hp]

    def get_love_message(self, user1_name, user2_name, score, user1_to_user2, user2_to_user1):
        if user1_to_user2 - user2_to_user1 > 70:
            return user1_name+"よ、諦めろ。"
        elif user2_to_user1 - user1_to_user2 > 70:
            return user2_name+"よ、諦めろ。"
        elif abs(user1_to_user2 - user2_to_user1) > 50:
            return "視界に入れてない可能性があります。"
        elif abs(user1_to_user2 - user2_to_user1) > 30:
            return "片思いの可能性があります。💔"
        elif score > 80:
            return "素晴らしい相性です！💞"
        elif score > 60:
            return "とても良い相性です！😊"
        elif score > 40:
            return "まあまあの相性です。🙂"
        elif score > 20:
            return "ちょっと微妙かも...😕"
        else:
            return "残念ながら、相性はあまり良くないようです。😢"

async def setup(bot):
    await bot.add_cog(LoveCalculator(bot))
