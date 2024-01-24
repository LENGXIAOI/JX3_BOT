import time
from datetime import datetime

from pydantic import parse_obj_as

from .config import FireWorkRecord, FireWorkRecords

# -------------------------------------------------------------
# 返回数据处理阶段，处理api返回data，方便模板使用
# -------------------------------------------------------------


def handle_data_price(data: list[list[dict]]) -> dict:
    """处理物价数据"""
    req_data = {}
    for one_data in data:
        for one_item in one_data:
            zone = one_item["zone"]
            if zone not in req_data:
                req_data[zone] = []
            req_data[zone].append(one_item)
    return req_data


def handle_data_event(data: list[dict]) -> dict:
    """处理角色奇遇"""
    world_event = []
    pet_event = []
    for one_data in data:
        get_time: int = one_data["time"]
        if get_time == 0:
            time_str = "未知"
            day = "遗忘的时间"
        else:
            time_now = datetime.now()
            time_pass = datetime.fromtimestamp(get_time)
            time_str = time_pass.strftime("%Y-%m-%d %H:%M:%S")
            day = f"{(time_now-time_pass).days} 天前"
        one_dict = {
            "time": time_str,
            "day": day,
            "event": one_data["event"],
            "level": one_data["level"],
        }
        level: int = one_data["level"]
        if level > 2:
            pet_event.append(one_dict)
        else:
            world_event.append(one_dict)
    req_data = {
        "world_event": world_event,
        "pet_event": pet_event,
        "num_world": len(world_event),
        "num_pet": len(pet_event),
    }
    return req_data


def handle_data_event_list(data: list[dict]) -> list[dict]:
    """处理奇遇统计数据"""
    req_data = []
    for one_data in data:
        get_time: int = one_data["time"]
        if get_time == 0:
            time_str = "未知"
            day = "遗忘的时间"
        else:
            time_now = datetime.now()
            time_pass = datetime.fromtimestamp(get_time)
            time_str = time_pass.strftime("%Y-%m-%d %H:%M:%S")
            day = f"{(time_now-time_pass).days} 天前"
        one_dict = {"time": time_str, "day": day, "name": one_data["name"]}
        req_data.append(one_dict)
    return req_data


def handle_data_event_summary(data: list[dict]) -> list[dict]:
    """处理奇遇汇总数据"""
    req_data = []
    for _data in data:
        one_data = _data["data"]
        get_time: int = one_data["time"]
        if get_time == 0:
            time_str = "遗忘的时间"
        else:
            time_pass = datetime.fromtimestamp(get_time)
            time_str = time_pass.strftime("%Y-%m-%d %H:%M:%S")
        one_dict = {
            "time": time_str,
            "count": _data["count"],
            "name": one_data["name"],
            "event": _data["event"],
        }
        req_data.append(one_dict)
    return req_data


def handle_data_match(data: dict) -> dict:
    """处理战绩数据"""
    req_data = {}
    req_data["performance"] = data["performance"]
    req_data["camp"] = data["campName"]
    history: list = data["history"]
    req_data["history"] = []
    for one_data in history:
        one_req_data = {}
        one_req_data["kungfu"] = one_data["kungfu"]
        one_req_data["avgGrade"] = one_data["avgGrade"]
        one_req_data["won"] = one_data["won"]
        one_req_data["totalMmr"] = one_data["totalMmr"]
        one_req_data["mmr"] = abs(one_data["mmr"])

        pvp_type = one_data.get("pvpType")
        if pvp_type == 2:
            one_req_data["pvpType"] = "2v2"
        elif pvp_type == 3:
            one_req_data["pvpType"] = "3v3"
        else:
            one_req_data["pvpType"] = "5v5"
        start_time = one_data.get("startTime")
        end_time = one_data.get("endTime")
        time_keep = end_time - start_time
        pvp_time = int((time_keep + 30) / 60)
        if pvp_time == 0:
            pvp_time = 1
        one_req_data["time"] = str(pvp_time) + " 分钟"

        time_now = time.time()
        time_ago = time_now - end_time
        if time_ago < 3600:
            # 一小时内用分钟表示
            time_end = int((time_ago + 30) / 60)
            if time_end == 0:
                time_end = 1
            one_req_data["ago"] = str(time_end) + " 分钟前"
        elif time_ago < 86400:
            # 一天内用小时表示
            time_end = int((time_ago + 1800) / 3600)
            if time_end == 0:
                time_end = 1
            one_req_data["ago"] = str(time_end) + " 小时前"
        elif time_ago < 864000:
            # 10天内用天表示
            time_end = int((time_ago + 43200) / 86400)
            if time_end == 0:
                time_end = 1
            one_req_data["ago"] = str(time_end) + " 天前"
        else:
            # 超过10天用日期表示
            timeArray = time.localtime(end_time)
            one_req_data["ago"] = time.strftime("%Y年%m月%d日", timeArray)
        req_data["history"].append(one_req_data)
    return req_data


