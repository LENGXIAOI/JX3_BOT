
import time
import requests
# from .cs import emm
from datetime import datetime
from enum import Enum
import urllib.parse
from typing import NoReturn, Optional
import os
from pathlib import Path
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.message import Message
from nonebot.matcher import Matcher
from nonebot.params import Depends, RegexDict
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, Event
from src.internal.jx3api import JX3API, JX3APICS, JX3APICSS, JX3APIV8, JX3APIJYH
from src.modules.group_info import GroupInfo
from src.modules.search_record import SearchRecord
from src.modules.ticket_info import TicketInfo
from src.params import PluginConfig, user_matcher_group, cost_gold
from src.utils.browser import browser
from src.utils.log import logger

from . import data_source as source
from .config import JX3PROFESSION,JX3QIYU

__plugin_meta__ = PluginMetadata(
    name="剑三查询", description="剑三游戏查询，数据源使用jx3api", usage="参考“功能”", config=PluginConfig()
)

api = JX3API()          #WWW
apics = JX3APICS()      #V7版API
apicss = JX3APICSS()    #V2
apiv8 = JX3APIV8()
apijyh = JX3APIJYH()    #交易行
"""jx3api接口实例"""

# ----------------------------------------------------------------
#   正则枚举，已实现的查询功能
# ----------------------------------------------------------------


class REGEX(Enum):
    """正则枚举"""

    日常任务 = r"^日常$|^日常 (?P<server>[\S]+)$"
    开服检查 = r"^开服$|^开服 (?P<server>[\S]+)$"
    金价比例 = r"^金价$|^金价 (?P<server>[\S]+)$"
    推荐小药 = r"^小药 (?P<value1>[\S]+)$|^(?P<value2>[\S]+)小药$"
    日常预测 = r"^日常预测$|^日常预测 (?P<server>[\S]+)$"
    掉落汇总 = r"^掉落汇总1$|^掉落汇总1 (?P<server>[\S]+)$"
    推荐装备 = r"^配装 (?P<value1>[\S]+)$|^(?P<value2>[\S]+)配装$"
    查宏命令 = r"^宏 (?P<value1>[\S]+)$"
    阵眼效果 = r"^阵眼 (?P<value1>[\S]+)$|^(?P<value2>[\S]+)阵眼$"
    物品价格 = r"^物价 (?P<value1>[\S]+)$"
    随机骚话 = r"^骚话$"
    马驹刷新 = r"^马场$|^马场 (?P<server>[\S]+)$"
    楚天行侠 = r"^楚天行侠$|^楚天社$"
    云从社 = r"^云从社$"
    百战异闻录 = r"^百战1$"
    百战异闻录V = r"^百战$"
    更新公告 = r"^更新$|^公告$|^更新公告$"
    奇遇查询 = r"^查询 (?P<value1>[\S]+)$|^查询 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    奇遇统计 = r"^奇遇 (?P<value1>[\S]+)$|^奇遇 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    掉落统计 = r"^掉落1 (?P<value1>[\S]+)$|^掉落1 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    掉落统计V = r"^掉落 (?P<value1>[\S]+)$|^掉落 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    鲜花价格 = r"^花价$|^花价 (?P<server>[\S]+)$"
    奇遇汇总 = r"^汇总$|^汇总 (?P<server>[\S]+)$"
    比赛战绩 = r"^战绩 (?P<value1>[\S]+)$|^战绩 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    名剑战绩 = r"^JJC (?P<server1>[\S]+) (?P<value1>[\S]+) (?P<value3>[\S]+)$|^JJC (?P<value2>[\S]+) (?P<value4>[\S]+)$"
    装备属性 = r"^(?:(?:装备)|(?:属性)) (?P<value1>[\S]+)$|^(?:(?:装备)|(?:属性)) (?P<server>[\S]+) (?P<value2>[\S]+)$"
    烟花记录 = r"^烟花 (?P<value1>[\S]+)$|^烟花 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    副本记录 = r"^副本 (?P<value1>[\S]+)$|^副本 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    招募查询 = r"^招募$|^招募 (?P<server1>[\S]+)$|^招募 (?P<server2>[\S]+) (?P<keyword>[\S]+)$"
    沙盘查询 = r"^沙盘$|^沙盘 (?P<server>[\S]+)$"
    风云榜单 = r"^风云录 (?P<value1>[\S]+) (?P<server1>[\S]+) (?P<value3>[\S]+)$|^风云录 (?P<value2>[\S]+) (?P<value4>[\S]+)$"
    资历榜 = r"^资历榜$|^资历榜 (?P<server1>[\S]+)$|^资历榜 (?P<server2>[\S]+) (?P<keyword>[\S]+)$"
    成就进度 = r"^成就 (?P<server1>[\S]+) (?P<value1>[\S]+) (?P<value3>[\S]+)$|^成就 (?P<value2>[\S]+) (?P<value4>[\S]+)$"
    科举答题 = r"^科举 (?P<value1>[\S]+)$"
    拜师列表 = r"^找师父$|^找师父 (?P<server1>[\S]+)$|^找师父 (?P<server2>[\S]+) (?P<keyword>[\S]+)$"
    收徒列表 = r"^找徒弟$|^找徒弟 (?P<server1>[\S]+)$|^找徒弟 (?P<server2>[\S]+) (?P<keyword>[\S]+)$"
    挂件详情 = r"^挂件 (?P<value1>[\S]+)$"
    V2剩余次数 = r"^V2次数$"
    角色信息 = r"^角色 (?P<value1>[\S]+)$|^角色 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    交易行价格 = r"^交易行 (?P<value1>[\S]+)$|^交易行 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    角色信息更新 = r"^角色更新 (?P<value1>[\S]+)$|^角色更新 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    八卦帖子 = r"^贴吧 (?P<value1>[\S]+)$|^贴吧 (?P<server>[\S]+) (?P<value2>[\S]+)$"
    名剑排行 = r"^名剑排行$|^名剑排行 (?P<value1>[\S]+)$"
    诛恶事件 = r"^诛恶事件$"
    统战歪歪 =  r"^统战$|^统战 (?P<server>[\S]+)$"
    的卢 = r"^的卢$|^的卢 (?P<server>[\S]+)$"


