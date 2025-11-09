from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import json
import os
import datetime
import requests
import asyncio
from pathlib import Path
import time

# JSON处理模块
class JsonHandler:
    @staticmethod
    def 验证文件名(文件名: str) -> bool:
        """验证文件名是否合法"""
        if not 文件名:
            print("错误: 文件名不能为空")
            return False
        
        # 检查文件名是否包含路径分隔符（防止路径遍历攻击）
        if any(c in 文件名 for c in ['/', '\\', './', '../', '.\\', '..\\']):
            print(f"错误: 文件名 '{文件名}' 包含非法字符或路径组件")
            return False
        
        # 检查文件名是否包含非法字符
        invalid_chars = '<>|?*"'
        if any(c in 文件名 for c in invalid_chars):
            print(f"错误: 文件名 '{文件名}' 包含非法字符")
            return False
        
        return True
    
    @staticmethod
    def 获取文件路径(文件名: str, 确保目录存在: bool = False) -> str:
        """获取JSON文件的完整路径"""
        # 验证文件名是否合法
        if not JsonHandler.验证文件名(文件名):
            raise ValueError(f"无效的文件名: {文件名}")
        
        # 获取项目根目录
        项目根目录 = Path(__file__).parent
        
        # 构建UserData文件夹的绝对路径
        用户数据目录 = 项目根目录 / "UserData"
        
        # 构建文件的完整路径
        文件路径 = 用户数据目录 / 文件名
        
        # 安全检查：确保最终路径仍然在UserData目录内
        规范后的文件路径 = 文件路径.resolve()
        规范后的用户数据目录 = 用户数据目录.resolve()
        
        if not str(规范后的文件路径).startswith(str(规范后的用户数据目录)):
            raise SecurityError(f"安全错误: 尝试访问UserData目录外的文件: {文件名}")
        
        # 如果需要确保目录存在
        if 确保目录存在:
            os.makedirs(规范后的用户数据目录, exist_ok=True)
        
        return str(规范后的文件路径)
    
    @staticmethod
    def 读取Json字典(文件名: str) -> dict:
        """读取JSON文件为字符串字典"""
        try:
            文件路径 = JsonHandler.获取文件路径(文件名)
            
            if not os.path.exists(文件路径):
                print(f"警告: 文件不存在: {文件路径}")
                return {}
            
            with open(文件路径, 'r', encoding='utf-8') as f:
                json内容 = f.read()
                字典 = json.loads(json内容) if json内容 else {}
                
                if not isinstance(字典, dict):
                    print(f"警告: JSON文件内容格式不正确: {文件路径}")
                    return {}
                
                return 字典
        except Exception as ex:
            print(f"错误: 读取JSON字典时发生错误 - {ex}")
            return {}
    
    @staticmethod
    def 获取值(字典: dict, 键: str, 默认值: str = None) -> str:
        """根据键获取值，如果键不存在返回默认值"""
        if 字典 is not None and 键 in 字典:
            return 字典[键]
        return 默认值
    
    @staticmethod
    def 添加或更新(文件名: str, 键: str, 值: str) -> bool:
        """向字典添加或更新键值对"""
        try:
            if not 键:
                print("错误: 键名不能为空")
                return False
            
            字典 = JsonHandler.读取Json字典(文件名)
            字典[键] = 值
            文件路径 = JsonHandler.获取文件路径(文件名, True)
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump(字典, f, ensure_ascii=False, indent=2)
            return True
        except Exception as ex:
            print(f"错误: 添加或更新JSON值时发生错误 - {ex}")
            return False

# 创建别名方便使用
Json = JsonHandler

