from BiliClient import asyncbili, calc_sign
from .push_message_task import webhook
import logging, asyncio, uuid, time, aiohttp
from async_timeout import timeout

async def xlive_heartbeat_task(biliapi: asyncbili,
                               task_config: dict
                               ) -> None:
    timeout = task_config.get("timeout", task_config.get("time", 30)) * 60
    send_msg = task_config.get("send_msg", "")
    medal_room = task_config.get("medal_room", True)
    rooms_id = set(task_config.get("room_id", []))
    tasks = []
    rooms = await get_rooms(biliapi)
    if send_msg:
        tasks.append(send_msg_task(biliapi, rooms, send_msg))

    if medal_room:
        rooms_id |= set(rooms)

    tasks.extend([heartbeat_task(biliapi, x, timeout) for x in rooms_id])

    if tasks:
        await asyncio.wait(tasks)

async def get_rooms(biliapi: asyncbili):
    '''获取所有勋章房间'''
    result = []
    page = 1
    while True:
        try:
            ret = await biliapi.xliveFansMedal(page, 50)
        except Exception as e:
            logging.warning(f'{biliapi.name}: 获取有勋章的直播间异常，原因为{str(e)}')
            break
        else:
            if ret["code"] == 0:
                if not ret["data"]["fansMedalList"]:
                    break
                for medal in ret["data"]["fansMedalList"]:
                    if 'roomid' in medal:
                        result.append(medal["roomid"])
            else:
                logging.warning(f'{biliapi.name}: 获取有勋章的直播间失败，信息为{ret["message"]}')
                break
            page += 1

    return result

async def send_msg_task(biliapi: asyncbili,
                        rooms: list,
                        msg: str
                        ):
    su = 0
    for roomid in rooms:
        retry = 3
        while retry:
            await asyncio.sleep(3)
            try:
                ret = await biliapi.xliveMsgSend(roomid, msg)
            except Exception as e:
                logging.warning(f'{biliapi.name}: 直播在房间{roomid}发送信息异常，原因为{str(e)}，重试')
                retry -= 1
            else:
                if ret["code"] == 0:
                    if ret["message"] == '':
                        logging.info(f'{biliapi.name}: 直播在房间{roomid}发送信息成功')
                        su += 1
                        break
                    else:
                        logging.warning(f'{biliapi.name}: 直播在房间{roomid}发送信息，消息为{ret["message"]}，重试')
                        retry -= 1
                else:
                    logging.warning(f'{biliapi.name}: 直播在房间{roomid}发送信息失败，消息为{ret["message"]}，跳过')
                    break
    webhook.addMsg('msg_simple', f'{biliapi.name}:直播成功在{su}个房间发送消息\n')

async def heartbeat_task(biliapi: asyncbili,
                         room_id: int,
                         max_time: float
                         ):
    try:
        ret = await biliapi.xliveGetRoomInfo(room_id)
        if ret["code"] != 0:
            logging.info(f'{biliapi.name}: 直播请求房间信息失败，信息为：{ret["message"]}，跳过直播心跳')
            webhook.addMsg('msg_simple', f'{biliapi.name}:直播心跳失败\n')
            return
        parent_area_id = ret["data"]["room_info"]["parent_area_id"]
        area_id = ret["data"]["room_info"]["area_id"]
        room_id = ret["data"]["room_info"]["room_id"] #为了防止上面的id是短id，这里确保得到的是长id
    except Exception as e:
        logging.warning(f'{biliapi.name}: 直播请求房间信息异常，原因为{str(e)}，跳过直播心跳')
        webhook.addMsg('msg_simple', f'{biliapi.name}:直播心跳失败\n')
        return
    del ret
    try:
        buvid = await biliapi.xliveGetBuvid()
    except Exception as e:
        logging.warning(f'{biliapi.name}: 获取直播buvid异常，原因为{str(e)}，跳过直播心跳')
        webhook.addMsg('msg_simple', f'{biliapi.name}:直播心跳失败\n')
        return

    retry = 2
    ii = 0
    try:
        async with timeout(max_time):
            heart_beat = xliveHeartBeat(biliapi, buvid, parent_area_id, area_id, room_id)
            async for code, message, wtime in heart_beat: #每一次迭代发送一次心跳
                if code != 0:
                    if retry:
                        logging.warning(f'{biliapi.name}: 直播心跳错误，原因为{message}，重新进入房间')
                        heart_beat.reset()
                        retry -= 1
                        continue
                    else:
                        logging.warning(f'{biliapi.name}: 直播心跳错误，原因为{message}，跳过')
                        break
                ii += 1
                logging.info(f'{biliapi.name}: 成功在id为{room_id}的直播间发送第{ii}次心跳')
                await asyncio.sleep(wtime) #等待wtime秒进行下一次迭代

    except asyncio.TimeoutError:
        logging.info(f'{biliapi.name}: 直播{room_id}心跳超时退出')
    except Exception as e:
        logging.warning(f'{biliapi.name}: 直播{room_id}心跳异常，原因为{str(e)}，退出直播心跳')
        webhook.addMsg('msg_simple', f'{biliapi.name}:直播{room_id}心跳发生异常\n')

class xliveHeartBeat:
    '''B站心跳异步迭代器，每迭代一次发送一次心跳'''

    def __init__(self, biliapi: asyncbili, buvid: str, parent_area_id: int, area_id: int, room_id: int):
        self._biliapi = biliapi
        self._data = {
            "id": [parent_area_id, area_id, 0, room_id],
            "device": [buvid, str(uuid.uuid4())]
            }
        self._secret_rule: list = None

    def reset(self):
        '''重新进入房间心跳'''
        data = {
            "id": self._data["id"],
            "device": self._data["device"]
            }
        data["id"][2] = 0
        self._data = data

    def __aiter__(self):
        return self

    async def __anext__(self):
        
        if self._data["id"][2] == 0:   #第1次执行进入房间心跳 HeartBeatE
            ret = await self._biliapi.xliveHeartBeatE(**self._data)
            if ret["code"] == 0:
                self._data["ets"] = ret["data"]["timestamp"]
                self._data["benchmark"] = ret["data"]["secret_key"]
                self._data["time"] = ret["data"]["heartbeat_interval"]
                self._secret_rule = ret["data"]["secret_rule"]
                self._data["id"][2] += 1
            return ret["code"], ret["message"], ret["data"]["heartbeat_interval"]

        else:                          #第n>1次执行进入房间心跳 HeartBeatX
            self._data["ts"] = int(time.time() * 1000)
            self._data["s"] = calc_sign(self._data, self._secret_rule)
            ret = await self._biliapi.xliveHeartBeatX(**self._data)
            if ret["code"] == 0:
                self._data["ets"] = ret["data"]["timestamp"]
                self._data["benchmark"] = ret["data"]["secret_key"]
                self._data["time"] = ret["data"]["heartbeat_interval"]
                self._secret_rule = ret["data"]["secret_rule"]
                self._data["id"][2] += 1
            return ret["code"], ret["message"], ret["data"]["heartbeat_interval"]