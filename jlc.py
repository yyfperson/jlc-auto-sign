import os
import sys
import time
import json
import random
import requests
from datetime import datetime, timedelta
from serverchan_sdk import sc_send

# 全局变量用于收集总结日志
in_summary = False
summary_logs = []

def log(msg):
    """日志记录函数，保留原程序风格"""
    full_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(full_msg, flush=True)
    if in_summary:
        summary_logs.append(msg)

def format_nickname(nickname):
    """格式化昵称，只显示第一个字和最后一个字，中间用星号代替"""
    if not nickname or len(nickname.strip()) == 0:
        return "未知用户"
    
    nickname = nickname.strip()
    if len(nickname) == 1:
        return f"{nickname}*"
    elif len(nickname) == 2:
        return f"{nickname[0]}*"
    else:
        return f"{nickname[0]}{'*' * (len(nickname)-2)}{nickname[-1]}"

def mask_account(account):
    """用于打印时隐藏部分账号信息"""
    if not account: return "未知"
    if len(account) >= 4:
        return account[:2] + '****' + account[-2:]
    return '****'

def is_sunday():
    """检查今天是否是周日"""
    return datetime.now().weekday() == 6

def is_last_day_of_month():
    """检查今天是否是当月最后一天"""
    today = datetime.now()
    next_month = today.replace(day=28) + timedelta(days=4)
    last_day = next_month - timedelta(days=next_month.day)
    return today.day == last_day.day

# ================= 嘉立创金豆相关逻辑 =================

class JLCBeanClient:
    def __init__(self, access_token, account_index):
        self.access_token = access_token
        self.account_index = account_index
        self.headers = {
            'X-JLC-AccessToken': access_token,
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp',
        }
        self.base_url = "https://m.jlc.com"
        
        # 状态记录
        self.initial_jindou = 0
        self.final_jindou = 0
        self.jindou_reward = 0
        self.sign_status = "未知"
        self.has_reward = False
        self.success = False

    def get_assets_info(self):
        """获取资产信息（金豆数和CustomerCode）"""
        url = f"{self.base_url}/api/appPlatform/center/assets/selectPersonalAssetsInfo"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('data', {})
        except Exception as e:
            log(f"账号 {self.account_index} - ❌ 获取金豆信息异常: {e}")
        return None

    def sign_in(self):
        """执行金豆签到"""
        url = f"{self.base_url}/api/activity/sign/signIn?source=3"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                log(f"账号 {self.account_index} - ❌ 金豆签到请求失败: {response.status_code}")
        except Exception as e:
            log(f"账号 {self.account_index} - ❌ 金豆签到异常: {e}")
        return None

    def receive_voucher(self):
        """领取七日连签奖励"""
        url = f"{self.base_url}/api/activity/sign/receiveVoucher"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    log(f"账号 {self.account_index} - ✅ 成功领取金豆连签奖励")
                    return True
                else:
                    log(f"账号 {self.account_index} - ℹ️ 领取金豆连签奖励失败: {data.get('message')}")
        except Exception as e:
            log(f"账号 {self.account_index} - ❌ 领取金豆连签奖励异常: {e}")
        return False

    def execute(self):
        """执行完整流程"""
        if not self.access_token:
            log(f"账号 {self.account_index} - 🚫 未提供JLC Token，跳过金豆签到")
            self.sign_status = "未配置"
            return

        log(f"账号 {self.account_index} - 开始金豆签到流程...")
        
        # 1. 获取初始信息
        assets = self.get_assets_info()
        if not assets:
            self.sign_status = "获取信息失败"
            return
            
        self.initial_jindou = assets.get('integralVoucher', 0)
        customer_code = assets.get('customerCode', '')
        log(f"账号 {self.account_index} - 签到前金豆💰: {self.initial_jindou} (用户: {mask_account(customer_code)})")

        # 2. 执行签到
        time.sleep(random.uniform(0.5, 1.5))
        sign_result = self.sign_in()
        
        if sign_result and sign_result.get('success'):
            data = sign_result.get('data', {})
            gain_num = data.get('gainNum', 0)
            
            # 判断是否需要领奖 (API逻辑：gainNum为0但成功通常意味着有额外奖励待领取)
            if gain_num and gain_num > 0:
                log(f"账号 {self.account_index} - ✅ 金豆签到成功，获取{gain_num}个金豆")
                self.sign_status = "签到成功"
                self.success = True
            else:
                # 尝试领取连签奖励
                log(f"账号 {self.account_index} - 检测到可能满足连签奖励条件，尝试领取...")
                if self.receive_voucher():
                    self.has_reward = True
                    self.sign_status = "领取奖励成功"
                    self.success = True
                else:
                    self.sign_status = "需手动检查" # 可能只是今天签到没金豆，或者已经领过了
                    self.success = True # 只要API通了，通常视为流程走通
        else:
            msg = sign_result.get('message', '未知') if sign_result else '请求失败'
            if '已经签到' in msg:
                log(f"账号 {self.account_index} - ✅ 今日已签到")
                self.sign_status = "已签到过"
                self.success = True
            else:
                log(f"账号 {self.account_index} - ❌ 金豆签到失败: {msg}")
                self.sign_status = f"失败:{msg}"
                return

        # 3. 获取最终信息
        time.sleep(random.uniform(0.5, 1.5))
        assets_final = self.get_assets_info()
        if assets_final:
            self.final_jindou = assets_final.get('integralVoucher', 0)
            self.jindou_reward = self.final_jindou - self.initial_jindou
            
            if self.jindou_reward > 0:
                extra_text = "（有奖励）" if self.has_reward else ""
                log(f"账号 {self.account_index} - 🎉 总金豆增加: {self.initial_jindou} → {self.final_jindou} (+{self.jindou_reward}){extra_text}")
            elif self.jindou_reward == 0:
                 log(f"账号 {self.account_index} - ⚠ 总金豆无变化: {self.initial_jindou} → {self.final_jindou}")
            else:
                 log(f"账号 {self.account_index} - ❗ 金豆减少: {self.initial_jindou} → {self.final_jindou} ({self.jindou_reward})")
        
        log(f"账号 {self.account_index} - ✅ 金豆签到流程完成")


