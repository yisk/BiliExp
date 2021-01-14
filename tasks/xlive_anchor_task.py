from BiliClient import asyncbili
from typing import AsyncGenerator, Dict, Any, List, Union
import logging, asyncio, time, traceback
from aiohttp.client_exceptions import ServerDisconnectedError
from async_timeout import timeout

async def xlive_anchor_task(biliapi: asyncbili,
                            task_config: Dict[str, Any]
                            ) -> None:
    Timeout = task_config.get("timeout", 850)
    delay = task_config.get("delay", 0)
    save_map = {} #id:(roomid, uid)
    is_followed = True
    try:
        async with timeout(Timeout):
            while True:
                for area in task_config["searche_areas"]:
                    async for room in xliveRoomGenerator(biliapi, area["paid"], area["aid"], area["sort"], area["ps"]):
                        if '2' in room["pendant_info"] and room["pendant_info"]["2"]["pendent_id"] == 504: #判断房间是否有天选时刻
                            if delay:
                                await asyncio.sleep(delay)

                            bl, anchor = await getAnchorInfo(biliapi, room["roomid"]) #获取天选信息
                            if not bl:
                                continue

                            if anchor["status"] != 1: #排除重复参加
                                continue

                            if anchor["id"] in save_map: #排除重复参加
                                continue

                            if not isJoinAnchor(anchor, task_config): #过滤条件
                                save_map[anchor["id"]] = None
                                continue

                            if task_config["unfollow"]:
                                is_followed = await isUserFollowed(biliapi, room["uid"])

                            await anchorJoin(biliapi, anchor, room, is_followed, save_map) #参加天选时刻

                await asyncio.sleep(task_config["searche_interval"])
                await cleanMapWithUnfollow(biliapi, save_map)
    
    except asyncio.TimeoutError:
        logging.warning(f'{biliapi.name}: 天选时刻抽奖任务超时({Timeout}秒)')
    except Exception as e:
        logging.warning(f'{biliapi.name}: 天选时刻抽奖任务异常，异常为({traceback.format_exc()})')

    await cleanMapWithUnfollow(biliapi, save_map, True)

def isJoinAnchor(anchor: Dict[str, Any], 
                 condition: Dict[str, Any]
                 ) -> bool:
    if not anchor:
        return False
    if anchor["gift_price"] > condition["price_limit"]:
        return False
    if not [anchor["require_type"], anchor["require_value"]] in condition["anchor_type"]:
        return False
    if anchor["room_id"] in condition["room_filter"]:
        return False
    for gf in condition["gift_filter"]:
        if gf in anchor["award_name"]:
            return False
    for dm in condition["room_filter"]:
        if dm in anchor["danmu"]:
            return False
    return True

async def isUserFollowed(biliapi: asyncbili, 
                   uid: int
                   ) -> bool:
    '''判断是否关注用户'''
    try:
        ret = await biliapi.getRelationByUid(uid)
    except Exception as e:
        logging.warning(f'{biliapi.name}: 天选判断与用户{uid}的关注状态失败，原因为({str(e)})，默认未关注')
        return False
    else:
        if ret["code"] == 0:
            return ret["data"]["attribute"] == 2
        else:
            logging.warning(f'{biliapi.name}: 天选判断与用户{uid}的关注状态失败，原因为({ret["message"]})，默认未关注')
            return False

async def anchorJoin(biliapi: asyncbili, 
                     anchor: dict,
                     room: dict,
                     is_followed: bool,
                     save_map: dict
                     ):
    '''参加天选时刻'''
    try:
        ret = await biliapi.xliveAnchorJoin(anchor["id"], anchor["gift_id"], anchor["gift_num"])
    except Exception as e:
        logging.warning(f'{biliapi.name}: 参与直播间{room["roomid"]}的天选时刻{anchor["id"]}异常，原因为({str(e)})')
    else:
        if ret["code"] == 0:
            save_map[anchor["id"]] = (room["roomid"], room["uid"], anchor["current_time"]+anchor["time"],not is_followed and anchor["require_type"] == 1)
            logging.info(f'{biliapi.name}: 参与直播间{room["roomid"]}的天选时刻{anchor["id"]}({anchor["award_name"]})成功')

async def cleanMapWithUnfollow(biliapi: asyncbili, 
                        save_map: dict,
                        clean_all: bool = False
                        ) -> bool:
    now_time = int(time.time())
    for k in list(save_map.keys()):
        if save_map[k]:
            if clean_all or now_time > save_map[k][2]:
                if save_map[k][3]:
                    await biliapi.followUser(save_map[k][1], 0)
                    logging.info(f'{biliapi.name}: 取关主播{save_map[k][1]}')
                del save_map[k]

async def getAnchorInfo(biliapi: asyncbili, 
                        room_id: int
                        ) -> (bool, dict):
    '''获取房间天选时刻信息'''
    try:
        ret = await biliapi.getLotteryInfoWeb(room_id)
    except Exception as e:
        logging.warning(f'{biliapi.name}: 天选时刻抽奖任务获取直播间{room_id}抽奖信息异常，原因为({str(e)})')
        return False, None
    if ret["code"] != 0:
        logging.warning(f'{biliapi.name}: 天选时刻抽奖任务获取直播间{room["roomid"]}抽奖信息失败，信息为({ret["message"]})')
        return False, None
    return bool(ret["data"]["anchor"]), ret["data"]["anchor"]

async def xliveRoomGenerator(biliapi: asyncbili,
                             pAreaId: int,
                             AreaId: int,
                             sort: str,
                             page_num: int
                             ) -> AsyncGenerator:
    page = 0
    has_more = True
    while has_more:
        page += 1
        try:
            ret = await biliapi.xliveSecondGetList(pAreaId, AreaId, sort, page)
        except ServerDisconnectedError:
            logging.warning(f'{biliapi.name}: 获取直播间列表异常,原因为(服务器强制断开连接)')
            return
        except Exception as e:
            logging.warning(f'{biliapi.name}: 获取直播间列表异常,原因为({str(e)})')
            return
        else:
            if ret["code"] != 0:
                logging.warning(f'{biliapi.name}: 获取直播间列表失败,信息为({ret["message"]})')
                return

        for item in ret["data"]["list"]:
            yield item

        if page >= page_num:
            return

        has_more = ret["data"]["has_more"] == 1