# 邮件服务模块
class EmailService:
    """邮件发送服务类（基于C#代码实现）"""
    
    def __init__(self, auth_token, project_id="p_95jd", max_retries=2):
        """
        初始化邮件服务
        
        Args:
            auth_token (str): 认证令牌
            project_id (str): 项目ID，默认值为"p_95jd"
            max_retries (int): 重试次数，默认值为2
        """
        self.auth_token = auth_token
        self.project_id = project_id
        self.add_email_url = "https://adminapi-pd.spark.xd.com/api/v1/table/add"
        self.send_email_url = "https://adminapi-pd.spark.xd.com/api/v1/table/row"
        self.table_id = "firm0_app_email_manager"
        self.session = requests.Session()
        self.max_retries = max_retries  # 设置重试次数
        # 设置默认请求头
        self._update_auth_headers(auth_token)
    
    def _update_auth_headers(self, token):
        """更新认证头信息"""
        self.auth_token = token
        self.session.headers.update({
            "Cookie": f"token={token}",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"  # 增加Authorization头
        })
        # 同时更新session的cookies
        self.session.cookies.set('token', token)
    
    def _trigger_email_send(self, row_id):
        """
        触发邮件发送（根据C#代码）
        
        Args:
            row_id: 邮件行ID
            
        Returns:
            dict: 发送结果
        """
        if not row_id:
            return {"success": False, "message": "行ID为空"}
        
        try:
            request_data = {
                "firm": self.project_id,
                "functor": "send",
                "payload": {},
                "row_id": row_id,
                "table_id": self.table_id
            }
            
            print(f"准备触发邮件发送: {row_id}")
            print(f"触发请求数据: {json.dumps(request_data, ensure_ascii=False)}")
            
            response = self.session.post(self.send_email_url, data=json.dumps(request_data))
            print(f"触发发送响应状态码: {response.status_code}")
            print(f"触发发送响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    return {
                        "success": result.get("result") == 0,
                        "message": result.get("msg", "未知响应")
                    }
                except json.JSONDecodeError:
                    print(f"触发发送响应解析失败: {response.text}")
                    return {"success": False, "message": "触发发送响应不是有效的JSON"}
            else:
                return {"success": False, "message": f"触发发送失败: {response.status_code} {response.reason}"}
                
        except Exception as e:
            print(f"触发邮件发送异常: {str(e)}")
            return {"success": False, "message": f"触发邮件发送异常: {str(e)}"}
    
    def send_email(self, email_data):
        """
        发送邮件（根据C#代码实现）
        
        Args:
            email_data (dict): 邮件数据，包含标题、正文、收件人ID等
            
        Returns:
            dict: 发送结果
        """
        try:
            print(f"准备发送邮件: {email_data.get('标题', '无标题')}")
            print(f"目标类型: {email_data.get('目标类型', 1)}，收件人ID: {email_data.get('收件人ID', '全体')}")
            
            # 先验证token是否存在
            if not self.auth_token:
                error_msg = "认证token为空，请先设置有效的token"
                print(error_msg)
                return {"success": False, "message": error_msg, "error_code": "TOKEN_EMPTY"}
            
            # 第一步：添加邮件到系统
            add_result = self._add_email(email_data)
            print(f"添加邮件结果: {add_result}")
            
            # 检查是否是401错误
            if add_result and "401 Unauthorized" in add_result.get("message", ""):
                print("检测到401未授权错误，可能需要刷新token")
                return {
                    "success": False, 
                    "message": add_result.get("message"),
                    "error_code": "TOKEN_EXPIRED",
                    "need_refresh": True
                }
            
            if not add_result:
                return {"success": False, "message": "添加邮件失败: 未收到响应", "error_code": "NO_RESPONSE"}
            if not add_result.get('success'):
                error_message = add_result.get('message', '添加邮件失败')
                return {"success": False, "message": error_message, "error_code": "EMAIL_ADD_FAILED"}
            
            # 第二步：触发发送
            row_id = add_result.get('row_id')
            if row_id:
                # 调用触发发送方法
                trigger_result = self._trigger_email_send(row_id)
                print(f"触发发送结果: {trigger_result}")
                
                if trigger_result.get("success"):
                    return {
                        "success": True,
                        "message": "邮件发送成功",
                        "row_id": row_id,
                        "trigger_result": trigger_result
                    }
                else:
                    # 触发发送失败，但邮件已添加
                    return {
                        "success": False,
                        "message": f"邮件添加成功但触发发送失败: {trigger_result.get('message')}",
                        "row_id": row_id,
                        "email_added": True
                    }
            else:
                return {"success": False, "message": "未获取到邮件行ID", "error_code": "NO_ROW_ID"}
            
        except requests.RequestException as e:
            error_msg = f"网络请求异常: {str(e)}"
            print(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                # 检查是否是401错误
                if e.response.status_code == 401:
                    return {
                        "success": False,
                        "message": f"401未授权错误: {str(e)}",
                        "error_code": "TOKEN_EXPIRED",
                        "need_refresh": True
                    }
            return {"success": False, "message": error_msg, "error_code": "NETWORK_ERROR"}
        except Exception as e:
            error_msg = f"发送邮件异常: {str(e)}"
            print(error_msg)
            import traceback
            print(f"异常堆栈: {traceback.format_exc()}")
            return {"success": False, "message": error_msg, "error_code": "INTERNAL_ERROR"}
    
    def quick_send(self, title, content, recipient_id, item_id=0, item_count=0, money=0, attachment=""):
        """
        快速发送邮件（根据C#代码实现）
        
        Args:
            title (str): 邮件标题
            content (str): 邮件内容
            recipient_id (str): 收件人ID
            item_id (int): 道具ID（保留兼容）
            item_count (int): 道具数量（保留兼容）
            money (int): 货币数量（保留兼容）
            attachment (str): 道具奖励字符串，如 "$p_95jd.lobby_resource.魂晶.root:999"
            
        Returns:
            dict: 发送结果
        """
        # 构建符合C#格式的邮件数据
        email_data = {
            "标题": title,
            "正文": content,
            "收件人ID": recipient_id,
            "道具奖励": attachment,
            "邮件类型": 1,
            "目标类型": 1,  # 个人邮件
            "接收方式": 0,
            "是否定时邮件": False,
            "排除新玩家": False,
            "有效天数": 90,
            "环境": "formal",
            "发件人": "系统管理员"
        }
        
        return self.send_email(email_data)
    
    def send_to_all(self, title, content, item_id=0, item_count=0, money=0, attachment=""):
        """
        发送全体邮件（根据C#代码实现）
        
        Args:
            title (str): 邮件标题
            content (str): 邮件内容
            item_id (int): 道具ID（保留兼容）
            item_count (int): 道具数量（保留兼容）
            money (int): 货币数量（保留兼容）
            attachment (str): 道具奖励字符串，如 "$p_95jd.lobby_resource.魂晶.root:999"
            
        Returns:
            dict: 发送结果
        """
        # 构建符合C#格式的邮件数据
        email_data = {
            "标题": title,
            "正文": content,
            "道具奖励": attachment,
            "邮件类型": 1,
            "目标类型": 0,  # 全体邮件
            "接收方式": 0,
            "是否定时邮件": False,
            "排除新玩家": False,
            "有效天数": 90,
            "环境": "formal",
            "发件人": "系统管理员"
        }
        
        return self.send_email(email_data)
    
    def _add_email(self, email_data):
        """
        添加邮件到系统（根据C#代码实现）
        
        Args:
            email_data (dict): 邮件数据
            
        Returns:
            dict: 添加结果
        """
        # 准备请求数据（提取为独立函数避免重复代码）
        def prepare_request_data():
            import time
            current_time_ms = int(time.time() * 1000)
            
            # 构建payload数据
            payload = {
                "attachment": email_data.get("道具奖励", ""),
                "content": email_data.get("正文", ""),
                "content_type": email_data.get("邮件类型", 1),
                "env": email_data.get("环境", "formal"),
                "include_new_player": email_data.get("排除新玩家", False),
                "map_name": self.project_id,
                "recieve_type": email_data.get("接收方式", 0),
                "send_type": email_data.get("是否定时邮件", False),
                "sender_name": email_data.get("发件人", "系统管理员"),
                "start_time": current_time_ms,
                "target": email_data.get("收件人ID", "") if email_data.get("目标类型", 1) == 1 else "",
                "target_type": email_data.get("目标类型", 1),
                "time_limit": email_data.get("有效天数", 90),
                "title": email_data.get("标题", "系统邮件")
            }
            
            # 构建完整请求数据
            request_data = {
                "firm": self.project_id,
                "table_id": self.table_id,
                "payload": payload
            }
            
            return request_data
        
        # 执行请求（带重试逻辑）
        for attempt in range(self.max_retries + 1):
            try:
                print(f"准备添加邮件到系统 (尝试 {attempt + 1}/{self.max_retries + 1})")
                print(f"原始邮件数据: {email_data}")
                
                request_data = prepare_request_data()
                
                print(f"准备发送邮件请求到: {self.add_email_url}")
                print(f"请求数据: {json.dumps(request_data, ensure_ascii=False)}")
                print(f"当前使用的token: {self.auth_token[:20]}...{self.auth_token[-8:]}")
                
                response = self.session.post(
                    self.add_email_url, 
                    data=json.dumps(request_data),
                    timeout=30  # 添加超时设置
                )
                
                print(f"邮件服务响应状态码: {response.status_code}")
                print(f"邮件服务响应内容: {response.text}")
                
                # 处理401错误（需要刷新token）
                if response.status_code == 401:
                    print(f"收到401未授权错误，token可能已过期")
                    
                    # 如果是最后一次尝试，直接返回错误
                    if attempt >= self.max_retries:
                        error_msg = f"HTTP错误: 401 Unauthorized，已尝试刷新token但仍失败"
                        print(error_msg)
                        return {"success": False, "message": error_msg, "response": response.text}
                    
                    # 尝试刷新token（这里我们只能提示，实际刷新需要外部调用）
                    print("需要刷新token，请使用刷新token命令或等待自动刷新")
                    
                    # 尝试从cookie中获取新token（如果有）
                    if 'token' in self.session.cookies:
                        new_token = self.session.cookies['token']
                        if new_token and new_token != self.auth_token:
                            print(f"从cookie中获取到新token")
                            self._update_auth_headers(new_token)
                            continue  # 重试请求
                    
                    # 添加延迟后重试
                    print(f"等待2秒后重试...")
                    import time
                    time.sleep(2)
                    continue
                
                # 处理其他状态码
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"响应解析结果: {result}")
                        
                        # 返回统一格式的结果
                        success = result.get("result") == 0
                        row_id = None
                        if success and result.get("data"):
                            row_id = result["data"].get("row_id")
                        
                        return {
                            "success": success,
                            "message": result.get("msg", "未知响应"),
                            "row_id": row_id,
                            "raw_response": response.text
                        }
                    except json.JSONDecodeError:
                        error_msg = f"响应解析失败: {response.text}"
                        print(error_msg)
                        return {"success": False, "message": error_msg}
                else:
                    error_msg = f"HTTP错误: {response.status_code} {response.reason}"
                    print(error_msg)
                    return {"success": False, "message": error_msg, "response": response.text}
                    
            except requests.Timeout:
                error_msg = f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1})"
                print(error_msg)
                if attempt >= self.max_retries:
                    return {"success": False, "message": error_msg}
                print("等待3秒后重试...")
                import time
                time.sleep(3)
            except requests.ConnectionError:
                error_msg = f"连接错误 (尝试 {attempt + 1}/{self.max_retries + 1})"
                print(error_msg)
                if attempt >= self.max_retries:
                    return {"success": False, "message": error_msg}
                print("等待3秒后重试...")
                import time
                time.sleep(3)
            except requests.RequestException as e:
                error_msg = f"HTTP请求错误: {str(e)} (尝试 {attempt + 1}/{self.max_retries + 1})"
                print(error_msg)
                if hasattr(e, 'response') and e.response is not None:
                    error_msg += f", 状态码: {e.response.status_code}, 响应: {e.response.text}"
                    # 检查是否是401错误
                    if e.response.status_code == 401 and attempt < self.max_retries:
                        print("401错误，需要刷新token")
                        continue
                if attempt >= self.max_retries:
                    return {"success": False, "message": error_msg}
                print("等待2秒后重试...")
                import time
                time.sleep(2)
            except Exception as e:
                error_msg = f"添加邮件异常: {str(e)} (尝试 {attempt + 1}/{self.max_retries + 1})"
                print(error_msg)
                import traceback
                print(f"异常堆栈: {traceback.format_exc()}")
                if attempt >= self.max_retries:
                    return {"success": False, "message": error_msg}
                print("等待2秒后重试...")
                import time
                time.sleep(2)
        
        # 所有尝试都失败
        return {"success": False, "message": "所有尝试均失败，请检查token是否有效"}