# ================= 开源平台 (OSHWHUB) 相关逻辑 =================

class OSHWHubClient:
    def __init__(self, cookie, account_index):
        self.cookie = cookie
        self.account_index = account_index
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Cookie': cookie,
            'Referer': 'https://oshwhub.com/sign_in'
        }
        self.base_url = "https://oshwhub.com"
        
        # 状态记录
        self.nickname = "未知"
        self.initial_points = 0
        self.final_points = 0
        self.points_reward = 0
        self.reward_results = []
        self.sign_status = "未知"
        self.success = False

    def get_user_info(self):
        """获取用户信息（积分、昵称）"""
        url = f"{self.base_url}/api/users"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('result', {})
                    self.nickname = result.get('nickname', '未知')
                    return result.get('points', 0)
                elif data.get('code') == 401:
                     log(f"账号 {self.account_index} - ❌ 开源平台Cookie失效或未登录")
                     return None
        except Exception as e:
            log(f"账号 {self.account_index} - ❌ 获取开源平台用户信息异常: {e}")
        return None

    def sign_in(self):
        """执行开源平台签到"""
        url = f"{self.base_url}/api/users/signIn"
        try:
            # 需要带上时间戳参数
            data = {"_t": int(time.time() * 1000)}
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                log(f"账号 {self.account_index} - ❌ 开源平台签到请求失败: {response.status_code}")
        except Exception as e:
            log(f"账号 {self.account_index} - ❌ 开源平台签到异常: {e}")
        return None

    def check_and_claim_gift(self, gift_type):
        """检查并领取礼包 (7天好礼/月度好礼)"""
        # 1. 获取礼品配置信息
        config_url = f"{self.base_url}/api/gift/goodGift"
        try:
            resp = requests.get(config_url, headers=self.headers, timeout=10)
            if resp.status_code != 200: return
            
            data = resp.json()
            if not data.get('success'): return

            result = data.get('result', {})
            target_gift = None
            
            if gift_type == "7天":
                target_gift = result.get('sevenDays') # {uuid: "...", name: "...", received: false}
            elif gift_type == "月度":
                target_gift = result.get('monthEnd')
            
            if not target_gift:
                log(f"账号 {self.account_index} - 未查询到{gift_type}好礼配置")
                return

            uuid = target_gift.get('uuid')
            
            # 2. 尝试领取
            # 接口文档显示领取接口为 /api/gift/goodGift/{uuid}
            # 尝试使用 POST
            claim_url = f"{self.base_url}/api/gift/goodGift/{uuid}"
            claim_resp = requests.post(claim_url, headers=self.headers, timeout=10)
            
            if claim_resp.status_code == 200:
                claim_data = claim_resp.json()
                if claim_data.get('success'):
                    # 1=优惠券, 2=积分
                    res_code = claim_data.get('result') 
                    msg = "优惠券" if res_code == 1 else "积分(约20)" if res_code == 2 else "未知奖励"
                    log_msg = f"开源平台{gift_type}礼包领取结果: 恭喜获取 {msg}"
                    log(f"账号 {self.account_index} - ✅ {log_msg}")
                    self.reward_results.append(log_msg)
                else:
                    err = claim_data.get('msg') or claim_data.get('message')
                    if "已领取" in str(err):
                        log(f"账号 {self.account_index} - ℹ️ {gift_type}好礼已领取过")
                    else:
                        log(f"账号 {self.account_index} - ⚠️ {gift_type}好礼领取失败: {err}")
            
        except Exception as e:
            log(f"账号 {self.account_index} - ❌ 领取{gift_type}好礼异常: {e}")

    def execute(self):
        """执行完整流程"""
        if not self.cookie:
            log(f"账号 {self.account_index} - 🚫 未提供开源平台Cookie，跳过开源平台签到")
            self.sign_status = "未配置"
            return

        # 1. 获取初始积分和昵称
        points = self.get_user_info()
        if points is None:
            self.sign_status = "Cookie无效"
            return
        
        self.initial_points = points
        formatted_nick = format_nickname(self.nickname)
        log(f"账号 {self.account_index} - 👤 昵称: {formatted_nick}")
        log(f"账号 {self.account_index} - 签到前积分💰: {self.initial_points}")

        # 2. 执行签到
        time.sleep(random.uniform(0.5, 1.5))
        sign_res = self.sign_in()
        
        if sign_res and sign_res.get('success'):
            log(f"账号 {self.account_index} - ✅ 开源平台签到成功！")
            self.sign_status = "签到成功"
            self.success = True
        else:
            msg = sign_res.get('message', '未知') if sign_res else '请求失败'
            # 检查是否是已签到
            if "已签到" in msg or "Duplicate entry" in str(sign_res):
                log(f"账号 {self.account_index} - ✅ 今天已经在开源平台签到过了！")
                self.sign_status = "已签到过"
                self.success = True
            else:
                log(f"账号 {self.account_index} - ❌ 开源平台签到失败: {msg}")
                self.sign_status = f"失败:{msg}"
                # 如果签到失败（非已签到），通常不继续后续领奖，但为了保险起见，如果是API错误，仍可尝试检查
        
        # 3. 检查并领取礼包 (即使已签到也要检查，防止之前漏领)
        if self.success:
            if is_sunday():
                log(f"账号 {self.account_index} - ✅ 检测到今天是周日，尝试领取7天好礼...")
                self.check_and_claim_gift("7天")
            
            if is_last_day_of_month():
                log(f"账号 {self.account_index} - ✅ 检测到今天是月底，尝试领取月度好礼...")
                self.check_and_claim_gift("月度")

        # 4. 获取最终积分
        time.sleep(random.uniform(0.5, 1.5))
        final_p = self.get_user_info()
        if final_p is not None:
            self.final_points = final_p
            self.points_reward = self.final_points - self.initial_points
            
            if self.points_reward > 0:
                log(f"账号 {self.account_index} - 🎉 总积分增加: {self.initial_points} → {self.final_points} (+{self.points_reward})")
            elif self.points_reward == 0:
                log(f"账号 {self.account_index} - ⚠ 总积分无变化: {self.initial_points} → {self.final_points}")
            else:
                log(f"账号 {self.account_index} - ❗ 积分减少: {self.initial_points} → {self.final_points} ({self.points_reward})")