def handle_data_equip(data: dict) -> dict:
    """处理装备属性"""
    req_data = {}
    req_data["kungfu"] = data["kungfuName"]
    info: dict = data["panelList"]
    if info:
        req_data["score"] = info.get("score")

        # 处理info数据
        info_panel: list[dict] = info.get("panel", [])
        data_info = []
        for one in info_panel:
            value = str(one["value"])
            if one["percent"]:
                value += "%"
            one_data = {"name": one["name"], "value": value}
            data_info.append(one_data)
        req_data["info"] = data_info

    color_level_map = {
        "0": "darkgray",
        "1": "gray",
        "2": "darkgreen",
        "3": "dodgerblue",
        "4": "blueviolet",
        "5": "chocolate",
    }
    # 处理equip数据
    equip: list[dict] = data["equipList"]
    data_equip = []
    for one in equip:
        _source = one.get("source")
        if _source is None:
            source = ""
        else:
            source = _source.split("；")[0]
        one_data = {
            "name": one["name"],
            "kind": one["kind"],
            "icon": one["icon"],
            "quality": one["quality"],
            "color": color_level_map.get(one["color"], "black"),
            "strengthLevel": int(one["strengthLevel"]),
            "source": source,
        }
        # 五行石图标
        five_stone: list = one.get("fiveStone")
        if five_stone is not None:
            one_data["fiveStone"] = [i["icon"] for i in five_stone]
        # 属性描述
        modifyType: list = one.get("modifyType")
        if modifyType is not None:
            name_list = [i["name"] for i in modifyType]
            one_data["modifyType"] = " ".join(name_list)
        # 附魔描述
        permanentEnchant: list = one.get("permanentEnchant")
        if permanentEnchant is not None:
            name_list = [i["name"] for i in permanentEnchant]
            one_data["permanentEnchant"] = " ".join(name_list)
        else:
            one_data["permanentEnchant"] = ""
        data_equip.append(one_data)
    req_data["equip"] = data_equip

    # 处理qixue数据
    qixue: list = data["qixueList"]
    data_qixue = []
    for one in qixue:
        # if one["name"] == "未知":
        #     continue
        one_data = {
            "name": one["name"],
            "icon": one["icon"],
        }
        data_qixue.append(one_data)
    req_data["qixue"] = data_qixue

    return req_data


def handle_data_firework(data: list[dict]) -> list[dict]:
    """处理烟花数据"""
    list_data = parse_obj_as(list[FireWorkRecord], data)
    req_data = []
    last = list_data[0]
    last.times -= 1
    # for one_data in data:
    #     get_time: int = one_data["time"]
    #     time_pass = datetime.fromtimestamp(get_time)
    #     time_str = time_pass.strftime("%Y-%m-%d %H:%M")
    #     one_dict = {
    #         "time": time_str,
    #     }
    #     req_data.append(one_dict)
    for one in list_data:
        if one == last:
            last.times += 1
        else:
            req_data.append(last.dict())
            last = one
    req_data.append(last.dict())
    return req_data


def handle_data_recruit(data: list[dict]) -> list[dict]:
    """处理招募信息"""
    req_data = []
    for one in data:
        one_data = {
            "activity": one.get("activity"),
            "level": one.get("level"),
            "leader": one.get("leader"),
            "createTime": datetime.fromtimestamp(one.get("createTime")).strftime(
                "%H:%M:%S"
            ),
            "number": f"{one.get('number')}/{one.get('maxNumber')}",
            "content": one.get("content"),
        }
        req_data.append(one_data)
    return req_data