# ----------------------------------------------------------------
#   matcher列表，定义查询的mathcer
# ----------------------------------------------------------------
daily_query = user_matcher_group.on_regex(pattern=REGEX.日常任务.value)
active_monster = user_matcher_group.on_regex(pattern=REGEX.百战异闻录.value)
daily_view = user_matcher_group.on_regex(pattern=REGEX.日常预测.value)
items_collect = user_matcher_group.on_regex(pattern=REGEX.掉落汇总.value)
server_query = user_matcher_group.on_regex(pattern=REGEX.开服检查.value)
gold_query = user_matcher_group.on_regex(pattern=REGEX.金价比例.value)
medicine_query = user_matcher_group.on_regex(pattern=REGEX.推荐小药.value)
equip_group_query = user_matcher_group.on_regex(pattern=REGEX.推荐装备.value)
macro_query = user_matcher_group.on_regex(pattern=REGEX.查宏命令.value)
zhenyan_query = user_matcher_group.on_regex(pattern=REGEX.阵眼效果.value)
trade_market = user_matcher_group.on_regex(pattern=REGEX.交易行价格.value)
update_query = user_matcher_group.on_regex(pattern=REGEX.更新公告.value)
price_query = user_matcher_group.on_regex(pattern=REGEX.物品价格.value)
serendipity_query = user_matcher_group.on_regex(pattern=REGEX.奇遇查询.value)
serendipity_list_query = user_matcher_group.on_regex(pattern=REGEX.奇遇统计.value)
items_statistical = user_matcher_group.on_regex(pattern=REGEX.掉落统计.value)
home_flower = user_matcher_group.on_regex(pattern=REGEX.鲜花价格.value)
serendipity_summary_query = user_matcher_group.on_regex(pattern=REGEX.奇遇汇总.value)
saohua_query = user_matcher_group.on_regex(pattern=REGEX.随机骚话.value)
match_query = user_matcher_group.on_regex(pattern=REGEX.比赛战绩.value)
equip_query = user_matcher_group.on_regex(pattern=REGEX.装备属性.value)
firework_query = user_matcher_group.on_regex(pattern=REGEX.烟花记录.value)
teamCdList_query = user_matcher_group.on_regex(pattern=REGEX.副本记录.value)
recruit_query = user_matcher_group.on_regex(pattern=REGEX.招募查询.value)
sand_query = user_matcher_group.on_regex(pattern=REGEX.沙盘查询.value)
zili_query = user_matcher_group.on_regex(pattern=REGEX.资历榜.value)
rank_excellent = user_matcher_group.on_regex(pattern=REGEX.风云榜单.value)
role_achievement = user_matcher_group.on_regex(pattern=REGEX.成就进度.value)
active_chivalrous = user_matcher_group.on_regex(pattern=REGEX.楚天行侠.value)
data_chivalrous = user_matcher_group.on_regex(pattern=REGEX.云从社.value)
exam_answer = user_matcher_group.on_regex(pattern=REGEX.科举答题.value)
member_student = user_matcher_group.on_regex(pattern=REGEX.拜师列表.value)
member_teacher = user_matcher_group.on_regex(pattern=REGEX.收徒列表.value)
other_pendant = user_matcher_group.on_regex(pattern=REGEX.挂件详情.value)
token_count = user_matcher_group.on_regex(pattern=REGEX.V2剩余次数.value)
role_roleInfo = user_matcher_group.on_regex(pattern=REGEX.角色信息.value)
save_roleInfo = user_matcher_group.on_regex(pattern=REGEX.角色信息更新.value)
tieba_random = user_matcher_group.on_regex(pattern=REGEX.八卦帖子.value)
server_antivice = user_matcher_group.on_regex(pattern=REGEX.诛恶事件.value)
active_baizhan = user_matcher_group.on_regex(pattern=REGEX.百战异闻录V.value)
active_jjc = user_matcher_group.on_regex(pattern=REGEX.名剑战绩.value)
match_awesome = user_matcher_group.on_regex(pattern=REGEX.名剑排行.value)
valuables_statistical = user_matcher_group.on_regex(pattern=REGEX.掉落统计V.value)
data_duowan = user_matcher_group.on_regex(pattern=REGEX.统战歪歪.value)
data_event = user_matcher_group.on_regex(pattern=REGEX.马驹刷新.value)
data_dilu = user_matcher_group.on_regex(pattern=REGEX.的卢.value)
help = user_matcher_group.on_regex(pattern=r"^功能$")


# ----------------------------------------------------------------
#   Dependency，用来获取相关参数及冷却实现
# ----------------------------------------------------------------


def get_server() -> str:
    """
    说明:
        Dependency，获取匹配字符串中的server，如果没有则获取群绑定的默认server
    """

    async def dependency(
        matcher: Matcher, event: GroupMessageEvent, regex_dict: dict = RegexDict()
    ) -> str:

        _server = regex_dict.get("server")
        if _server:
            server = api.app_server(name=_server)
            if not server:
                msg = f"未找到服务器[{_server}]，请验证后查询。"
                await matcher.finish(msg)
        else:
            server = await GroupInfo.get_server(event.group_id)
        return server

    return Depends(dependency)