# 主程序功能整合
@register("sce_spark_game", "开发者", "SCE星火游戏插件", "1.3.1")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 初始化token管理，先设置token文件名
        self.token_file = "系统token储存.json"
        
        # 初始化默认token（仅作为备份使用）
        default_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaW5mbyI6eyJ1c2VySWQiOjE0MDgxNzcxODUsIm5hbWUiOiLmmq7pm6giLCJhdmF0YXIiOiJodHRwczovL2ltZzMudGFwaW1nLmNvbS9hdmF0YXJzL2V0YWcvRnVSVnh1d1ZiM21BRTRTSWVCNkxhbkQ2UjltbC5wbmc_aW1hZ2VNb2dyMi9hdXRvLW9yaWVudC9zdHJpcC90aHVtYm5haWwvITI3MHgyNzByL2dyYXZpdHkvQ2VudGVyL2Nyb3AvMjcweDI3MC9mb3JtYXQvanBnL2ludGVybGFjZS8xL3F1YWxpdHkvODAiLCJ1bmlvbl9pZCI6IkMzNXc1YTEtaHV5akVMVzZNWXBaY0Vxd1pQMlUzM1c2RFVlbGg4blJMUWhnYXR1RCIsInRva2VuIjoiNGJlNWE4ODkzZDQ0NmU3ZTYwNzI5MzkwNGU5YmJjMGRjMDk2MGNiZThjYTBiYmRlYWZlOTNiYTM4NWE2OWExNCIsInRva2VuX3NlY3JldCI6Ijk3ODM4NjVhNWNhYWI2MzMxMmY0MDllODA2MjEzNjg1MDY3YmI5MjYifSwiaWF0IjoxNzYyMjMzMzE2LCJleHAiOjE3NjIzMTk3MTZ9.Hyxy9jwdxqGQaRI6t681qOuwHVVegk60kzNpByo5BZ0"
        
        # 优先从token文件加载auth_token
        try:
            token_data = Json.读取Json字典(self.token_file)
            self.auth_token = token_data.get("token", default_token)
            logger.info(f"已从{self.token_file}加载auth_token，长度: {len(self.auth_token)} 字符")
        except Exception as e:
            logger.warning(f"从token文件加载auth_token失败: {e}，使用默认token")
            self.auth_token = default_token
        
        # 初始化游戏配置字典，包含URL
        self.game_configs = {
            "捉妖:钟馗": {
                "项目ID": "p_95jd",
                "发送的奖励": "$p_95jd.lobby_resource.魂晶.root:999",
                "URL": "https://developer.spark.xd.com/dashboard/p_95jd/firm0_lv_1_1_1?tab_firm0_app_submit_game=firm0_app_submit_game&tab_firm0_app_submit_game_history=firm0_app_submit_game_history"
            },
            "魂晶": {
                "项目ID": "p_95jd",
                "发送的奖励": "$p_95jd.lobby_resource.魂晶.root:100",
                "URL": "https://developer.spark.xd.com/dashboard/p_95jd/firm0_lv_1_1_1?tab_firm0_app_submit_game=firm0_app_submit_game&tab_firm0_app_submit_game_history=firm0_app_submit_game_history"
            },
            "金币": {
                "项目ID": "p_95jd",
                "发送的奖励": "$p_95jd.lobby_resource.金币.root:5000",
                "URL": "https://developer.spark.xd.com/dashboard/p_95jd/firm0_lv_1_1_1?tab_firm0_app_submit_game=firm0_app_submit_game&tab_firm0_app_submit_game_history=firm0_app_submit_game_history"
            },
            "钻石": {
                "项目ID": "p_95jd",
                "发送的奖励": "$p_95jd.lobby_resource.钻石.root:50",
                "URL": "https://developer.spark.xd.com/dashboard/p_95jd/firm0_lv_1_1_1?tab_firm0_app_submit_game=firm0_app_submit_game&tab_firm0_app_submit_game_history=firm0_app_submit_game_history"
            }
        }
        
        # 加载current_token（可能与auth_token不同，用于实际请求）
        self._load_token()

    async def initialize(self):
        """初始化插件，确保数据目录存在"""
        try:
            # 确保UserData目录存在
            JsonHandler.获取文件路径("test.json", True)
            
            # 检查并更新数据保质期
            self._check_and_update_date()
            
            # 启动定时任务，每分钟检查一次日期
            self.date_check_task = asyncio.create_task(self._schedule_date_check())
            
            # 启动定时任务，每15分钟刷新一次网页并更新token
            self.refresh_task = asyncio.create_task(self._schedule_web_refresh())
            
            logger.info("SCE星火游戏插件初始化成功")
        except Exception as e:
            logger.error(f"SCE星火游戏插件初始化失败: {e}")
    
    def _parse_token_expiry(self, token):
        """解析JWT token中的过期时间"""
        try:
            # JWT token通常分为三部分，第二部分包含payload
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # 解码base64的payload部分
            import base64
            payload = parts[1]
            # 确保padding正确
            payload += '=' * ((4 - len(payload) % 4) % 4)
            decoded = base64.urlsafe_b64decode(payload).decode('utf-8')
            payload_data = json.loads(decoded)
            
            # 获取过期时间戳
            if 'exp' in payload_data:
                exp_time = datetime.datetime.fromtimestamp(payload_data['exp'])
                return exp_time
            return None
        except Exception as e:
            logger.error(f"解析token过期时间失败: {e}")
            return None
    
    def _is_token_valid(self, token):
        """验证token是否有效"""
        if not token:
            return False
            
        # 检查token格式
        if len(token) < 30 or '.' not in token:
            logger.warning(f"无效的token格式: 长度不足或缺少分隔符")
            return False
            
        # 检查过期时间
        expiry = self._parse_token_expiry(token)
        if expiry:
            time_until_expiry = expiry - datetime.datetime.now()
            if time_until_expiry.total_seconds() < 0:
                logger.warning(f"token已过期: {expiry}")
                return False
            elif time_until_expiry.total_seconds() < 300:  # 5分钟内过期
                logger.info(f"token将在5分钟内过期: {expiry}")
        
        return True
    
    def _load_token(self):
        """从文件加载token"""
        try:
            token_data = Json.读取Json字典(self.token_file)
            token = token_data.get("token", self.auth_token)
            
            # 验证token有效性
            if self._is_token_valid(token):
                self.current_token = token
                logger.info(f"已加载有效token，长度: {len(token)} 字符")
                
                # 检查过期时间并提前刷新
                expiry = self._parse_token_expiry(token)
                if expiry:
                    time_until_expiry = expiry - datetime.datetime.now()
                    logger.info(f"token过期时间: {expiry}，剩余时间: {time_until_expiry}")
                    # 如果token将在30分钟内过期，记录警告
                    if time_until_expiry.total_seconds() < 1800:
                        logger.warning(f"token将在30分钟内过期，建议尽快刷新")
            else:
                logger.warning(f"加载的token无效，使用默认token")
                self.current_token = self.auth_token
        except Exception as e:
            logger.error(f"加载token失败: {e}")
            self.current_token = self.auth_token  # 使用默认token
    
    def _save_token(self, token):
        """保存token到文件，包含有效性验证"""
        # 首先验证token有效性
        if not self._is_token_valid(token):
            logger.error(f"尝试保存无效token，放弃保存")
            return False
            
        # 尝试保存token，增加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 一次性读取并更新整个文件，减少文件操作次数
                token_data = Json.读取Json字典(self.token_file)
                token_data["token"] = token
                token_data["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 解析并保存过期时间
                expiry = self._parse_token_expiry(token)
                if expiry:
                    token_data["expiry"] = expiry.strftime("%Y-%m-%d %H:%M:%S")
                
                # 写入文件
                文件路径 = JsonHandler.获取文件路径(self.token_file, True)
                with open(文件路径, 'w', encoding='utf-8') as f:
                    json.dump(token_data, f, ensure_ascii=False, indent=2)
                
                # 更新当前token
                self.current_token = token
                logger.info(f"已保存新token，长度: {len(token)} 字符，尝试次数: {attempt + 1}")
                return True
            except Exception as e:
                logger.error(f"保存token失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # 等待一段时间后重试
                    time.sleep(1)
                else:
                    logger.error(f"保存token达到最大重试次数，保存失败")
        return False
    
    async def _check_token_expiry(self):
        """检查token是否即将过期，如果是则提前刷新"""
        try:
            # 先加载最新token
            self._load_token()
            
            # 解析token过期时间
            expiry = self._parse_token_expiry(self.current_token)
            if expiry:
                time_until_expiry = expiry - datetime.datetime.now()
                # 如果token将在10分钟内过期，立即刷新
                if 0 < time_until_expiry.total_seconds() < 600:
                    logger.warning(f"token将在10分钟内过期，立即刷新")
                    await self._refresh_all_games()
                    return True
                logger.info(f"token状态正常，剩余有效期: {time_until_expiry}")
            return False
        except Exception as e:
            logger.error(f"检查token过期时间失败: {e}")
            return False
    
    async def _schedule_web_refresh(self):
        """定时任务：固定时间刷新游戏网页并更新token"""
        logger.info("启动网页刷新定时任务，包含固定时间刷新和token过期检查")
        
        # 定义刷新间隔（秒）
        refresh_interval = 15 * 60  # 15分钟
        check_interval = 5 * 60     # 5分钟检查一次token过期
        last_refresh_time = datetime.datetime.now()
        last_check_time = datetime.datetime.now()
        
        try:
            while True:
                current_time = datetime.datetime.now()
                
                # 检查是否需要刷新所有游戏（每15分钟）
                if (current_time - last_refresh_time).total_seconds() >= refresh_interval:
                    logger.info(f"到达固定刷新时间，距离上次刷新: {(current_time - last_refresh_time).total_seconds():.2f}秒")
                    try:
                        await self._refresh_all_games()
                        last_refresh_time = current_time
                    except Exception as e:
                        logger.error(f"定时刷新网页时出错: {e}")
                        import traceback
                        logger.error(f"异常堆栈: {traceback.format_exc()}")
                
                # 检查token是否即将过期（每5分钟）
                if (current_time - last_check_time).total_seconds() >= check_interval:
                    await self._check_token_expiry()
                    last_check_time = current_time
                
                # 短暂休眠，避免CPU占用过高
                await asyncio.sleep(60)  # 每分钟检查一次
                
        except asyncio.CancelledError:
            logger.info("网页刷新任务已取消")
        except KeyboardInterrupt:
            logger.info("收到键盘中断，停止网页刷新任务")
        except Exception as e:
            logger.error(f"网页刷新定时任务异常: {e}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            # 发生异常后等待一段时间再尝试恢复
            await asyncio.sleep(60)
            # 尝试重新启动任务
            logger.info("尝试重新启动网页刷新任务")
            asyncio.create_task(self._schedule_web_refresh())
    
    async def _refresh_single_game(self, game_name, url, session):
        """刷新单个游戏网页，带重试机制"""
        max_retries = 3
        base_delay = 3  # 基础延迟时间（秒）
        
        for attempt in range(max_retries):
            try:
                logger.info(f"刷新游戏: {game_name}, URL: {url}, 尝试 {attempt + 1}/{max_retries}")
                
                # 设置headers模拟浏览器请求
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                    'Connection': 'keep-alive'
                }
                
                # 如果当前有token，添加到请求中
                if self.current_token:
                    # 可以通过header或cookie传递token
                    session.headers.update({'Authorization': f'Bearer {self.current_token}'})
                    session.cookies.set('token', self.current_token)
                
                # 发送GET请求模拟网页刷新
                response = session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                logger.info(f"游戏{game_name}刷新成功，状态码: {response.status_code}")
                
                # 从cookie中获取新token
                if 'token' in session.cookies:
                    cookie_token = session.cookies['token']
                    if cookie_token and cookie_token != self.current_token:
                        logger.info(f"发现新token，游戏: {game_name}")
                        return True, cookie_token
                
                # 检查响应内容是否表明需要重新登录
                if 'login' in response.text.lower() or '登录' in response.text:
                    logger.warning(f"游戏{game_name}响应中包含登录提示，可能需要重新认证")
                
                return True, None
            except requests.Timeout:
                logger.error(f"刷新游戏{game_name}超时 (尝试 {attempt + 1}/{max_retries})")
            except requests.ConnectionError:
                logger.error(f"刷新游戏{game_name}连接错误 (尝试 {attempt + 1}/{max_retries})")
            except requests.HTTPError as e:
                logger.error(f"刷新游戏{game_name}HTTP错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                # 对于401/403错误，可能是token过期，立即返回
                if response.status_code in [401, 403]:
                    logger.warning(f"游戏{game_name}返回认证错误，token可能已过期")
                    break
            except Exception as e:
                logger.error(f"刷新游戏{game_name}失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            # 如果不是最后一次尝试，等待一段时间后重试
            if attempt < max_retries - 1:
                delay = base_delay * (attempt + 1)  # 指数退避
                logger.info(f"等待 {delay} 秒后重试游戏 {game_name}")
                await asyncio.sleep(delay)
        
        return False, None
    
    async def _refresh_all_games(self):
        """刷新所有游戏的网页并更新token，带增强的错误处理"""
        logger.info(f"开始刷新所有游戏网页，共{len(self.game_configs)}个游戏")
        
        # 使用同一个session来保存cookie和token
        session = requests.Session()
        new_token = None
        success_count = 0
        failure_count = 0
        
        # 检查是否有游戏配置
        if not self.game_configs:
            logger.warning("没有找到游戏配置，跳过刷新")
            return None
        
        for game_name, config in self.game_configs.items():
            url = config.get("URL")
            if not url:
                logger.warning(f"游戏 {game_name} 没有配置URL，跳过刷新")
                failure_count += 1
                continue
            
            try:
                # 刷新单个游戏，带重试
                success, game_token = await self._refresh_single_game(game_name, url, session)
                
                if success:
                    success_count += 1
                    # 如果找到新token，更新new_token
                    if game_token:
                        new_token = game_token
                else:
                    failure_count += 1
                
                # 避免频繁请求，添加延迟，使用随机延迟避免固定间隔
                import random
                delay = 2 + random.uniform(0, 1)
                logger.info(f"等待 {delay:.2f} 秒后刷新下一个游戏")
                await asyncio.sleep(delay)
                
            except Exception as e:
                failure_count += 1
                logger.error(f"处理游戏 {game_name} 时发生异常: {e}")
        
        # 统计信息
        logger.info(f"游戏刷新统计: 成功 {success_count}, 失败 {failure_count}, 总计 {len(self.game_configs)}")
        
        # 如果找到新token，保存它
        if new_token:
            save_success = self._save_token(new_token)
            if save_success:
                logger.info(f"成功保存新token")
                return {
                    "success": True,
                    "token": new_token,
                    "message": "成功刷新并保存新token"
                }
            else:
                logger.error(f"保存新token失败")
                return {
                    "success": False,
                    "message": "找到新token但保存失败"
                }
        else:
            logger.info("未发现新token，继续使用当前token")
            # 即使没有找到新token，如果所有游戏刷新都成功了，也算刷新成功
            if failure_count == 0:
                return {
                    "success": True,
                    "token": self.current_token,
                    "message": "所有游戏刷新成功，但未发现新token"
                }
            else:
                return {
                    "success": False,
                    "message": f"部分游戏刷新失败，成功: {success_count}, 失败: {failure_count}"
                }
        
        logger.info("所有游戏网页刷新完成")
        return {"success": False, "message": "未知错误"}
    
    async def _schedule_date_check(self):
        """定时任务：每分钟检查一次数据保质期"""
        logger.info("启动每分钟数据保质期检查任务")
        try:
            while True:
                # 每分钟执行一次检查
                await asyncio.sleep(60)
                try:
                    self._check_and_update_date()
                except Exception as e:
                    logger.error(f"定时检查日期时出错: {e}")
        except asyncio.CancelledError:
            logger.info("数据保质期检查任务已取消")
        except Exception as e:
            logger.error(f"定时任务异常: {e}")
    
    def _check_and_update_date(self):
        """检查并更新数据保质期，重置签到状态"""
        try:
            # 获取当前日期的day值
            current_day = str(datetime.datetime.now().day)
            
            # 读取数据保质期
            保质期数据 = Json.读取Json字典("数据保质期.json")
            存储的日期 = Json.获取值(保质期数据, "日期", "")
            
            # 比较日期
            if current_day != 存储的日期:
                logger.info(f"日期变更: 从{存储的日期}更新到{current_day}，重置所有签到状态")
                
                # 更新数据保质期
                Json.添加或更新("数据保质期.json", "日期", current_day)
                
                # 重置所有玩家的签到状态
                签到数据 = Json.读取Json字典("玩家今天是否签到过.json")
                if 签到数据:
                    # 创建新的签到数据字典，所有值设为false
                    新签到数据 = {key: "false" for key in 签到数据.keys()}
                    # 写入文件
                    文件路径 = JsonHandler.获取文件路径("玩家今天是否签到过.json", True)
                    with open(文件路径, 'w', encoding='utf-8') as f:
                        json.dump(新签到数据, f, ensure_ascii=False, indent=2)
                    logger.info(f"已重置{len(新签到数据)}条签到记录")
        except Exception as e:
            logger.error(f"检查和更新数据保质期时出错: {e}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")

    async def 发送消息(self, event: AstrMessageEvent, 消息内容: str):
        """发送消息封装函数"""
        yield event.plain_result(消息内容)

    async def send_personal_reward_email(self, 认证令牌, 项目ID, 奖励内容, 发送的用户, 邮件标题, 邮件正文, 游戏名称=None):
        """发送个人奖励邮件（适配C#邮件格式）"""
        try:
            # 如果没有提供游戏名称，尝试从游戏配置中获取第一个
            if not 游戏名称 and self.game_configs:
                游戏名称 = list(self.game_configs.keys())[0]
            
            # 获取附件奖励
            attachment = ""
            display_name = "奖励"
            count = 1
            
            # 检查是否有特殊格式的奖励配置
            if 游戏名称 in self.game_configs and "发送的奖励" in self.game_configs[游戏名称]:
                奖励字符串 = self.game_configs[游戏名称]["发送的奖励"]
                try:
                    # 直接使用游戏配置中的奖励信息作为附件
                    attachment = 奖励字符串
                    
                    # 解析显示名称和数量用于邮件内容
                    if ":" in 奖励字符串:
                        奖励_id, 数量 = 奖励字符串.split(":")
                        count = int(数量)
                        # 从奖励ID中提取显示名称
                        if "." in 奖励_id:
                            name_parts = 奖励_id.split(".")
                            for part in name_parts:
                                if any('\u4e00' <= char <= '\u9fff' for char in part):
                                    display_name = part
                                    break
                except Exception as e:
                    print(f"解析奖励字符串异常: {str(e)}")
            
            # 更新邮件正文，包含奖励信息
            if display_name and count:
                # 如果邮件正文中没有包含奖励信息，则添加
                if f"{display_name} x{count}" not in 邮件正文:
                    邮件正文 = f"{邮件正文}\n\n获得奖励：{display_name} x{count}"
            
            # 先验证current_token是否有效
            token_to_use = self.current_token or 认证令牌
            if not token_to_use or len(token_to_use) < 10:  # 简单的长度验证
                print("警告: 当前token可能无效，尝试使用默认token")
                token_to_use = self.auth_token
            
            logger.info(f"使用存储的token发送邮件，token长度: {len(token_to_use)} 字符")
            
            # 创建邮件服务并发送邮件（增加重试设置）
            email_service = EmailService(
                auth_token=token_to_use,
                project_id=项目ID,
                max_retries=3
            )
            result = email_service.quick_send(邮件标题, 邮件正文, 发送的用户, attachment=attachment)
            
            # 检查是否是token相关错误
            message = result.get('message', '')
            if not result.get('success') and (message and ('token' in message.lower() or '认证' in message or '401' in message)):
                print("检测到token过期或无效，尝试刷新token")
                # 立即尝试刷新token
                refresh_result = await self._refresh_all_games()
                
                # 处理新的返回格式
                if isinstance(refresh_result, dict):
                    if refresh_result.get("success"):
                        new_token = refresh_result.get("token")
                        if new_token and self._is_token_valid(new_token):
                            print(f"token刷新成功，新token: {new_token[:20]}...{new_token[-8:]}")
                            # 使用新token重新发送邮件
                    else:
                        logger.error(f"token刷新失败: {refresh_result.get('message', '未知错误')}")
                        # 记录失败信息
                        self._log_email_failure(发送的用户, 奖励内容, "Token刷新失败: " + refresh_result.get('message', '未知错误'))
                        return False
                # 向后兼容旧的返回格式（直接返回token字符串）
                elif refresh_result and self._is_token_valid(refresh_result):
                    new_token = refresh_result
                    print(f"token刷新成功（旧格式），新token: {new_token[:20]}...{new_token[-8:]}")
                    # 使用新token重新发送邮件
                else:
                    logger.error(f"token刷新失败: 返回值无效或为None")
                    # 记录失败信息
                    self._log_email_failure(发送的用户, 奖励内容, "Token刷新失败: 返回值无效")
                    return False
            
            if result.get('success'):
                logger.info(f"奖励邮件发送成功: {发送的用户}")
                return True
            else:
                logger.error(f"奖励邮件发送失败: {发送的用户}, 原因: {result.get('message')}")
                # 记录失败信息
                self._log_email_failure(发送的用户, 奖励内容, result.get('message'))
                return False
        except requests.RequestException as e:
            error_msg = f"发送奖励邮件网络异常: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            self._log_email_failure(发送的用户, 奖励内容, error_msg)
            return False
        except Exception as e:
            error_msg = f"发送奖励邮件异常: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            self._log_email_failure(发送的用户, 奖励内容, error_msg)
            return False
    
    def _log_email_failure(self, user_id, reward_info, error_msg):
        """
        记录邮件发送失败信息
        
        Args:
            user_id (str): 用户ID
            reward_info (dict): 奖励信息
            error_msg (str): 错误信息
        """
        import os
        import datetime
        
        # 创建失败日志目录
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 日志文件名
        log_file = os.path.join(log_dir, "email_failures.log")
        
        # 构建日志内容
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] 用户: {user_id}, 奖励: {reward_info}, 错误: {error_msg}\n"
        
        # 写入日志文件
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            print(f"邮件发送失败信息已记录到: {log_file}")
        except Exception as e:
            print(f"记录失败日志异常: {str(e)}")

    @filter.command("签到")
    async def handle_checkin(self, event: AstrMessageEvent):
        """处理签到功能"""
        # 每次签到前检查日期，确保签到状态正确
        self._check_and_update_date()
        
        message_str = event.message_str.strip()
        author_id = event.get_sender_id()
        
        # 解析游戏名称
        parts = message_str.split(" ")
        if len(parts) > 1:
            游戏名称 = parts[1]
            # 单游戏签到
            async for msg in self.handle_single_checkin(event, author_id, 游戏名称):
                yield msg
        else:
            # 批量签到
            async for msg in self.handle_batch_checkin(event, author_id):
                yield msg

    async def handle_single_checkin(self, event: AstrMessageEvent, author_id, 游戏名称):
        """处理单个游戏签到"""
        # 使用复合键格式: "玩家ID_游戏ID"
        复合键 = f"{author_id}_{游戏名称}"
        
        # 检查是否已签到
        if Json.获取值(Json.读取Json字典("玩家今天是否签到过.json"), 复合键) is None:
            Json.添加或更新("玩家今天是否签到过.json", 复合键, "false")
        
        if Json.获取值(Json.读取Json字典("玩家今天是否签到过.json"), 复合键) != "true":
            # 检查ID绑定
            玩家数据 = Json.读取Json字典("玩家绑定id数据存储.json")
            发送的用户 = Json.获取值(玩家数据, author_id)
            
            if not 发送的用户:
                async for msg in self.发送消息(event, "ID未绑定，请发送\"绑定ID xxx\"进行绑定"):
                    yield msg
                return
            
            # 发送奖励邮件
            # 从游戏配置中获取项目ID和奖励信息
            游戏配置 = self.game_configs.get(游戏名称, {})
            项目ID = 游戏配置.get("项目ID", "mock_project")
            发送的奖励 = {"items": []}
            
            # 解析奖励格式: "$p_95jd.lobby_resource.魂晶.root:999"
            奖励字符串 = 游戏配置.get("发送的奖励", "")
            if 奖励字符串:
                try:
                    # 提取奖励ID和数量
                    奖励_id, 数量 = 奖励字符串.split(":")
                    数量 = int(数量)
                    # 提取显示名称
                    display_name = 奖励_id.split(".")[-1].split(":")[0]
                    发送的奖励["items"].append(f"{display_name}×{数量}")
                except:
                    # 如果解析失败，使用默认奖励
                    发送的奖励["items"] = ["签到奖励"]
            else:
                发送的奖励["items"] = ["签到奖励"]
                
            邮件标题 = "签到奖励"
            邮件正文 = f"恭喜您在{游戏名称}签到成功！"

            邮件返回值 = await self.send_personal_reward_email(self.auth_token, 项目ID, 发送的奖励, 发送的用户, 邮件标题, 邮件正文, 游戏名称)
            
            if 邮件返回值:
                # 更新签到状态
                Json.添加或更新("玩家今天是否签到过.json", 复合键, "true")
                
                # 处理连续签到
                async for msg in self.handle_continuous_checkin(event, author_id, 游戏名称):
                    yield msg
        else:
            async for msg in self.发送消息(event, f"您今天已经在{游戏名称}签到过了，请明天再来！"):
                yield msg

    @filter.command("查看游戏列表")
    async def handle_view_games(self, event: AstrMessageEvent):
        """查看签到游戏列表，输出格式为游戏名称+奖励*数量"""
        if not self.game_configs:
            async for msg in self.发送消息(event, "当前没有配置任何签到游戏"):
                yield msg
            return
        
        # 构建游戏列表消息
        游戏列表 = []
        for 游戏名称, 配置 in self.game_configs.items():
            奖励字符串 = 配置.get("发送的奖励", "")
            if 奖励字符串 and ":" in 奖励字符串:
                try:
                    # 解析奖励ID和数量
                    奖励_id, 数量 = 奖励字符串.split(":")
                    # 尝试从奖励ID中提取显示名称
                    name_parts = 奖励_id.split(".")
                    显示名称 = "奖励"
                    for part in name_parts:
                        if any('\u4e00' <= char <= '\u9fff' for char in part):
                            显示名称 = part
                            break
                    # 如果没有找到中文字符，使用最后一部分
                    if 显示名称 == "奖励" and name_parts:
                        显示名称 = name_parts[-1]
                    游戏列表.append(f"{游戏名称}: {显示名称}*{数量}")
                except:
                    游戏列表.append(f"{游戏名称}: 奖励*1")
            else:
                游戏列表.append(f"{游戏名称}: 奖励*1")
        
        # 发送游戏列表
        消息内容 = "签到游戏列表：\n" + "\n".join(游戏列表)
        async for msg in self.发送消息(event, 消息内容):
            yield msg
    
    async def handle_continuous_checkin(self, event: AstrMessageEvent, author_id, 游戏名称):
        """处理连续签到逻辑"""
        签到统计数据 = Json.读取Json字典("玩家连续签到数据.json")
        连续签到复合键 = f"{author_id}_连续签到"
        上次签到日期键 = f"{author_id}_上次签到日期"
        
        当前日期 = datetime.datetime.now().strftime("%Y-%m-%d")
        连续签到天数 = 0
        
        # 获取上次签到日期
        上次签到日期 = Json.获取值(签到统计数据, 上次签到日期键, "")
        
        if not 上次签到日期:
            # 第一次签到
            连续签到天数 = 1
        else:
            try:
                last_date = datetime.datetime.strptime(上次签到日期, "%Y-%m-%d")
                current_date = datetime.datetime.strptime(当前日期, "%Y-%m-%d")
                if (current_date - last_date).days == 1:
                    # 连续签到
                    连续签到天数 = int(Json.获取值(签到统计数据, 连续签到复合键, "0")) + 1
                elif 上次签到日期 == 当前日期:
                    # 同一天签到
                    连续签到天数 = int(Json.获取值(签到统计数据, 连续签到复合键, "0"))
                else:
                    # 中断连续签到
                    连续签到天数 = 1
            except:
                连续签到天数 = 1
        
        # 保存签到数据
        Json.添加或更新("玩家连续签到数据.json", 连续签到复合键, str(连续签到天数))
        Json.添加或更新("玩家连续签到数据.json", 上次签到日期键, 当前日期)
        
        # 计算活跃度奖励
        基础活跃度奖励 = 5
        额外活跃度奖励 = 0
        
        if 连续签到天数 >= 7:
            额外活跃度奖励 = 10
        elif 连续签到天数 >= 3:
            额外活跃度奖励 = 3
        
        总活跃度奖励 = 基础活跃度奖励 + 额外活跃度奖励
        
        # 增加活跃度
        活跃度数据 = Json.读取Json字典("玩家活跃度数据.json")
        当前活跃度 = Json.获取值(活跃度数据, author_id, "0")
        新活跃度 = int(当前活跃度) + 总活跃度奖励
        Json.添加或更新("玩家活跃度数据.json", author_id, str(新活跃度))
        
        # 发送签到成功消息
        # 从奖励内容中提取显示信息
        奖励显示信息 = []
        if 游戏名称 in self.game_configs:
            游戏配置 = self.game_configs[游戏名称]
            奖励字符串 = 游戏配置.get("发送的奖励", "")
            if 奖励字符串:
                try:
                    # 解析奖励格式
                    奖励_id, 数量 = 奖励字符串.split(":")
                    数量 = int(数量)
                    # 提取显示名称
                    display_name = 奖励_id.split(".")[-1].split(":")[0]
                    奖励显示信息.append(f"{display_name}×{数量}")
                except:
                    pass
        奖励显示信息 = "、".join(奖励显示信息) if 奖励显示信息 else "签到奖励"
        消息内容 = f"🔥 签到成功！恭喜您在{游戏名称}获得了奖励！\n"
        消息内容 += f"🎁 获得道具：{奖励显示信息}\n"
        消息内容 += f"💯 基础活跃度奖励：{基础活跃度奖励}点\n"
        
        if 额外活跃度奖励 > 0:
            消息内容 += f"✨ 连续签到{连续签到天数}天额外奖励：{额外活跃度奖励}点\n"
        
        消息内容 += f"🎊 当前连续签到天数：{连续签到天数}天\n"
        消息内容 += f"📈 总活跃度：{新活跃度}点"
        
        async for msg in self.发送消息(event, 消息内容):
            yield msg

    async def handle_batch_checkin(self, event: AstrMessageEvent, author_id):
        """处理批量签到"""
        async for msg in self.发送消息(event, "批量签到功能正在开发中"):
            yield msg

    @filter.command("绑定ID")
    async def handle_bind_id(self, event: AstrMessageEvent):
        """处理ID绑定"""
        message_str = event.message_str.strip()
        author_id = event.get_sender_id()
        
        parts = message_str.split(" ")
        if len(parts) > 1:
            游戏_id = parts[1]
            Json.添加或更新("玩家绑定id数据存储.json", author_id, 游戏_id)
            async for msg in self.发送消息(event, f"ID绑定成功！您的游戏ID是：{游戏_id}"):
                yield msg
        else:
            async for msg in self.发送消息(event, "请输入正确的格式：绑定ID xxx"):
                yield msg

    async def terminate(self):
        """插件销毁方法"""
        # 取消定时任务
        if hasattr(self, 'date_check_task'):
            self.date_check_task.cancel()
            try:
                await self.date_check_task
            except asyncio.CancelledError:
                pass
        
        # 取消网页刷新任务
        if hasattr(self, 'refresh_task'):
            self.refresh_task.cancel()
            try:
                await self.refresh_task
            except asyncio.CancelledError:
                pass
        
        logger.info("SCE星火游戏插件已停用")
    
    @filter.command("刷新token")
    async def handle_refresh_token(self, event: AstrMessageEvent):
        """手动刷新所有游戏的token"""
        try:
            async for msg in self.发送消息(event, "正在刷新所有游戏的token，请稍候..."):
                yield msg
            
            # 执行刷新操作
            new_token = await self._refresh_all_games()
            
            if new_token:
                async for msg in self.发送消息(event, "token刷新成功！已更新到最新值"):
                    yield msg
            else:
                async for msg in self.发送消息(event, "token刷新完成，但未发现新token，继续使用当前token"):
                    yield msg
        except Exception as e:
            logger.error(f"手动刷新token失败: {e}")
            async for msg in self.发送消息(event, f"刷新token时出错: {str(e)}"):
                yield msg
