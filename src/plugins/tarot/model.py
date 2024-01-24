import random
from io import BytesIO
from pathlib import Path

from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.utils import run_sync
from PIL import Image
from pydantic import BaseModel


class Card(BaseModel):
    """塔罗牌模型"""

    name_cn: str
    """中文名"""
    name_en: str
    """英文名"""
    type: str
    """所属类型"""
    meaning: dict
    """释义"""
    pic: str
    """资源名称"""


class Content(BaseModel):
    """阵型模型"""

    name: str
    """阵型名"""
    is_cut: bool
    """是否需要切牌"""
    cards_num: int
    """卡牌数量"""
    represent: list[list[str]]
    """代表内容"""


class TarotModel(BaseModel):
    """卡牌传递模型"""

    formation_name: str
    """阵型名称"""
    cards_num: int
    """卡牌数量"""
    devined: list[Card]
    """选出的卡牌"""
    is_cut: bool
    """是否切牌"""
    represent: list[str]
    """代表内容"""


class Tarot(BaseModel):
    """塔罗牌类"""

    formations: list[Content]
    """阵型"""
    cards: list[Card]
    """卡片"""

    async def single_divine(self) -> MessageSegment:
        """
        说明:
            单抽一张塔罗牌
        """
        card = random.choice(self.cards)
        msg_header = MessageSegment.text("回应是")
        msg_body = await self.multi_divine(card)
        return msg_header + msg_body

    def divine(self) -> TarotModel:
        """
        说明:
            获取一个阵型
        """
        formation = random.choice(self.formations)
        devined = random.sample(self.cards, formation.cards_num)
        represent = random.choice(formation.represent)
        return TarotModel(
            formation_name=formation.name,
            cards_num=formation.cards_num,
            devined=devined,
            is_cut=formation.is_cut,
            represent=represent,
        )

    @classmethod
    async def reveal(cls, tarot: TarotModel, index: int) -> MessageSegment:
        """
        说明:
            揭示一张塔罗牌

        参数:
            * `tarot`：塔罗牌模型
            * `index`：序号

        返回:
            * `MessageSegment`：揭示的消息
        """
        if tarot.is_cut and index == tarot.cards_num - 1:
            msg_header = MessageSegment.text(f"切牌「{tarot.represent[index]}」\n")
        else:
            msg_header = MessageSegment.text(
                f"第{index+1}张牌「{tarot.represent[index]}」\n"
            )

        msg_body = await cls.multi_divine(tarot.devined[index])
        return msg_header + msg_body

    @classmethod
    @run_sync
    def multi_divine(cls, card: Card) -> MessageSegment:
        """
        说明:
            返回卡牌图片消息

        参数:
            * `card`：卡片信息

        返回:
            * `MessageSegment`：卡片图片消息
        """
        img_path = Path("data/resource") / card.type / card.pic
        img = Image.open(img_path)
        if random.random() < 0.5:
            # 正位
            meaning = card.meaning["up"]
            msg = MessageSegment.text(f"「{card.name_cn}正位」「{meaning}」\n")
        else:
            # 逆位
            meaning = card.meaning["down"]
            msg = MessageSegment.text(f"「{card.name_cn}逆位」「{meaning}」\n")
            img = img.rotate(180)

        buf = BytesIO()
        img.save(buf, format="png")
        return msg + MessageSegment.image(buf)
