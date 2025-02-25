# Swiftly DiscordBot.
# Developed by: TechFish_1
import asyncio
import os
import json
import time
from typing import Final, Optional, Set, Dict, Any
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import aiosqlite
import dotenv
import discord
from discord.ext import commands

# 定数定義
SHARD_COUNT: Final[int] = 10
COMMAND_PREFIX: Final[str] = "sw!"
STATUS_UPDATE_COOLDOWN: Final[int] = 5
LOG_RETENTION_DAYS: Final[int] = 7

PATHS: Final[dict] = {
    "log_dir": Path("./log"),
    "db": Path("data/prohibited_channels.db"),
    "user_count": Path("data/user_count.json"),
    "cogs_dir": Path("./cogs")
}

ERROR_MESSAGES: Final[dict] = {
    "command_error": "エラーが発生しました",
    "prohibited_channel": "このチャンネルではコマンドの実行が禁止されています。",
    "db_error": "データベースエラーが発生しました: {}"
}

LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logger = logging.getLogger(__name__)

class DatabaseManager:
    """データベース操作を管理するクラス"""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """データベースを初期化"""
        self._connection = await aiosqlite.connect(self.db_path)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS prohibited_channels (
                guild_id TEXT,
                channel_id TEXT,
                PRIMARY KEY (guild_id, channel_id)
            )
        """)
        await self._connection.commit()

    async def cleanup(self) -> None:
        """データベース接続を閉じる"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def is_channel_prohibited(
        self,
        guild_id: int,
        channel_id: int
    ) -> bool:
        """
        チャンネルが禁止されているかチェック

        Parameters
        ----------
        guild_id : int
            ギルドID
        channel_id : int
            チャンネルID

        Returns
        -------
        bool
            禁止されているならTrue
        """
        try:
            if not self._connection:
                await self.initialize()

            async with self._connection.execute(
                """
                SELECT 1 FROM prohibited_channels
                WHERE guild_id = ? AND channel_id = ?
                """,
                (str(guild_id), str(channel_id))
            ) as cursor:
                return bool(await cursor.fetchone())

        except Exception as e:
            logger.error(f"Database error: {e}", exc_info=True)
            return False