def handle_data_teamCdList(data: list[dict]) -> list[dict]:
    """处理副本记录信息"""
    req_data = []
    for one in data:
        one_data = {
            "mapName": one["mapName"], #副本名称
            "mapType": one["mapType"], #副本等级
            "bossCount": one["bossCount"], #BOSS数量
            "bossFinished": one["bossFinished"], #已有CD的BOSS数量
            "bossProgress": one["bossProgress"], #BOSSCD详情
        }
        req_data.append(one_data)
    return req_data

def handle_data_monster(data: list[dict]) -> list[dict]:
    """处理百战异闻录信息"""
    req_data = []
    for one in data:
        one_data = {
            # "data": one ["data"],
            "index": one["index"], #位置信息
            "name": one["name"], #首领名称
            "extras": one["extras"], #携带BUFF
            # "extract": one["extract"], #buff效果简称
            "extract": "".join(str(i) for i in one["extract"]),
            "desc": one["desc"], #buff效果详情
        }
        req_data.append(one_data)
    return req_data

def handle_school_force(data: list[dict]) -> list[dict]:
    """处理奇穴效果信息"""
    req_data = []
    for one in data:
        one_data = {
            "name": one["name"], #奇穴名称
            "desc": one["desc"], #奇穴描述
            "kind": one["kind"], #类型
        }
        req_data.append(one_data)
    return req_data
    
def handle_server_antivice(data: list[dict]) -> list[dict]:
    """处理诛恶事件信息"""
    req_data = []
    for one in data:
        one_data = {
            "zone": one.get("zone"),
            "server": one.get("server"),
            "map_name": one.get("map_name"),
            "time": datetime.fromtimestamp(one.get("time")).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
        req_data.append(one_data)
    return req_data
    
def handle_valuables_statistical(data: list[dict]) -> list[dict]:
    """处理掉落统计信息"""
    req_data = []
    for one in data:
        one_data = {
            "zone": one.get("zone"),
            "server": one.get("server"),
            "role_name": one.get("role_name"),
            "map_name": one.get("map_name"),
            "name": one.get("name"),
            "time": datetime.fromtimestamp(one.get("time")).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
        req_data.append(one_data)
    return req_data

def handle_data_statistical(data: list[dict]) -> list[dict]:
    """处理统战歪歪信息"""
    req_data = []
    for one in data:
        one_data = {
            # "server": one["server"], #fuwuqi
            "data": one["data"], #xaingqing
        }
        req_data.append(one_data)
    return req_data
    
def handle_dilu(data: list[dict]) -> list[dict]:
    """处理的卢刷新信息"""
    req_data = []
    for one in data:
        one_data = {
            # "zone": one.get("zone"),
            "server": one.get("server"),
            "map_name": one.get("map_name"),
            "capture_role_name": one.get("capture_role_name"),
            "capture_camp_name": one.get("capture_camp_name"),
            "auction_role_name": one.get("auction_role_name"),
            "auction_camp_name": one.get("auction_camp_name"),
            "auction_amount": one.get("auction_amount"),
            "refresh_time": datetime.fromtimestamp(one.get("refresh_time")).strftime(
                "%Y-%m-%d %H:%M:%S"),
            "capture_time": datetime.fromtimestamp(one.get("capture_time")).strftime(
                "%Y-%m-%d %H:%M:%S"),
            "auction_time": datetime.fromtimestamp(one.get("auction_time")).strftime(
                "%Y-%m-%d %H:%M:%S"),
            "start_time": datetime.fromtimestamp(one.get("start_time")).strftime(
                "%Y-%m-%d %H"),
            "end_time": datetime.fromtimestamp(one.get("end_time")).strftime(
                "%Y-%m-%d %H"),
        }
        req_data.append(one_data)
    return req_data
    
def handle_trade_marketa(data: list[dict]) -> list[dict]:
    """处理副本记录信息"""
    req_data = []
    for one in data:
        one_data = {
            "name": one["name"], #物品名称
            "icon": one["icon"], #物品图片
            "data": one.get("data"), #价格列表
        }
        req_data.append(one_data)
    return req_data