# ================= 推送通知逻辑 (保留原程序) =================

def push_summary():
    if not summary_logs:
        return
    
    title = "嘉立创签到总结"
    text = "\n".join(summary_logs)
    full_text = f"{title}\n{text}"
    
    # Telegram
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if telegram_bot_token and telegram_chat_id:
        try:
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            params = {'chat_id': telegram_chat_id, 'text': full_text}
            requests.get(url, params=params)
            log("Telegram-日志已推送")
        except: pass

    # 企业微信 (WeChat Work)
    wechat_webhook_key = os.getenv('WECHAT_WEBHOOK_KEY')
    if wechat_webhook_key:
        try:
            url = wechat_webhook_key if wechat_webhook_key.startswith('https://') else f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={wechat_webhook_key}"
            body = {"msgtype": "text", "text": {"content": full_text}}
            requests.post(url, json=body)
            log("企业微信-日志已推送")
        except: pass

    # 钉钉 (DingTalk)
    dingtalk_webhook = os.getenv('DINGTALK_WEBHOOK')
    if dingtalk_webhook:
        try:
            url = dingtalk_webhook if dingtalk_webhook.startswith('https://') else f"https://oapi.dingtalk.com/robot/send?access_token={dingtalk_webhook}"
            body = {"msgtype": "text", "text": {"content": full_text}}
            requests.post(url, json=body)
            log("钉钉-日志已推送")
        except: pass

    # PushPlus
    pushplus_token = os.getenv('PUSHPLUS_TOKEN')
    if pushplus_token:
        try:
            url = "http://www.pushplus.plus/send"
            body = {"token": pushplus_token, "title": title, "content": text}
            requests.post(url, json=body)
            log("PushPlus-日志已推送")
        except: pass

    # Server酱
    serverchan_sckey = os.getenv('SERVERCHAN_SCKEY')
    if serverchan_sckey:
        try:
            url = f"https://sctapi.ftqq.com/{serverchan_sckey}.send"
            body = {"title": title, "desp": text}
            requests.post(url, data=body)
            log("Server酱-日志已推送")
        except: pass

    # Server酱3
    serverchan3_sckey = os.getenv('SERVERCHAN3_SCKEY') 
    if serverchan3_sckey:
        try:
            options = {"tags": "嘉立创|签到"}
            sc_send(serverchan3_sckey, title, text, options)            
            log("Server酱3-日志已推送")
        except: pass    

    # 酷推
    coolpush_skey = os.getenv('COOLPUSH_SKEY')
    if coolpush_skey:
        try:
            url = f"https://push.xuthus.cc/send/{coolpush_skey}?c={full_text}"
            requests.get(url)
            log("酷推-日志已推送")
        except: pass

    # 自定义API
    custom_webhook = os.getenv('CUSTOM_WEBHOOK')
    if custom_webhook:
        try:
            body = {"title": title, "content": text}
            requests.post(custom_webhook, json=body)
            log("自定义API-日志已推送")
        except: pass

