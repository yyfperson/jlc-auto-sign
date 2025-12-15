# 推送配置说明

推送仅看作不同的日志输出端，与日志输出内容没有本质区别。

配置多个，多个端均会收到日志消息。推荐钉钉、server酱、企业微信。

配置方式主要通过GitHub Secrets添加环境变量（推荐），如`TELEGRAM_BOT_TOKEN`等。

推送内容仅为签到总结日志（"📊 详细签到任务完成总结"以下部分）。

## Telegram

点击 https://core.telegram.org/api#bot-api 查看如何创建机器人并获取到机器人的botToken。

### botToken

| TITLE | CONTENT             |
| ----- | ------------------- |
| 配置Key | `TELEGRAM_BOT_TOKEN` |
| 值域    | 一串字符串             |
| 默认值   | 空                   |

### chatId

点击 https://api.telegram.org/bot{TOKEN}/getUpdates 获取到与机器人的chatId（需要用上面获取到的Token替换进链接里的{TOKEN}后访问）

P.S.访问链接需要能访问"外网"，有vpn的挂vpn。

| TITLE | CONTENT           |
| ----- | ----------------- |
| 配置Key | `TELEGRAM_CHAT_ID` |
| 值域    | 一串字符串           |
| 默认值   | 空                 |

## 企业微信机器人

在群内添加机器人，获取到机器人的Webhook Key，添加到配置中。支持完整URL或仅Key（程序会自动构建URL）。

### webhookKey

| TITLE | CONTENT                 |
| ----- | ----------------------- |
| 配置Key | `WECHAT_WEBHOOK_KEY`     |
| 值域    | 一串字符串（Key或完整URL）   |
| 默认值   | 空                       |

## 钉钉群机器人

在群内添加机器人，获取到机器人的Webhook地址，添加到配置中。支持完整URL或仅access_token（程序会自动构建URL）。

机器人的安全策略，当前不支持加签，请使用关键字策略，推荐关键字：`签到` 或 `总结`。

<img src="/img/dingtalk.jpg" alt="push-ding" width="400" />

### webhook

| TITLE | CONTENT             |
| ----- | ------------------- |
| 配置Key | `DINGTALK_WEBHOOK`   |
| 值域    | 一串字符串（URL或token） |
| 默认值   | 空                   |

## PushPlus

官网： http://www.pushplus.plus/doc/

### token

获取方式请参考官网。

| TITLE | CONTENT          |
| ----- | ---------------- |
| 配置Key | `PUSHPLUS_TOKEN`  |
| 值域    | 一串字符串          |
| 默认值   | 空                |

## Server酱

官网： https://sct.ftqq.com/

### scKey

获取方式请参考官网。

| TITLE | CONTENT               |
| ----- | --------------------- |
| 配置Key | `SERVERCHAN_SCKEY`     |
| 值域    | 一串字符串               |
| 默认值   | 空                     |

## 酷推

https://cp.xuthus.cc/

### sKey

该平台可能还在完善当中，对接时发现其接口定义不规范，且机器人容易被封，所以不推荐使用，且不接受提酷推推送相关bug。

| TITLE | CONTENT          |
| ----- | ---------------- |
| 配置Key | `COOLPUSH_SKEY`   |
| 值域    | 一串字符串          |
| 默认值   | 空                |

## 自定义API

这是简单封装的一个通用推送接口，可以推送到任意的API地址，如果有自己的机器人或自己的用于接受日志的API，可以根据需要自定义配置。程序会发送POST JSON `{"title": "嘉立创签到总结", "content": "..."}`。

### webhook

| TITLE | CONTENT             |
| ----- | ------------------- |
| 配置Key | `CUSTOM_WEBHOOK`     |
| 值域    | 一串字符串（完整URL）    |
| 默认值   | 空                   |