def get_value() -> str:
    """
    说明:
        Dependency，获取匹配字符串中的value字段
    """

    async def dependency(regex_dict: dict = RegexDict()) -> str:

        value = regex_dict.get("value1")
        return value if value else regex_dict.get("value2")

    return Depends(dependency)
    
def get_value1() -> str:
    """
    说明:
        Dependency，获取匹配字符串中的value字段
    """

    async def dependency(regex_dict: dict = RegexDict()) -> str:

        value = regex_dict.get("value3")
        return value if value else regex_dict.get("value4")

    return Depends(dependency)


def get_profession() -> str:
    """
    说明:
        Dependency，通过别名获取职业名称
    """

    async def dependency(matcher: Matcher, name: str = get_value()) -> str:

        profession = JX3PROFESSION.get_profession(name)
        if profession:
            return profession

        # 未找到职业
        msg = f"未找到职业[{name}]，请检查参数。"
        await matcher.finish(msg)

    return Depends(dependency)
    
def get_qiyu() -> str:
    """
    说明:
        Dependency，通过别名获取奇遇名称
    """

    async def dependency(matcher: Matcher, name: str = get_value()) -> str:

        qiyu = JX3QIYU.get_qiyu(name)
        if qiyu:
            return qiyu

        # 未找到职业
        msg = f"未找到奇遇名[{name}]，请检查参数。"
        await matcher.finish(msg)

    return Depends(dependency)


def get_server_with_keyword() -> str:
    """
    说明:
        Dependency，获取server，会判断是不是keyword
    """

    async def dependency(
        matcher: Matcher, event: GroupMessageEvent, regex_dict: dict = RegexDict()
    ) -> str:
        _server = regex_dict.get("server2")
        if _server:
            server = api.app_server(name=_server)
            if not server:
                msg = f"未找到服务器[{_server}]，请验证后查询。"
                await matcher.finish(msg)
            else:
                return server
        else:
            _server = regex_dict.get("server1")
            if _server:
                # 判断server是不是keyword
                server = api.app_server(name=_server)
                if not server:
                    server = await GroupInfo.get_server(event.group_id)
            else:
                # 单招募
                server = await GroupInfo.get_server(event.group_id)
            return server

    return Depends(dependency)


def get_keyword() -> str:
    """
    说明:
        Dependency，招募查询-关键字
    """

    async def dependency(regex_dict: dict = RegexDict()) -> Optional[str]:
        if _keyword := regex_dict.get("keyword"):
            return _keyword
        if _keyword := regex_dict.get("server1"):
            if api.app_server(name=_keyword):
                keyword = None
            else:
                keyword = _keyword
        else:
            keyword = None
        return keyword

    return Depends(dependency)


def cold_down(name: str, cd_time: int) -> None:
    """
    说明:
        Dependency，增加命令冷却，同时会在数据库中记录一次查询
    参数:
        * `name`：app名称，相同名称会使用同一组cd
        * `cd_time`：冷却时间
    用法:
    ```
        @matcher.handle(parameterless=[cold_down(name="app", cd_time=0)])
        async def _():
            pass
    ```
    """

    async def dependency(matcher: Matcher, event: GroupMessageEvent):
        time_last = await SearchRecord.get_search_time(event.group_id, name)
        time_now = int(time.time())
        over_time = over_time = time_now - time_last
        if over_time > cd_time:
            await SearchRecord.use_search(event.group_id, name)
            return
        else:
            left_cd = cd_time - over_time
            await matcher.finish(f"[{name}]冷却中 ({left_cd})")

    return Depends(dependency)


# ----------------------------------------------------------------
#   handler列表，具体实现回复内容
# ----------------------------------------------------------------

@home_flower.handle(parameterless=[cold_down(name="鲜花价格", cd_time=0)])
async def _(event: GroupMessageEvent, robot: str = "@By憨仔",server: str = get_server()) -> NoReturn:
    """鲜花价格"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 鲜花价格 | 请求：{server}, {robot}")
    response = await api.view_home_flower(robot=robot,server=server)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await home_flower.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await home_flower.finish(msg)

@daily_query.handle(parameterless=[cold_down(name="日常查询", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server(), robot: str = "By憨仔") -> NoReturn:
    """日常查询"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 日常查询 | 请求：{server}, {robot}"
    )
    response = await api.view_active_current(server=server,robot=robot)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await daily_query.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await rank_excellent.finish(msg)