class UserCountManager:
    """ユーザー数管理を行うクラス"""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_update = 0
        self._cache: Dict[str, Any] = {}

    def _read_count(self) -> int:
        """ファイルからユーザー数を読み込み"""
        try:
            if self.file_path.exists():
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
                return data.get("total_users", 0)
            return 0
        except Exception as e:
            logger.error(f"Error reading user count: {e}", exc_info=True)
            return 0

    def _write_count(self, count: int) -> None:
        """ユーザー数をファイルに書き込み"""
        try:
            self.file_path.write_text(
                json.dumps(
                    {"total_users": count},
                    ensure_ascii=False,
                    indent=4
                ),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Error writing user count: {e}", exc_info=True)

    def get_count(self) -> int:
        """現在のユーザー数を取得"""
        return self._read_count()

    def update_count(self, count: int) -> None:
        """
        ユーザー数を更新

        Parameters
        ----------
        count : int
            新しいユーザー数
        """
        self._write_count(count)
        self._last_update = time.time()

    def should_update(self) -> bool:
        """更新が必要かどうかを判定"""
        return time.time() - self._last_update >= STATUS_UPDATE_COOLDOWN

class SwiftlyBot(commands.Bot):
    """Swiftlyボットのメインクラス"""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.messages = True
        intents.message_content = True

        client = discord.AutoShardedClient(
            intents=intents,
            shard_count=SHARD_COUNT
        )

        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            client=client
        )

        self.db = DatabaseManager(PATHS["db"])
        self.user_count = UserCountManager(PATHS["user_count"])
        self._setup_logging()

    def _setup_logging(self) -> None:
        """ロギングの設定"""
        PATHS["log_dir"].mkdir(exist_ok=True)

        # 共通のログハンドラ設定
        handlers = []
        for name, level in [("logs", logging.DEBUG), ("commands", logging.DEBUG)]:
            handler = TimedRotatingFileHandler(
                PATHS["log_dir"] / f"{name}.log",
                when="midnight",
                interval=1,
                backupCount=LOG_RETENTION_DAYS,
                encoding="utf-8"
            )
            handler.setLevel(level)
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            handlers.append(handler)

        # ボットのロガー設定
        logger.setLevel(logging.WARNING)
        for handler in handlers:
            logger.addHandler(handler)

        # Discordのロガー設定
        discord_logger = logging.getLogger("discord")
        discord_logger.setLevel(logging.WARNING)
        for handler in handlers:
            discord_logger.addHandler(handler)

    async def setup_hook(self) -> None:
        """ボットのセットアップ処理"""
        await self.db.initialize()
        await self._load_extensions()
        await self.tree.sync()

    async def _load_extensions(self) -> None:
        """Cogを読み込み"""
        for file in PATHS["cogs_dir"].glob("*.py"):
            if file.stem == "__init__":
                continue

            try:
                await self.load_extension(f"cogs.{file.stem}")
                logger.info(f"Loaded: cogs.{file.stem}")
            except Exception as e:
                logger.error(
                    f"Failed to load: cogs.{file.stem} - {e}",
                    exc_info=True
                )

    async def update_presence(self) -> None:
        """ステータスを更新"""
        if self.user_count.should_update():
            count = self.user_count.get_count()
            await self.change_presence(
                activity=discord.Game(
                    name=f"{count}人のユーザー数"
                )
            )

    async def count_unique_users(self) -> None:
        """ユニークユーザー数を集計"""
        unique_users: Set[int] = set()
        for guild in self.guilds:
            unique_users.update(member.id for member in guild.members)

        count = len(unique_users)
        logger.info(f"Unique user count: {count}")
        self.user_count.update_count(count)
        await self.update_presence()

    async def on_ready(self) -> None:
        """準備完了時の処理"""
        logger.info(f"Logged in as {self.user}")
        await self.count_unique_users()

    async def on_member_join(self, _) -> None:
        """メンバー参加時の処理"""
        await self.count_unique_users()

    async def on_member_remove(self, _) -> None:
        """メンバー退出時の処理"""
        await self.count_unique_users()

    async def on_command_completion(
        self,
        ctx: commands.Context
    ) -> None:
        """コマンド完了時の処理"""
        logger.info("Command executed: %s", ctx.command)

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: Exception
    ) -> None:
        """コマンドエラー時の処理"""
        logger.error("Command error: %s", error, exc_info=True)
        await ctx.send(ERROR_MESSAGES["command_error"])

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ) -> None:
        """アプリケーションコマンドエラー時の処理"""
        logger.error("App command error: %s", error, exc_info=True)
        await interaction.response.send_message(
            ERROR_MESSAGES["command_error"],
            ephemeral=True
        )

    async def check_command_permissions(
        self,
        ctx: commands.Context
    ) -> bool:
        """
        コマンド実行権限をチェック

        Parameters
        ----------
        ctx : commands.Context
            コマンドコンテキスト

        Returns
        -------
        bool
            実行可能ならTrue
        """
        if not ctx.guild:
            return True

        if ctx.command and ctx.command.name == "set_mute_channel":
            return True

        is_prohibited = await self.db.is_channel_prohibited(
            ctx.guild.id,
            ctx.channel.id
        )
        if is_prohibited:
            await ctx.send(ERROR_MESSAGES["prohibited_channel"])
            return False
        return True

    async def check_slash_command(
        self,
        interaction: discord.Interaction
    ) -> bool:
        """
        スラッシュコマンドの実行権限をチェック

        Parameters
        ----------
        interaction : discord.Interaction
            インタラクションコンテキスト

        Returns
        -------
        bool
            実行可能ならTrue
        """
        if not interaction.guild:
            return True

        if (interaction.command and
            interaction.command.name == "set_mute_channel"):
            return True

        is_prohibited = await self.db.is_channel_prohibited(
            interaction.guild_id,
            interaction.channel_id
        )
        if is_prohibited:
            await interaction.response.send_message(
                ERROR_MESSAGES["prohibited_channel"],
                ephemeral=True
            )
            return False
        return True

def main() -> None:
    """メイン処理"""
    # 環境変数の読み込み
    dotenv.load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN not found in .env file")

    # ボットの起動
    bot = SwiftlyBot()
    bot.tree.interaction_check = bot.check_slash_command
    bot.check(bot.check_command_permissions)

    try:
        asyncio.run(bot.start(token))
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error("Bot crashed: %s", e, exc_info=True)
    finally:
        asyncio.run(bot.db.cleanup())

if __name__ == "__main__":
    main()
