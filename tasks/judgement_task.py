from BiliClient import asyncbili
from .push_message_task import webhook
import logging, aiohttp, asyncio
from async_timeout import timeout

voteInfo = ("未投票", "封禁", "否认", "弃权", "删除")

async def judgement_task(biliapi: asyncbili, 
                         task_config: dict
                         ) -> None:
    '''风纪委员会投票任务'''
    try:
        ret = await biliapi.juryInfo()
    except Exception as e:
        logging.warning(f'{biliapi.name}: 获取风纪委员信息异常，原因为{str(e)}，跳过投票')
        webhook.addMsg('msg_simple', f'{biliapi.name}:风纪委投票失败\n')
        return
    if ret["code"] == 25005:
        logging.warning(f'{biliapi.name}: 风纪委员投票失败，请去https://www.bilibili.com/judgement/apply 申请成为风纪委员')
        webhook.addMsg('msg_simple', f'{biliapi.name}:不是风纪委\n')
        return
    elif ret["code"] != 0:
        logging.warning(f'{biliapi.name}: 风纪委员投票失败，信息为：{ret["msg"]}')
        webhook.addMsg('msg_simple', f'{biliapi.name}:风纪委投票失败\n')
        return
    if ret["data"]["status"] != 1:
        logging.warning(f'{biliapi.name}: 风纪委员投票失败，风纪委员资格失效')
        webhook.addMsg('msg_simple', f'{biliapi.name}:风纪委资格失效\n')
        return

    logging.warning(f'{biliapi.name}: 拥有风纪委员身份，开始获取案件投票，当前裁决正确率为：{ret["data"]["rightRadio"]}%')
    webhook.addMsg('msg_simple', f'{biliapi.name}:风纪委当前裁决正确率为：{ret["data"]["rightRadio"]}%\n')

    baiduNLPConfig = task_config.get("baiduNLP", None)
    params = task_config.get("params", {})
    vote_num = task_config.get("vote_num", 20)
    check_interval = task_config.get("check_interval", 420)
    Timeout = task_config.get("timeout", 850)

    su = 0
    try:
        async with timeout(Timeout):
            while su < vote_num:
                while True:
                    try:
                        ret = await biliapi.juryCaseObtain()
                    except Exception as e:
                        logging.warning(f'{biliapi.name}: 获取风纪委员案件异常，原因为{str(e)}，跳过本次投票')
                        break
                    if ret["code"] == 25008:
                        logging.warning(f'{biliapi.name}: 风纪委员没有新案件了')
                        break
                    elif ret["code"] == 25014:
                        logging.warning(f'{biliapi.name}: 风纪委员案件已审满')
                        break
                    elif ret["code"] != 0:
                        logging.warning(f'{biliapi.name}: 获取风纪委员案件失败，信息为：{ret["message"]}')
                        break
                    if await juryVote(biliapi, ret["data"]["id"], task_config["params"], baiduNLPConfig):
                        su += 1

                logging.info(f'{biliapi.name}: 风纪委员投票等待{check_interval}s后继续获取案件')
                await asyncio.sleep(check_interval)

    except asyncio.TimeoutError:
        logging.warning(f'{biliapi.name}: 风纪委员投票任务超时({Timeout}秒)退出')

    webhook.addMsg('msg_simple', f'{biliapi.name}:风纪委投票成功{su}次\n')

async def baiduNLP(text: str) -> dict:
    '''百度NLP语言情感识别'''
    async with aiohttp.request("post",
                               url='https://ai.baidu.com/aidemo', 
                               data={"apiType": "nlp", "type": "sentimentClassify", "t1": text}, 
                               headers={"Cookie": "BAIDUID=0"}
                               ) as r:
        ret = await r.json(content_type=None)
    return ret

async def juryVote(biliapi: asyncbili,
                   cid: int,
                   params: dict,
                   baiduNLPConfig: dict = None
                   ) -> bool:
    if baiduNLPConfig and baiduNLPConfig.get("confidence", 0) > 0:
        try:
            ret = await biliapi.juryCaseInfo(cid)
        except Exception as e:
            logging.warning(f'{biliapi.name}: 获取id为{cid}的案件信息异常，原因为{str(e)}，使用默认投票参数')
        else:
            if ret["code"] != 0:
                logging.warning(f'{biliapi.name}: 获取id为{cid}的案件信息失败，原因为{ret["message"]}，使用默认投票参数')
            else:
                try:
                    ret = await baiduNLP(ret["data"]["originContent"])
                except Exception as e:
                    logging.warning(f'{biliapi.name}: 百度NLP接口异常，原因为{str(e)}，使用默认投票参数')
                else:
                    if ret["errno"] != 0:
                        logging.warning(f'{biliapi.name}: 调用百度NLP接口失败，原因为{ret["msg"]}，使用默认投票参数')
                    elif ret["data"]["items"][0]["confidence"] > baiduNLPConfig["confidence"]:
                        params = params.copy()
                        if ret["data"]["items"][0]["negative_prob"] > baiduNLPConfig["negative_prob"]:
                            params["vote"] = params["vote"] if 'vote' in params and params["vote"] in (1, 4) else 4
                        elif ret["data"]["items"][0]["positive_prob"] > baiduNLPConfig["positive_prob"]:
                            params["vote"] = 2
                        else:
                            params["vote"] = 3

    try:
        ret = await biliapi.juryVote(cid, **params) #将参数params展开后传参
    except Exception as e:
        logging.warning(f'{biliapi.name}: 风纪委员投票id为{cid}的案件异常，原因为{str(e)}，跳过本次投票')
        return False
    if ret["code"] == 0:
        logging.info(f'{biliapi.name}: 风纪委员成功为id为{cid}的案件投({voteInfo[params["vote"]]})票')
        return True
    else:
        logging.warning(f'{biliapi.name}: 风纪委员投票id为{cid}的案件失败，信息为：{ret["message"]}')
        return False