@daily_view.handle(parameterless=[cold_down(name="日常预测", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server(), robot: str = "@By憨仔") -> NoReturn:
    """日常预测"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 日常预测 | 请求：{server}, {robot}")
    response = await api.view_active_calendar(server=server,robot=robot)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await daily_view.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await daily_view.finish(msg)

@items_collect.handle(parameterless=[cold_down(name="掉落汇总", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server(), robot: str = "@By憨仔") -> NoReturn:
    """掉落汇总"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 掉落汇总 | 请求：{server}, {robot}")
    response = await apicss.view_valuables_collect(server=server,robot=robot)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await items_collect.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await items_collect.finish(msg)


@items_statistical.handle(parameterless=[cold_down(name="掉落统计", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server(), robot: str = "@By憨仔",name: str = get_value()) -> NoReturn:
    """掉落统计"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 掉落统计 | 请求：{server}, {robot}, {name}")
    response = await apicss.view_valuables_statistical(server=server,robot=robot,name=name)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await items_statistical.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await items_statistical.finish(msg)


@server_query.handle(parameterless=[cold_down(name="开服查询", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server()) -> NoReturn:
    """开服查询"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 开服查询 | 请求：{server}"
    )
    response = await api.data_server_check(server=server)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await server_query.finish(msg)

    data = response.data
    status = "已开服" if data["status"] == 1 else "维护中"
    msg = f"{server} 当前状态是[{status}]"
    await server_query.finish(msg)


@gold_query.handle(parameterless=[cold_down(name="金价查询", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server(),robot: str = "@By憨仔") -> NoReturn:
    """金价查询"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 金价查询 | 请求：{server}, {robot}")
    response = await api.view_trade_demon(robot=robot,server=server)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await gold_query.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await gold_query.finish(msg)


@zhenyan_query.handle(parameterless=[cold_down(name="阵眼查询", cd_time=0)])
async def _(event: GroupMessageEvent, name: str = get_profession()) -> NoReturn:
    """阵眼查询"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 阵眼查询 | 请求：{name}")
    response = await api.data_school_matrix(name=name)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await zhenyan_query.finish(msg)

    data = response.data
    msg = f"{name}：【{data.get('skillName')}】\n"
    descs: list[dict] = data.get("descs")
    for i in descs:
        msg += f"{i.get('name')}：{i.get('desc')}\n"
    await zhenyan_query.finish(msg)


@update_query.handle(parameterless=[cold_down(name="更新公告", cd_time=0)])
async def _(event: GroupMessageEvent) -> NoReturn:
    """更新公告"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 更新公告查询")
    url = "https://jx3.xoyo.com/launcher/update/latest.html"
    img = await browser.get_image_from_url(url=url, width=130, height=480)
    msg = MessageSegment.image(img)
    log = f"群{event.group_id} | 查询更新公告"
    logger.info(log)
    await update_query.finish(msg)


@saohua_query.handle(parameterless=[cold_down(name="骚话", cd_time=0)])
async def _(event: GroupMessageEvent) -> NoReturn:
    """骚话"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 骚话 | 请求骚话")
    response = await api.data_saohua_random()
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await saohua_query.finish(msg)

    data = response.data
    await saohua_query.finish(data["text"])


@sand_query.handle(parameterless=[cold_down(name="沙盘", cd_time=10)])
async def _(event: GroupMessageEvent, robot: str = "@By憨仔",server: str = get_server(), show: str = "1") -> NoReturn:
    """沙盘"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 沙盘查询 {robot},{show},{server}"
    )
    response = await api.view_server_sand(server=server,robot=robot,show=show)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await saohua_query.finish(msg)

    data = response.data
    url = data.get("url")
    await sand_query.finish(MessageSegment.image(url))


@price_query.handle(parameterless=[cold_down(name="物价查询", cd_time=0)])
async def _(event: GroupMessageEvent, robot: str = "@By憨仔",name: str = get_value()) -> NoReturn:
    """物价查询"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 物价查询 | 请求：{robot}, {name}")
    response = await api.view_trade_record(robot=robot,name=name)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await price_query.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await price_query.finish(msg)


# -------------------------------------------------------------
#   下面是使用模板生成的图片事件
# -------------------------------------------------------------


@serendipity_query.handle(parameterless=[cold_down(name="角色奇遇", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
    name: str = get_value(),
    # filter: str = "1",
) -> NoReturn:
    """角色奇遇查询"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 角色奇遇查询 | 请求：server:{server},name:{name}"
    )

    ticket = await TicketInfo.get_ticket()
    response = await api.data_luck_adventure(server=server, name=name, ticket=ticket)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await serendipity_query.finish(msg)

    data = response.data
    pagename = "角色奇遇.html"
    get_data = source.handle_data_event(data)
    img = await browser.template_to_image(
        pagename=pagename, server=server, name=name, data=get_data
    )
    await serendipity_query.finish(MessageSegment.image(img))

# @serendipity_query.handle(parameterless=[cold_down(name="角色奇遇", cd_time=10)])
# async def _(
#     event: GroupMessageEvent, 
#     server: str = get_server(), 
#     robot: str = "@By憨仔", 
#     filter: str = "1",
#     name: str = get_value(),
# ) -> NoReturn:
#     """角色奇遇查询"""
#     logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 角色奇遇查询 | 请求：{server},{name},{robot},{filter}")
#     response = await api.view_luck_adventure(robot=robot,server=server,name=name,filter=filter)
#     if response.code != 200:
#         msg = f"查询失败，{response.msg}"
#         await serendipity_query.finish(msg)

#     data = response.data
#     url = data.get("url")
#     msg = MessageSegment.image(url)
#     await serendipity_query.finish(msg)


@serendipity_list_query.handle(parameterless=[cold_down(name="奇遇统计", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
    name: str = get_value(),
) -> NoReturn:
    """奇遇统计查询"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 奇遇统计查询 | 请求：server:{server},serendipity:{name}"
    )
    response = await api.data_luck_statistical(server=server, name=name)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await serendipity_list_query.finish(msg)

    data = response.data
    pagename = "奇遇统计.html"
    get_data = source.handle_data_event_list(data)
    img = await browser.template_to_image(
        pagename=pagename, server=server, name=name, data=get_data
    )
    await serendipity_list_query.finish(MessageSegment.image(img))


@serendipity_summary_query.handle(parameterless=[cold_down(name="奇遇汇总", cd_time=10)])
async def _(event: GroupMessageEvent, server: str = get_server()) -> NoReturn:
    """奇遇汇总查询"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 奇遇汇总查询 | 请求：{server}"
    )
    response = await api.data_luck_collect(server=server)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await serendipity_summary_query.finish(msg)

    data = response.data
    pagename = "奇遇汇总.html"
    get_data = source.handle_data_event_summary(data)
    img = await browser.template_to_image(
        pagename=pagename, server=server, data=get_data
    )
    await serendipity_summary_query.finish(MessageSegment.image(img))


@match_query.handle(parameterless=[cold_down(name="战绩查询", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
    name: str = get_value(),
) -> NoReturn:
    """战绩查询"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 战绩查询 | 请求：server:{server},name:{name}"
    )
    ticket = await TicketInfo.get_ticket()
    response = await api.data_match_recent(server=server, name=name, ticket=ticket)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await match_query.finish(msg)

    data = response.data
    pagename = "比赛记录.html"
    get_data = source.handle_data_match(data)
    img = await browser.template_to_image(
        pagename=pagename, server=server, name=name, data=get_data
    )
    await match_query.finish(MessageSegment.image(img))

# @match_query.handle(parameterless=[cold_down(name="战绩查询", cd_time=10)])
# async def _(
#     event: GroupMessageEvent,  
#     robot: str = "@By憨仔", 
#     # server: str = get_server_with_keyword(),
#     server: str = get_server(),
#     name:str = get_value(),
#     # mode: str = get_value1(),
# ) -> NoReturn:
#     """战绩查询"""
#     logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 战绩查询 | 请求：{robot},{server},{name}")
#     ticket = await TicketInfo.get_ticket()
#     response = await api.view_match_recent(robot=robot,server=server,name=name,ticket=ticket)
#     if response.code != 200:
#         msg = f"查询失败，{response.msg}"
#         await match_query.finish(msg)

#     data = response.data
#     url = data.get("url")
#     msg = MessageSegment.image(url)
#     await match_query.finish(msg)

@equip_query.handle(parameterless=[cold_down(name="装备属性", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
    name: str = get_value(),
) -> NoReturn:
    """装备属性查询"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 装备属性查询 | 请求：server:{server},name:{name}"
    )
    ticket = await TicketInfo.get_ticket()
    response = await api.data_role_attribute(server=server, name=name, ticket=ticket)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await equip_query.finish(msg)

    data = response.data
    forceName:str=data.get("forceName")
    bodyName:str=data.get("bodyName")
    campName:str=data.get("campName")
    pagename = "角色装备.html"
    get_data = source.handle_data_equip(data)
    img = await browser.template_to_image(
        pagename=pagename, 
        server=server, 
        name=name, 
        data=get_data,
        forceName=forceName, 
        bodyName=bodyName,
        campName=campName,
    )
    await equip_query.finish(MessageSegment.image(img))


@firework_query.handle(parameterless=[cold_down(name="烟花记录", cd_time=10),cost_gold(gold=100)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
    name: str = get_value(),
) -> NoReturn:
    """烟花记录查询"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 烟花记录查询 | 请求：server:{server},name:{name}"
    )
    response = await apicss.data_watch_record(server=server, name=name)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await firework_query.finish(msg)

    data = response.data
    get_data = source.handle_data_firework(data)
    pagename = "烟花记录.html"
    img = await browser.template_to_image(
        pagename=pagename, server=server, name=name, data=get_data
    )
    await firework_query.finish(MessageSegment.image(img))
    

@recruit_query.handle(parameterless=[cold_down(name="招募查询", cd_time=10)])
async def _(
    event: GroupMessageEvent, 
    server: str = get_server_with_keyword(), 
    robot: str = "@By憨仔", 
    keyword: Optional[str] = get_keyword(),
) -> NoReturn:
    """招募查询"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 招募查询 | 请求：{server},{robot}, {keyword}")
    response = await api.view_member_recruit(robot=robot,server=server,keyword=keyword)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await recruit_query.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await recruit_query.finish(msg)
    

@teamCdList_query.handle(parameterless=[cold_down(name="副本记录", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
	name: str = get_value(),
) -> NoReturn:
    """副本记录"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 副本记录 | 请求：server:{server},name:{name}"
    )
    ticket = await TicketInfo.get_ticket()
    response = await api.data_role_teamCdList(server=server, name=name,ticket=ticket)
    responses = await api.data_saohua_random()
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await teamCdList_query.finish(msg)

    data = response.data
    texts = responses.data
    text = texts.get("text")
    servername:str=data.get("serverName")
    rolename:str=data.get("roleName")
    forceName:str=data.get("forceName")
    bodyName:str=data.get("bodyName")
    campName:str=data.get("campName")
    data: list[dict] = data.get("data")
    num = len(data)
    get_data = source.handle_data_teamCdList(data)
    pagename = "副本记录.html"
    img = await browser.template_to_image(
        pagename=pagename,
        servername=servername,
        rolename=rolename,
        forceName=forceName,
        bodyName=bodyName,
        campName=campName,
        data=get_data,
        text=text,
        num=num,
    )
    await teamCdList_query.finish(MessageSegment.image(img))
    

@active_monster.handle(parameterless=[cold_down(name="百战异闻录", cd_time=10),cost_gold(gold=300)])
async def _(
    event: GroupMessageEvent,  
    robot: str = "@By憨仔", 
) -> NoReturn:
    """百战异闻录"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 百战异闻录 | 请求：{robot}")
    response = await apicss.view_active_monster(robot=robot)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await active_monster.finish(msg)

    data = response.data
    url = data.get("url")
    IMAGE_PATH = Path() / "data" 
    r = requests.get(url)
    with open(f'{IMAGE_PATH}/image/baizhan.image', 'wb') as file:
        file.write(r.content)
    msg = MessageSegment.image(url)
    await active_monster.finish(msg)
    
    
@role_achievement.handle(parameterless=[cold_down(name="角色成就进度", cd_time=10)])
async def _(
    event: GroupMessageEvent,  
    robot: str = "@By憨仔", 
    server: str = get_server_with_keyword(),
    role:str = get_value(),
    cache: str = "0",
    name: str = get_value1(),
) -> NoReturn:
    """角色成就进度"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 角色成就进度 | 请求：{robot},{server},{role},{name},{cache}")
    ticket = await TicketInfo.get_ticket()
    response = await api.view_role_achievement(robot=robot,server=server,name=name,role=role,ticket=ticket,cache=cache)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await role_achievement.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await role_achievement.finish(msg)