# ================= 主程序 =================

def main():
    global in_summary
    
    if len(sys.argv) < 3:
        print("用法: python jlc.py \"Token1&Token2...\" \"Cookie1&Cookie2...\" [失败退出标志]")
        print("注意: 使用 & 分割多个账号的Token和Cookie，两者数量必须一致。")
        sys.exit(1)
    
    # 1. 参数解析
    raw_tokens = sys.argv[1].split('&')
    raw_cookies = sys.argv[2].split('&')
    
    # 解析失败退出标志，默认为关闭
    enable_failure_exit = False
    if len(sys.argv) >= 4:
        enable_failure_exit = (sys.argv[3].lower() == 'true')
    
    log(f"失败退出功能: {'开启' if enable_failure_exit else '关闭'}")
    
    # 清理空白字符，但保留空位以维持索引对齐（如果出现连续&&）
    tokens = [t.strip() for t in raw_tokens]
    cookies = [c.strip() for c in raw_cookies]
    
    if len(tokens) != len(cookies):
        log(f"❌ 错误: Token数量({len(tokens)}) 和 Cookie数量({len(cookies)}) 不匹配!")
        sys.exit(1)
    
    total_accounts = len(tokens)
    log(f"开始处理 {total_accounts} 个账号的签到任务")
    
    # 存储结果
    results = []

    # 2. 循环处理账号
    for i in range(total_accounts):
        account_index = i + 1
        log(f"开始处理第 {account_index} 个账号")
        
        token = tokens[i]
        cookie = cookies[i]
        
        # 初始化结果对象
        res = {
            'index': account_index,
            'oshw_client': None,
            'jlc_client': None
        }
        
        # --- 开源平台流程 ---
        if cookie:
            oshw = OSHWHubClient(cookie, account_index)
            oshw.execute()
            res['oshw_client'] = oshw
        else:
            log(f"账号 {account_index} - ⚠️ Cookie为空，跳过开源平台签到")

        # --- 金豆流程 ---
        if token:
            jlc = JLCBeanClient(token, account_index)
            jlc.execute()
            res['jlc_client'] = jlc
        else:
            log(f"账号 {account_index} - ⚠️ Token为空，跳过金豆签到")
            
        results.append(res)
        
        if i < total_accounts - 1:
            wait_time = random.randint(2, 5)
            log(f"等待 {wait_time} 秒后处理下一个账号...")
            time.sleep(wait_time)

    # 3. 生成总结日志
    log("=" * 70)
    in_summary = True
    log("📊 详细签到任务完成总结")
    log("=" * 70)
    
    oshwhub_success_count = 0
    jindou_success_count = 0
    total_points_reward = 0
    total_jindou_reward = 0
    failed_accounts = []

    for res in results:
        idx = res['index']
        oshw = res['oshw_client']
        jlc = res['jlc_client']
        
        nickname = oshw.nickname if oshw else "未知"
        
        log(f"账号 {idx} ({format_nickname(nickname)}) 详细结果:")
        
        # 开源平台结果
        if oshw:
            log(f"  ├── 开源平台: {oshw.sign_status}")
            
            p_sign = "+" if oshw.points_reward > 0 else ""
            log(f"  ├── 积分变化: {oshw.initial_points} → {oshw.final_points} ({p_sign}{oshw.points_reward})")
            
            for gift_log in oshw.reward_results:
                log(f"  ├── {gift_log}")
                
            if oshw.points_reward > 0: total_points_reward += oshw.points_reward
            if oshw.success: oshwhub_success_count += 1
            else: 
                # 如果配置了cookie但失败了
                log(f"  ├── ⚠️ 开源平台签到未成功")
        else:
            log(f"  ├── 开源平台: 未配置(跳过)")

        # 金豆结果
        if jlc:
            log(f"  ├── 金豆签到: {jlc.sign_status}")
            
            j_sign = "+" if jlc.jindou_reward > 0 else ""
            reward_flag = "（有奖励）" if jlc.has_reward else ""
            log(f"  ├── 金豆变化: {jlc.initial_jindou} → {jlc.final_jindou} ({j_sign}{jlc.jindou_reward}){reward_flag}")
            
            if jlc.jindou_reward > 0: total_jindou_reward += jlc.jindou_reward
            if jlc.success: jindou_success_count += 1
            else:
                log(f"  ├── ⚠️ 金豆签到未成功")
        else:
            log(f"  ├── 金豆签到: 未配置(跳过)")
            
        log("  " + "-" * 50)
        
        # 判定是否为失败账号 (只有当配置了凭证但success为False时才算失败)
        is_fail = False
        if oshw and not oshw.success: is_fail = True
        if jlc and not jlc.success: is_fail = True
        if is_fail:
            failed_accounts.append(idx)

    # 总体统计
    log("📈 总体统计:")
    log(f"  ├── 总账号数: {total_accounts}")
    log(f"  ├── 开源平台签到成功: {oshwhub_success_count}")
    log(f"  ├── 金豆签到成功: {jindou_success_count}")
    if total_points_reward > 0:
        log(f"  ├── 总计获得积分: +{total_points_reward}")
    if total_jindou_reward > 0:
        log(f"  ├── 总计获得金豆: +{total_jindou_reward}")
        
    if failed_accounts:
        log(f"  ⚠ 存在异常的账号索引: {', '.join(map(str, failed_accounts))}")
    else:
        log("  🎉 所有配置的账号均执行成功!")
        
    log("=" * 70)
    
    # 推送
    push_summary()
    
    # 退出码逻辑
    if enable_failure_exit and failed_accounts:
        log("❌ 由于失败退出功能已开启且存在失败账号，返回退出码 1")
        sys.exit(1)
    else:
        log("✅ 程序正常退出")
        sys.exit(0)

if __name__ == "__main__":
    main()
