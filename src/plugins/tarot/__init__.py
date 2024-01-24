from nonebot import on_regex
from nonebot.adapters.onebot.v11 import GROUP, Bot, GroupMessageEvent
from nonebot.plugin import PluginMetadata

from src.params import PluginConfig, cost_gold

from .config import CARDS, CONTENT
from .model import Tarot

__plugin_meta__ = PluginMetadata(
    name="塔罗牌",
    description="塔罗牌占卜，单抽抽取单张牌，塔罗牌抽取牌组",
    usage="单抽 | 塔罗牌",
    config=PluginConfig(),
)

tarot_manager = Tarot.parse_obj({"cards": CARDS, "formations": CONTENT})


divine = on_regex(pattern=r"^单抽$", permission=GROUP, priority=5, block=True)
tarot = on_regex(pattern=r"^塔罗牌$", permission=GROUP, priority=5, block=True)


@divine.handle(parameterless=[])
async def _(event: GroupMessageEvent):
    """单抽"""
    msg = await tarot_manager.single_divine()
    await divine.finish(msg)


@tarot.handle(parameterless=[])
async def _(bot: Bot, event: GroupMessageEvent):
    """塔罗牌牌阵"""

    content = tarot_manager.divine()
    msg = f"启用{content.formation_name}，正在洗牌中"
    await tarot.send(msg)

    chain = []
    for i in range(content.cards_num):
        reveal_msg = await tarot_manager.reveal(content, i)
        data = {
            "type": "node",
            "data": {
                "name": list(bot.config.nickname)[0],
                "uin": bot.self_id,
                "content": reveal_msg,
            },
        }
        chain.append(data)

    await bot.send_group_forward_msg(group_id=event.group_id, messages=chain)
    await tarot.finish()