@zili_query.handle(parameterless=[cold_down(name="资历排行", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server_with_keyword(),
    kungfu: Optional[str] = get_keyword(),
) -> NoReturn:
    """资历榜"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 资历排行 | 请求：server:{server},kunfu:{kungfu}"
    )
    ticket = await TicketInfo.get_ticket()
    if not kungfu:
        kungfu = "ALL"
    response = await api.data_school_seniority(
        server=server, school=kungfu, ticket=ticket
    )
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await zili_query.finish(msg)

    data = response.data
    pagename = "资历排行.html"
    img = await browser.template_to_image(
        pagename=pagename,
        server=server,
        data=data,
    )
    await zili_query.finish(MessageSegment.image(img))

@rank_excellent.handle(parameterless=[cold_down(name="风云榜单", cd_time=10)])
async def _(
    event: GroupMessageEvent,  
    robot: str = "@By憨仔", 
    server: str = get_server_with_keyword(),
    table:str = get_value(),
    name: str = get_value1(),
) -> NoReturn:
    """风云榜单"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 风云榜单 | 请求：{robot},{server},{table},{name}")
    response = await api.view_rank_statistical(robot=robot,server=server,name=name,table=table)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await rank_excellent.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await rank_excellent.finish(msg)

@active_chivalrous.handle(parameterless=[cold_down(name="楚天社进度", cd_time=0)])
async def _(event: GroupMessageEvent, name: str = "楚天社进度",ver: str = "1") -> NoReturn:
    """楚天社进度"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 楚天社进度 | 请求：{name}, {ver}")
    response = await api.data_active_celebrities(ver=ver)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await active_chivalrous.finish(msg)

    data = response.data
    time_now = datetime.now().strftime("%H:%M:%S")
    time_nows = datetime.now().strftime("%H:%M")
    pagename = "楚天社.html"
    img = await browser.template_to_image(
        pagename=pagename, data=data, time_now=time_now, time_nows=time_nows
    )
    await active_chivalrous.finish(MessageSegment.image(img))
    
@data_chivalrous.handle(parameterless=[cold_down(name="云从社进度", cd_time=0)])
async def _(event: GroupMessageEvent, name: str = "云从社进度",ver: str = "3") -> NoReturn:
    """云从社进度"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 云从社进度 | 请求：{name}, {ver}")
    response = await api.data_active_celebrities(ver=ver)
    responses = await api.data_saohua_random()
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await data_chivalrous.finish(msg)

    data = response.data
    texts = responses.data
    text = texts.get("text")
    time_now = datetime.now().strftime("%H:%M:%S")
    time_nows = datetime.now().strftime("%H:%M")
    pagename = "云从社.html"
    img = await browser.template_to_image(
        pagename=pagename, data=data, time_now=time_now, time_nows=time_nows,text=text
    )
    await data_chivalrous.finish(MessageSegment.image(img))

