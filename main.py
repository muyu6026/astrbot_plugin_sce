from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import json
import os
import datetime
import requests
from pathlib import Path

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
    """邮件发送服务类"""
    
    def __init__(self, auth_token, project_id="p_nm2d"):
        """
        初始化邮件服务
        
        Args:
            auth_token (str): 认证令牌
            project_id (str): 项目ID，默认值为"p_nm2d"
        """
        self.auth_token = auth_token
        self.project_id = project_id
        self.base_url = "https://adminapi-pd.spark.xd.com/api/v1/mail"
        self.session = requests.Session()
        # 设置默认请求头
        self.session.headers.update({
            "Cookie": f"token={auth_token}",
            "Content-Type": "application/json"
        })
    
    def send_email(self, email_data):
        """
        发送邮件
        
        Args:
            email_data (dict): 邮件数据，包含title, content, recipient等
            
        Returns:
            dict: 发送结果
        """
        try:
            # 第一步：添加邮件到系统
            add_result = self._add_email(email_data)
            if not add_result or not add_result.get('success'):
                return {"success": False, "message": "添加邮件失败"}
            
            # 第二步：触发发送
            email_id = add_result.get('data', {}).get('id')
            if not email_id:
                return {"success": False, "message": "未获取到邮件ID"}
            
            # 这里可以添加触发发送的逻辑
            return {"success": True, "message": "邮件发送成功", "email_id": email_id}
            
        except Exception as e:
            print(f"发送邮件异常: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def quick_send(self, title, content, recipient_id, item_id=0, item_count=0, money=0):
        """
        快速发送邮件
        
        Args:
            title (str): 邮件标题
            content (str): 邮件内容
            recipient_id (str): 收件人ID
            item_id (int): 道具ID，默认0
            item_count (int): 道具数量，默认0
            money (int): 货币数量，默认0
            
        Returns:
            dict: 发送结果
        """
        email_data = {
            "title": title,
            "content": content,
            "recipient": recipient_id,
            "item_id": item_id,
            "item_count": item_count,
            "money": money
        }
        return self.send_email(email_data)
    
    def send_to_all(self, title, content, item_id=0, item_count=0, money=0):
        """
        发送全体邮件
        
        Args:
            title (str): 邮件标题
            content (str): 邮件内容
            item_id (int): 道具ID，默认0
            item_count (int): 道具数量，默认0
            money (int): 货币数量，默认0
            
        Returns:
            dict: 发送结果
        """
        email_data = {
            "title": title,
            "content": content,
            "recipient": "all",
            "item_id": item_id,
            "item_count": item_count,
            "money": money
        }
        return self.send_email(email_data)
    
    def _add_email(self, email_data):
        """
        添加邮件到系统（内部方法）
        
        Args:
            email_data (dict): 邮件数据
            
        Returns:
            dict: 添加结果
        """
        try:
            url = f"{self.base_url}/add"
            request_data = {
                "firm": self.project_id,
                "mail_data": email_data
            }
            
            response = self.session.post(url, data=json.dumps(request_data))
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.RequestException as e:
            print(f"HTTP请求错误: {str(e)}")
            return None
        except json.JSONDecodeError:
            print("响应不是有效的JSON")
            return None

# 主程序功能整合
@register("sce_spark_game", "开发者", "SCE星火游戏插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化插件配置
        self.auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaW5mbyI6eyJ1c2VySWQiOjE0MDgxNzcxODUsIm5hbWUiOiLmmq7pm6giLCJhdmF0YXIiOiJodHRwczovL2ltZzMudGFwaW1nLmNvbS9hdmF0YXJzL2V0YWcvRnVSVnh1d1ZiM21BRTRTSWVCNkxhbkQ2UjltbC5wbmc_aW1hZ2VNb2dyMi9hdXRvLW9yaWVudC9zdHJpcC90aHVtYm5haWwvITI3MHgyNzByL2dyYXZpdHkvQ2VudGVyL2Nyb3AvMjcweDI3MC9mb3JtYXQvanBnL2ludGVybGFjZS8xL3F1YWxpdHkvODAiLCJ1bmlvbl9pZCI6IkMzNXc1YTEtaHV5akVMVzZNWXBaY0Vxd1pQMlUzM1c2RFVlbGg4blJMUWhnYXR1RCIsInRva2VuIjoiNGJlNWE4ODkzZDQ0NmU3ZTYwNzI5MzkwNGU5YmJjMGRjMDk2MGNiZThjYTBiYmRlYWZlOTNiYTM4NWE2OWExNCIsInRva2VuX3NlY3JldCI6Ijk3ODM4NjVhNWNhYWI2MzMxMmY0MDllODA2MjEzNjg1MDY3YmI5MjYifSwiaWF0IjoxNzYyMjMzMzE2LCJleHAiOjE3NjIzMTk3MTZ9.Hyxy9jwdxqGQaRI6t681qOuwHVVegk60kzNpByo5BZ0"
        
        # 初始化游戏配置字典
        self.game_configs = {
            "捉妖:钟馗": {
                "项目ID": "p_95jd",
                "发送的奖励": "$p_95jd.lobby_resource.魂晶.root:999"
            },
            "魂晶": {
                "项目ID": "p_95jd",
                "发送的奖励": "$p_95jd.lobby_resource.魂晶.root:100"
            },
            "金币": {
                "项目ID": "p_95jd",
                "发送的奖励": "$p_95jd.lobby_resource.金币.root:5000"
            },
            "钻石": {
                "项目ID": "p_95jd",
                "发送的奖励": "$p_95jd.lobby_resource.钻石.root:50"
            }
        }

    async def initialize(self):
        """初始化插件，确保数据目录存在"""
        try:
            # 确保UserData目录存在
            JsonHandler.获取文件路径("test.json", True)
            logger.info("SCE星火游戏插件初始化成功")
        except Exception as e:
            logger.error(f"SCE星火游戏插件初始化失败: {e}")

    async def 发送消息(self, event: AstrMessageEvent, 消息内容: str):
        """发送消息封装函数"""
        yield event.plain_result(消息内容)

    async def send_personal_reward_email(self, 认证令牌, 项目ID, 奖励内容, 发送的用户, 邮件标题, 邮件正文):
        """发送个人奖励邮件"""
        try:
            # 从奖励内容中提取道具信息
            items = 奖励内容.get("items", [])
            item_id = 0
            item_count = 0
            money = 0
            
            # 简单解析道具格式（如：金币×100）
            for item in items:
                if "金币" in item:
                    try:
                        money = int(item.split("×")[-1])
                    except:
                        pass
                else:
                    try:
                        item_count = int(item.split("×")[-1])
                    except:
                        item_count = 1
            
            email_service = EmailService(认证令牌, 项目ID)
            result = email_service.quick_send(邮件标题, 邮件正文, 发送的用户, item_id, item_count, money)
            
            if result.get('success'):
                logger.info(f"奖励邮件发送成功: {发送的用户}")
                return True
            else:
                logger.error(f"奖励邮件发送失败: {发送的用户}, 原因: {result.get('message')}")
                return False
        except Exception as e:
            logger.error(f"发送奖励邮件时出错: {e}")
            return False

    @filter.command("签到")
    async def handle_checkin(self, event: AstrMessageEvent):
        """处理签到功能"""
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

            邮件返回值 = await self.send_personal_reward_email(self.auth_token, 项目ID, 发送的奖励, 发送的用户, 邮件标题, 邮件正文)
            
            if 邮件返回值:
                # 更新签到状态
                Json.添加或更新("玩家今天是否签到过.json", 复合键, "true")
                
                # 处理连续签到
                async for msg in self.handle_continuous_checkin(event, author_id, 游戏名称):
                    yield msg
        else:
            async for msg in self.发送消息(event, f"您今天已经在{游戏名称}签到过了，请明天再来！"):
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
        logger.info("SCE星火游戏插件已停用")
