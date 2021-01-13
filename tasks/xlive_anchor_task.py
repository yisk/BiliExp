from BiliClient import asyncbili
from typing import AsyncGenerator, Dict, Any, List, Union
import logging, asyncio
from aiohttp.client_exceptions import ServerDisconnectedError
from async_timeout import timeout

async def xlive_anchor_task(biliapi: asyncbili,
                                   task_config: Dict[str, Any]
                                   ) -> None:
    Timeout = task_config.get("timeout", 850)
    delay = task_config.get("delay", 0)
    save_map = {} #id:(roomid, uid)
    try:
        async with timeout(Timeout):
            async for room in searcheRoomGenerator(biliapi, task_config["searche_interval"], task_config["searche_areas"]):
                if '2' in room["pendant_info"] and room["pendant_info"]["2"]["pendent_id"] == 504:
                    if delay:
                        await asyncio.sleep(delay)
                    try:
                        ret = await biliapi.getLotteryInfoWeb(room["roomid"])
                    except Exception as e:
                        logging.warning(f'{biliapi.name}: 天选时刻抽奖任务获取直播间{room["roomid"]}抽奖信息异常，原因为({str(e)})')
                        continue
                    if ret["code"] != 0:
                        logging.warning(f'{biliapi.name}: 天选时刻抽奖任务获取直播间{room["roomid"]}抽奖信息失败，信息为({ret["message"]})')
                        continue
                    anchor = ret["data"]["anchor"]

                    if anchor["status"] != 1: #排除重复参加
                        continue

                    if anchor["id"] in save_map: #排除重复参加
                        continue

                    if not isJoinAnchor(anchor, task_config):
                        save_map[anchor["id"]] = None
                        continue
                    status = False
                    try:
                        ret = await biliapi.xliveAnchorJoin(anchor["id"], anchor["gift_id"], anchor["gift_num"])
                    except Exception as e:
                        logging.warning(f'{biliapi.name}: 参与直播间{room["roomid"]}的天选时刻{anchor["id"]}异常，原因为({str(e)})')
                    else:
                        if ret["code"] == 0:
                            save_map[anchor["id"]] = (room["roomid"], room["uid"])
                            logging.info(f'{biliapi.name}: 参与直播间{room["roomid"]}的天选时刻{anchor["id"]}({anchor["award_name"]})成功')
                            status = True
                        else:
                            save_map[anchor["id"]] = None
                            logging.warning(f'{biliapi.name}: 参与直播间{room["roomid"]}的天选时刻{anchor["id"]}失败，信息为({ret["message"]})')

                    if task_config["unfollow"] and status and anchor["require_type"] == 1:
                        await asyncio.sleep(6)
                        await biliapi.followUser(room["uid"], 0)
                        logging.info(f'{biliapi.name}: 取关主播{room["uid"]}')
    
    except asyncio.TimeoutError:
        logging.warning(f'{biliapi.name}: 天选时刻抽奖任务超时({Timeout}秒)退出')
    except Exception as e:
        logging.warning(f'{biliapi.name}: 天选时刻抽奖任务异常，原因为({str(e)})，退出任务')

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

async def searcheRoomGenerator(biliapi: asyncbili,
                               searche_interval: int,
                               searche_areas: List[Dict[str, Union[str, int]]],
                               ) -> AsyncGenerator:
    '''
    循环获取直播间(生成器)
    '''
    while True:
        for area in searche_areas:
            async for room in xliveRoomGenerator(biliapi, area["paid"], area["aid"], area["sort"], area["ps"]):
                yield room
        await asyncio.sleep(searche_interval)

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