@exam_answer.handle(parameterless=[cold_down(name="科举试题", cd_time=0)])
async def _(event: GroupMessageEvent,match: str = get_value()) -> NoReturn:
    """科举试题"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 科举试题 | 请求：{match}")
    response = await api.data_exam_answer(match=match)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await exam_answer.finish(msg)

    data = response.data
    msg = f""
    for one in data:
        msg += f"{one.get('question')} 答案：{one.get('answer')}\n"
    await exam_answer.finish(msg)

# @member_student.handle(parameterless=[cold_down(name="拜师列表", cd_time=10), cost_gold(gold=100)])
# async def _(
#     event: GroupMessageEvent,
#     server: str = get_server_with_keyword(),
#     keyword: Optional[str] = get_keyword(),
# ) -> NoReturn:
#     """拜师列表"""
#     logger.info(
#         f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 拜师列表 | 请求：server:{server},keyword:{keyword}"
#     )
#     response = await apicss.data_member_teacher(server=server, keyword=keyword)
#     if response.code != 200:
#         msg = f"查询失败，{response.msg}"
#         await member_student.finish(msg)

#     data = response.data
#     server:str=data.get("server")
#     pagename = "拜师列表.html"
#     img = await browser.template_to_image(
#         pagename=pagename,
#         server=server,
#         data=data,
#     )
#     await member_student.finish(MessageSegment.image(img))

# @member_teacher.handle(parameterless=[cold_down(name="收徒列表", cd_time=10), cost_gold(gold=100)])
# async def _(
#     event: GroupMessageEvent,
#     server: str = get_server_with_keyword(),
#     keyword: Optional[str] = get_keyword(),
# ) -> NoReturn:
#     """收徒列表"""
#     logger.info(
#         f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 收徒列表 | 请求：server:{server},keyword:{keyword}"
#     )
#     response = await apicss.data_member_student(server=server, keyword=keyword)
#     if response.code != 200:
#         msg = f"查询失败，{response.msg}"
#         await member_teacher.finish(msg)

#     data = response.data
#     server:str=data.get("server")
#     pagename = "收徒列表.html"
#     img = await browser.template_to_image(
#         pagename=pagename,
#         server=server,
#         data=data,
#     )
#     await member_teacher.finish(MessageSegment.image(img))

@other_pendant.handle(parameterless=[cold_down(name="挂件详情", cd_time=0)])
async def _(event: GroupMessageEvent, name: str = get_value()) -> NoReturn:
    """挂件详情"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 挂件详情 | 请求：{name}")
    response = await api.data_other_pendant(name=name)
    responses = await api.data_saohua_random()
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await other_pendant.finish(msg)

    data = response.data
    texts = responses.data
    text = texts.get("text")
    pagename = "挂件详情.html"
    img = await browser.template_to_image(
        pagename=pagename,
        data=data,
        text=text,
    )
    await other_pendant.finish(MessageSegment.image(img))

