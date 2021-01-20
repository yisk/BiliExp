BiliExp-Actions
====  
##### 本分支为主分支的云函数功能的一部分，去除了对云函数的依赖，只需要github Actions就能使用，最新功能在本分支更新，因此会频繁变动，如无必要可以不及时更新代码(除非出现严重bug)

[![](https://img.shields.io/badge/author-%E6%98%9F%E8%BE%B0-red "作者")](https://github.com/happy888888/ )
![](https://img.shields.io/badge/dynamic/json?label=GitHub%20Followers&query=%24.data.totalSubs&url=https%3A%2F%2Fapi.spencerwoo.com%2Fsubstats%2F%3Fsource%3Dgithub%26queryKey%3Dhappy888888&labelColor=282c34&color=181717&logo=github&longCache=true "关注数量")
![](https://img.shields.io/github/stars/happy888888/BiliExp.svg?style=plastic&logo=appveyor "Star数量")
![](https://img.shields.io/github/forks/happy888888/BiliExp.svg?style=plastic&logo=stackshare "Fork数量")

</br>[点击快速使用](#使用方式先按照主分支说明切换分支否则找不到对应的Actions)

### 主要功能
**B站自动操作脚本**
* [x] 每日获取经验(投币(支持自定义up主)、点赞、分享视频) 
* [x] 自动转发互动抽奖并评论点赞(自己关注的up主,支持指定关键字如"#互动抽奖#",支持跟踪转发模式)
* [x] 获取主站@和私聊消息提醒(便于多账号抽奖时获取中奖信息)
* [x] 参与官方转盘抽奖活动(目前没有自动搜集活动的功能,需要在配置文件config/activities.json里面手动指定,本项目***discussions***下会更新比较新的转盘抽奖活动)
* [x] 每日直播签到
* [x] 直播挂机(获取小心心,点亮粉丝牌，默认每次每个粉丝牌房间分别挂机45分钟)
* [x] 直播自动送出快过期礼物 
* [x] 直播天选时刻抽奖 (支持条件过滤，默认执行45分钟后退出)
* [x] 直播应援团每日签到 
* [ ] ~~直播开启宝箱领取银瓜子(本活动已结束，不知道B站以后会不会再启动)~~ 
* [x] 每日兑换银瓜子为硬币 
* [x] 自动领取大会员每月权益(每月1号领取B币劵，优惠券)
* [x] 自动花费大会员剩余B币劵(每月28号执行，支持给自己充电或者兑换成金瓜子)
* [x] 漫画APP每日签到
* [x] 自动花费即将过期漫读劵(默认不开启)
* [x] 自动积分兑换漫画福利券(需中午12点启动，默认不开启)
* [x] 自动领取大会员漫画每月福利劵
* [ ] ~~自动参加每月"站友日"活动(本活动已结束，不知道B站以后会不会再启动)~~
* [x] 定时清理无效动态(转发的过期抽奖，失效动态，支持自定义关键字，非官方渠道抽奖无法判断是否过期) 
* [x] 风纪委员投票(默认45分钟内没有案件自动退出)
</br>

```
如有其他功能需求请发issue，提供功能说明和功能所在的B站页面(app功能可提供界面截图和进入方式)以帮助本项目扩展功能
```

### 使用方式(先按照主分支说明切换分支否则找不到对应的Actions)
* 1.准备
    *  1.1 一个或多个B站账号，以及登录后获取的SESSDATA，bili_jct，DedeUserID (获取方式见下方示意图)
	   `浏览器打开B站主页--》按F12打开开发者工具--》application--》cookies`
	   
       <div align="center"><img src="https://s1.ax1x.com/2020/09/23/wjM09e.png" width="800" height="450" title="获取cookies示例"></div>
    *  1.2 fork本项目
* 2.部署
    *  2.1 在fork后的github仓库的 “Settings” --》“Secrets” 中添加"Secrets"，name(不用在意大小写)和value分别为：
        *  2.1.1 name为"biliconfig"           value为B站账号登录信息(可多个)，格式如下
        ```
        SESSDATA(账号1)
        bili_jct(账号1)
        uid(账号1)
		uid(账号2)
		bili_jct(账号2)
		SESSDATA(账号2)
		(多个账户继续加在后面，不用考虑每个账号三个参数的先后顺序)
        ```
        例如下面这样(例子为两个账号)
        ```
        e1272654%vfdawi241825%2C8dc06*a1
        0a9081cc53856314783d195f5ddbadf3
        203953353
		
		2035453
		dfs425cc53856351d4d5195f5ddbakb2
        e1412354%afdoii534825%2Cbbc06*a1
        ```
		注：每行一个cookie项(SESSDATA bili_jct uid或者空行)，***不规定顺序***但必须一个账户三个参数填完才能填下一个账户的参数
		![image](https://user-images.githubusercontent.com/67217225/98549976-73700900-22d6-11eb-9356-22802456da50.png)
        *  2.1.2 (可选)name为"push_message"           value为推送SCKEY或email或telegramBot_token用于消息推送，格式如下
        ```
        SCU10xxxxxxxxxxxxxxxd547519b62d027xxxxxxxxx20f3578cbe6
		example@qq.com
		1443793198:AAEI9TGazdrj4Jh6X6B7CvuAKX4IivEb450,1459469720
        ```
		注：每行一个推送参数(SCKEY email telegramBot_token或者空行)，***可以同时提供多个或不提供SCKEY或email或telegramBot_token，填写后会同时推送***,<br>
		***使用telegramBot的注意，除了填写token,还要填写chat_id,在同一行用逗号隔开***,比如例子提供的意思是telegram token为`1443793198:AAEI9TGazdrj4Jh6X6B7CvuAKX4IivEb450`,chat_id为`1459469720`
        *  2.1.3 (可选)name为"advconfig"           value为/config/config.json文件的所有内容(直接复制粘贴整个文件)
		***此项为详细配置文件，可配置所有细节参数，可直接替代前两个secrets也可以与前两个secrets共同使用，注意此项不存在时直接使用默认配置***<br>
		如果使用***天选时刻***，***风纪委员投票***和 ***直播心跳(获取小心心)*** 功能可参考 [部分功能推荐配置](https://github.com/happy888888/BiliExp/issues/178)
    *  2.2 添加完上面的"Secrets"后，进入"Actions" --》"run BiliExp"，点击右边的"Run workflow"即可第一次启动
        *  2.2.1 首次fork可能要去actions(正上方的actions不是Settings里面的actions)里面同意使用actions条款，如果"Actions"里面没有"run BiliExp"，点一下右上角的"star"，"run BiliExp"就会出现在"Actions"里面(先按照主分支说明切换分支否则找不到对应的Actions)
		![image](https://user-images.githubusercontent.com/67217225/98933791-16659480-251c-11eb-9713-c3dbcc6321bf.png)
		![image](https://user-images.githubusercontent.com/67217225/98934269-c935f280-251c-11eb-8bce-b8fa04c68cb8.png)
        *  2.2.2 第一次启动后，脚本会每天12:00自动执行，不需要再次手动执行(第一次手动执行这个步骤不能忽略)。

* 3.更新代码
    
    *  进入文件夹.github/workflows，删除auto_merge.yml文件中第5,6行前面的`#`即可定时启动代码更新

</br>

## 打赏
如果觉得本项目好用，对你有所帮助，欢迎打赏支持一下本项目发展！！！

<div align="center">

<img src="https://user-images.githubusercontent.com/67217225/99527309-8d48d480-29d7-11eb-8f4e-7034dbd91baf.png" width="600" title="支付宝，微信，QQ扫码赞助" style="display:block;" />

</div>
</br>

## 更新日志

### 2021/01/19更新

* 1.优化天选时刻，直播心跳，风纪投票三个模块
* 2.更新转盘抽奖

### 2021/01/02更新

* 1.修复充电接口失效问题
* 2.天选时刻支持过滤付费抽奖
* 3.更新转盘抽奖
* 4.永久移除站友日活动

</br>

### 2020/12/01更新

* 1.直播送出礼物支持自定义直播间
* 2.直播间心跳支持多个直播间
* 3.修复抽奖跟踪转发模式bug

</br>

### 2020/11/15更新

* 1.动态转发抽奖使用正则表达式匹配up主自发抽奖
* 2.动态转发抽奖支持跟踪转发(抽奖抽得多的人转发啥我转发啥)
* 3.添加直播参加天选时刻功能

</br>

### 2020/11/11更新

* 1.视频投币支持自定义up主
* 2.风纪委员投票支持百度NLP情感分析

</br>

### 2020/11/10更新

* 1.增加直播挂机获取小心心
* 2.增加自动同步代码的Actions

</br>

### 2020/11/05更新

* 1.增加花费漫读劵的方式(兑换为金瓜子)
* 2.风纪委员投票改为给当前所有案件投票

</br>

### 2020/10/19更新

* 1.修复部分动态转发问题
* 2.调整模块名

</br>

### 2020/10/16更新

* 1.增加风纪委员投票的功能

</br>

### 2020/10/13更新

* 1.调整代码结构，程序改为单入口
* 2.用aiohttp重写B站接口类，整个脚本改用协程并发执行提高效率(activity单ip地址五秒内只能请求一次只能加锁限制并发)
* 3.将功能模块化，通过配置文件控制模块的加载和开关

</br>

### 2020/10/01更新

* 1.主分支的更新内容
* 2.官方转盘抽奖活动的活动列表改为手动指定，存放在config/activity.json(自动搜索活动的效率太低)

</br>

### 2020/09/27更新

* 1.互动抽奖方式改为转发并评论(听说能提高中奖率🤑🤩)。

</br>

### 2020/09/26更新

* 1.增加email推送。

</br>

### 2020/09/24更新

* 1.移除参加B站活动抽奖的脚本的活动列表文件，改为自动获取。(现在这个活动抽奖很鸡肋)