@token_count.handle(parameterless=[cold_down(name="V2剩余次数", cd_time=0)])
async def _(event: GroupMessageEvent, name: str = "V2剩余次数",token: str = "v2a9d722fe48614a90") -> NoReturn:
    """V2剩余次数"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | V2剩余次数 | 请求：{name}",{token})
    response = await apicss.data_token_web_token(token=token)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await token_count.finish(msg)

    data = response.data
    # limit:str=data.get("limit")
    limit = data.get("limit")
    msg = f"剩余次数：{limit}"
    await token_count.finish(msg)


@role_roleInfo.handle(parameterless=[cold_down(name="角色信息", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server(),name: str = get_value(),) -> NoReturn:
    """角色信息"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 角色信息 | 请求：{name},{server}")
    response = await api.data_role_detailed(server=server,name=name)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await role_roleInfo.finish(msg)

    data = response.data
    # url = data.get("personAvatar")
    # msg = MessageSegment.image(url)
    msg = (
        f'推栏名称：{data.get("personName")}\n'
        f'{data.get("zoneName")}：{data.get("serverName")}\n'
        f'角色名称：{data.get("roleName")}\n'
        f'角色门派：{data.get("forceName")}\n'
        f'角色体型：{data.get("bodyName")}\n'
        f'角色阵营：{data.get("campName")}\n'
        f'数字标识：{data.get("roleId")}\n'
        f'全服标识：{data.get("globalRoleId")}\n'
        
    )
    await role_roleInfo.finish(msg)

@save_roleInfo.handle(parameterless=[cold_down(name="角色信息更新", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server(),roleId: str = get_value(),) -> NoReturn:
    """角色信息更新"""
    ticket = await TicketInfo.get_ticket()
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 角色信息更新 | 请求：{roleId},{server},{ticket}")
    response = await api.data_save_detailed(server=server,roleId=roleId,ticket=ticket)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await save_roleInfo.finish(msg)

    data = response.data
    # url = data.get("personAvatar")
    # msg = MessageSegment.image(url)
    msg = (
        f'{data.get("zoneName")}：{data.get("serverName")}\n'
        f'角色名称：{data.get("roleName")}\n'
        f'角色门派：{data.get("forceName")}\n'
        f'角色体型：{data.get("bodyName")}\n'
        f'数字标识：{data.get("roleId")}\n'
        f'全服标识：{data.get("globalRoleId")}\n'
        # f'角色阵营：{data.get("campName")}\n'
        # f'推栏名称：{data.get("personName")}'
    )
    await save_roleInfo.finish(msg)
    

@macro_query.handle(parameterless=[cold_down(name="查宏命令", cd_time=0)])
async def _(event: GroupMessageEvent, name: str = get_profession()) -> NoReturn:
    """查宏命令"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 查宏命令 | 请求：{name}")

    tname = urllib.parse.quote_plus(name)
    print(tname)
    msg = f"{name}宏：https://www.jx3box.com/macro/?subtype={tname}"
    await macro_query.finish(msg)


@tieba_random.handle(parameterless=[cold_down(name="八卦帖子", cd_time=0)])
async def _(event: GroupMessageEvent, server: str = get_server(), subclass: str = get_value()) -> NoReturn:
    """八卦帖子"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 八卦帖子 | 请求：{server},{subclass}"
    )
    response = await api.data_tieba_random(server=server,subclass=subclass)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await tieba_random.finish(msg)

    data = response.data
    title = data[0].get('title')
    url: list[dict] = data[0].get('url')
    name: list[dict] = data[0].get('name')
    msg = f'{title}\n 链接：https://tieba.baidu.com/p/{url}\n 来自：{name}吧'
    await tieba_random.finish(msg)

@server_antivice.handle(parameterless=[cold_down(name="诛恶事件历史记录", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    name: str = "By憨仔",
    server: str = get_server(),
) -> NoReturn:
    """诛恶事件历史记录"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 诛恶事件历史记录 | 请求：{name},{server}"
    )
    response = await api.data_server_antivice()
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await server_antivice.finish(msg)

    data = response.data
    server = server
    get_data = source.handle_server_antivice(data)
    pagename = "诛恶事件.html"
    img = await browser.template_to_image(
        pagename=pagename, server = server, data=get_data
    )
    await server_antivice.finish(MessageSegment.image(img))

@trade_market.handle(parameterless=[cold_down(name="交易行价格", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    name: str = get_value(),
	server: str = get_server(),
) -> NoReturn:
    """交易行价格"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 交易行价格 | 请求：{name},{server}"
    )
    response = await api.data_trade_market(name=name,server=server)
    responses = await api.data_saohua_random()
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await trade_market.finish(msg)

    data = response.data
    texts = responses.data
    text = texts.get("text")
    server = server
    get_data = source.handle_trade_marketa(data)
    pagename = "交易行.html"
    img = await browser.template_to_image(
        pagename=pagename, data=get_data, server=server, text=text
    )
    await trade_market.finish(MessageSegment.image(img))

@active_baizhan.handle(parameterless=[cold_down(name="百战异闻录V", cd_time=10)])
async def _(
    event: GroupMessageEvent,  
    robot: str = "@By憨仔", 
) -> NoReturn:
    """百战异闻录V"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 百战异闻录V | 请求：{robot}")


    IMAGE_PATH = Path() / "data" /"image"/f"baizhan.image"
    msg = MessageSegment.image(IMAGE_PATH)
    await active_baizhan.finish(msg)
    
@active_jjc.handle(parameterless=[cold_down(name="名剑战绩", cd_time=10)])
async def _(
    event: GroupMessageEvent,  
    robot: str = "@By憨仔", 
    server: str = get_server_with_keyword(),
    name:str = get_value(),
    mode: str = get_value1(),
) -> NoReturn:
    """名剑战绩"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 名剑战绩 | 请求：{robot},{server},{name},{mode}")
    ticket = await TicketInfo.get_ticket()
    response = await api.view_match_recent(robot=robot,server=server,name=name,mode=mode,ticket=ticket)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await active_jjc.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await active_jjc.finish(msg)

@match_awesome.handle(parameterless=[cold_down(name="名剑排行", cd_time=10)])
async def _(
    event: GroupMessageEvent,  
    robot: str = "@By憨仔", 
    mode: str = get_value(),
) -> NoReturn:
    """名剑排行"""
    logger.info(f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 名剑排行 | 请求：{robot},{mode}")
    ticket = await TicketInfo.get_ticket()
    response = await api.view_match_awesome(robot=robot,mode=mode,ticket=ticket)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await match_awesome.finish(msg)

    data = response.data
    url = data.get("url")
    msg = MessageSegment.image(url)
    await match_awesome.finish(msg)

@valuables_statistical.handle(parameterless=[cold_down(name="掉落统计V", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
    name: str = get_value(),
) -> NoReturn:
    """掉落统计V"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 掉落统计V | 请求：{name},{server}"
    )
    response = await apicss.data_valuables_statistical(name=name,server=server)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await valuables_statistical.finish(msg)

    data = response.data
    server = server
    name=name
    get_data = source.handle_valuables_statistical(data)
    pagename = "掉落统计.html"
    img = await browser.template_to_image(
        pagename=pagename, data=get_data,server = server,name=name
    )
    await valuables_statistical.finish(MessageSegment.image(img))

@data_dilu.handle(parameterless=[cold_down(name="的卢", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
) -> NoReturn:
    """的卢"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 的卢 | 请求：{server}"
    )
    response = await apicss.data_horse_records(server=server)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await data_dilu.finish(msg)

    data = response.data
    server = server
    get_data = source.handle_dilu(data)
    pagename = "的卢.html"
    img = await browser.template_to_image(
        pagename=pagename, data=get_data,server = server
    )
    await data_dilu.finish(MessageSegment.image(img))

    
@data_duowan.handle(parameterless=[cold_down(name="统战歪歪", cd_time=10), cost_gold(gold=500)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
) -> NoReturn:
    """统战歪歪"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 统战歪歪 | 请求：{server}"
    )
    response = await apicss.data_duowan_statistical(server=server)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await data_duowan.finish(msg)

    data = response.data
    server = server
    # get_data: str = data.get('data')
    msg = f"服务器：{server}\n"
    get_data: list[dict] = data.get('data')
    for i in get_data:
        msg += f"{i.get('snick')}\n频道标识：{i.get('sid')}"
    
    await data_duowan.finish(msg)
    # get_data: list[dict] = data.get("data")
    # pagename = "统战歪歪.html"
    # img = await browser.template_to_image(
    #     pagename=pagename, get_data=get_data, server=server
    # )
    # await data_duowan.finish(MessageSegment.image(img))

@data_event.handle(parameterless=[cold_down(name="马驹刷新", cd_time=10)])
async def _(
    event: GroupMessageEvent,
    server: str = get_server(),
) -> NoReturn:
    """马驹刷新"""
    logger.info(
        f"<y>群{event.group_id}</y> | <g>{event.user_id}</g> | 马驹刷新 | 请求：{server}"
    )
    response = await api.data_other_event(server=server)
    if response.code != 200:
        msg = f"查询失败，{response.msg}"
        await data_event.finish(msg)

    data = response.data
    print(data)
    server = server
    tip = data[0].get('tip')
    msg = f"{server}·马场告示\n-------------------------------\n"
    for i in data:
        desc = i.get("desc")
        desc2 = str(desc).replace("['","").replace("']","").replace("', '","\n")
        print(desc2)
        msg += f'{i.get("name")}\n{desc2}\n-------------------------------\n'
    msg +=f'{tip}'
    await data_event.finish(msg)
    
@help.handle()
async def _(event: GroupMessageEvent) -> NoReturn:
    """功能"""
    flag = bool(api.config.api_token)
    pagename = "查询帮助.html"
    img = await browser.template_to_image(pagename=pagename, flag=flag)
    await help.finish(MessageSegment.image(img))
