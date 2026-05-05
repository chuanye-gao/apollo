from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

CATEGORY_TOOLS = {
    "系统工具": [
        ("file.search", "搜索文件"), ("file.open", "打开文件"), ("file.copy", "复制文件"),
        ("file.delete", "删除文件"), ("file.rename", "重命名文件"), ("file.compress", "压缩文件"),
        ("folder.create", "新建文件夹"), ("clipboard.copy", "复制到剪贴板"), ("clipboard.read", "读取剪贴板"),
        ("app.open", "打开应用"), ("app.close", "关闭应用"), ("window.switch", "切换窗口"),
        ("window.screenshot", "窗口截图"), ("system.search", "系统搜索"), ("notification.create", "创建通知"),
        ("setting.wifi.toggle", "切换 Wi-Fi"), ("setting.bluetooth.toggle", "切换蓝牙"),
        ("volume.set", "设置音量"), ("brightness.set", "设置亮度"), ("password.generate", "生成密码"),
    ],
    "办公工具": [
        ("email.send", "发送邮件"), ("email.search", "搜索邮件"), ("email.draft", "起草邮件"),
        ("calendar.create", "创建日程"), ("calendar.query", "查询日程"), ("meeting.schedule", "安排会议"),
        ("document.create", "创建文档"), ("document.summarize", "总结文档"), ("document.translate", "翻译文档"),
        ("document.export_pdf", "导出 PDF"), ("spreadsheet.create", "创建表格"), ("spreadsheet.chart", "生成表格图表"),
        ("slides.create", "创建幻灯片"), ("todo.create", "创建待办"), ("todo.update", "更新待办"),
        ("approval.submit", "提交审批"), ("expense.create", "创建报销"), ("invoice.search", "查询发票"),
        ("contact.search", "查找联系人"), ("reminder.create", "创建提醒"), ("project.status", "查询项目状态"),
        ("note.create", "创建笔记"), ("note.search", "搜索笔记"), ("form.create", "创建表单"),
        ("report.generate", "生成报告"),
    ],
    "通讯工具": [
        ("message.send", "发送消息"), ("message.search", "搜索消息"), ("sms.send", "发送短信"),
        ("phone.call", "拨打电话"), ("contact.create", "新建联系人"), ("group.create", "创建群聊"),
        ("group.message", "发送群消息"), ("chat.search", "搜索聊天记录"), ("video_call.start", "发起视频通话"),
        ("voicemail.check", "检查语音留言"), ("broadcast.send", "发送公告"), ("slack.message", "发送 Slack 消息"),
        ("teams.message", "发送 Teams 消息"), ("social.post", "发布动态"), ("customer.reply", "回复客户"),
    ],
    "生活服务": [
        ("weather.query", "查询天气"), ("navigation.start", "开始导航"), ("taxi.call", "呼叫打车"),
        ("food.order", "点外卖"), ("hotel.search", "搜索酒店"), ("flight.search", "搜索机票"),
        ("train.search", "搜索火车票"), ("delivery.track", "查询快递"), ("package.send", "寄送包裹"),
        ("restaurant.book", "预订餐厅"), ("movie.ticket", "购买电影票"), ("doctor.appointment", "预约医生"),
        ("pharmacy.search", "查找药店"), ("bank.transfer", "银行转账"), ("bill.pay", "缴纳账单"),
        ("shopping.search", "搜索商品"), ("coupon.search", "搜索优惠券"), ("fitness.log", "记录运动"),
        ("water.log", "记录饮水"), ("habit.track", "打卡习惯"), ("parking.find", "查找停车场"),
        ("gas_station.find", "查找加油站"), ("event.search", "搜索活动"), ("laundry.pickup", "预约洗衣取送"),
        ("home_repair.book", "预约上门维修"),
    ],
    "多媒体": [
        ("music.play", "播放音乐"), ("podcast.play", "播放播客"), ("video.play", "播放视频"),
        ("album.search", "搜索相册"), ("photo.find", "查找照片"), ("photo.edit", "编辑照片"),
        ("photo.slideshow", "播放照片幻灯片"), ("camera.open", "打开相机"), ("recording.start", "开始录音"),
        ("recording.transcribe", "转写录音"), ("audiobook.play", "播放有声书"), ("ebook.open", "打开电子书"),
        ("playlist.create", "创建歌单"), ("radio.play", "播放电台"), ("screen.record", "录制屏幕"),
        ("subtitle.generate", "生成字幕"), ("image.generate", "生成图片"), ("video.edit", "剪辑视频"),
    ],
    "智能家居": [
        ("light.turn_on", "打开灯光"), ("light.turn_off", "关闭灯光"), ("light.set_brightness", "调节灯光亮度"),
        ("ac.set_temperature", "设置空调温度"), ("curtain.open", "打开窗帘"), ("curtain.close", "关闭窗帘"),
        ("tv.turn_on", "打开电视"), ("tv.channel", "切换电视频道"), ("robot_vacuum.start", "启动扫地机器人"),
        ("camera.view", "查看摄像头"), ("door.lock", "锁门"), ("door.unlock", "开门锁"),
        ("thermostat.set", "设置恒温器"), ("humidifier.set", "设置加湿器"), ("purifier.turn_on", "打开空气净化器"),
    ],
    "开发工具": [
        ("code.search", "搜索代码"), ("test.run", "运行测试"), ("issue.create", "创建 issue"),
        ("pr.query", "查询 PR"), ("deploy.start", "开始部署"), ("logs.search", "检索日志"),
        ("ci.status", "查询 CI 状态"), ("branch.create", "创建分支"), ("commit.summarize", "总结提交"),
        ("database.query", "查询数据库"), ("api.call", "调用 API"), ("incident.create", "创建故障单"),
        ("feature_flag.toggle", "切换功能开关"), ("release.create", "创建发布"), ("container.restart", "重启容器"),
        ("metric.query", "查询监控指标"), ("secrets.rotate", "轮换密钥"), ("dependency.check", "检查依赖"),
    ],
    "知识工具": [
        ("translate.text", "翻译文本"), ("summarize.text", "总结文本"), ("calculator.compute", "计算表达式"),
        ("unit.convert", "单位换算"), ("currency.convert", "汇率换算"), ("encyclopedia.search", "百科搜索"),
        ("dictionary.lookup", "词典查询"), ("grammar.check", "语法检查"), ("text.rewrite", "改写文本"),
        ("sentiment.analyze", "情感分析"), ("data.extract", "抽取数据"), ("citation.format", "格式化引用"),
        ("ocr.extract", "识别图片文字"),
    ],
}

LABELS = {
    "recipient": "收件人", "content": "内容", "subject": "主题", "title": "标题", "time": "时间",
    "date": "日期", "location": "地点", "destination": "目的地", "origin": "起点", "query": "查询",
    "name": "名称", "file": "文件", "folder": "文件夹", "url": "链接", "amount": "数量",
    "unit": "单位", "source": "来源", "target": "目标", "language": "语言", "priority": "优先级",
    "status": "状态", "assignee": "负责人", "device": "设备", "mode": "模式", "temperature": "温度",
    "duration": "时长",
}

VALUES = {
    "recipient": "张三", "content": "项目材料已经更新", "subject": "项目进度同步", "title": "周会安排",
    "time": "明天下午三点", "date": "明天", "location": "上海", "destination": "虹桥火车站",
    "origin": "公司", "query": "季度报告", "name": "李雷", "file": "方案.docx", "folder": "项目资料",
    "url": "https://example.com/api", "amount": "80", "unit": "摄氏度", "source": "中文", "target": "英文",
    "language": "英文", "priority": "高", "status": "进行中", "assignee": "王经理", "device": "客厅灯",
    "mode": "开启", "temperature": "26 度", "duration": "30 分钟",
}


def infer_arguments(code: str) -> dict[str, dict[str, object]]:
    if code in {"email.send", "email.draft"}:
        args = [("recipient", True), ("subject", False), ("content", True)]
    elif code in {"message.send", "sms.send", "slack.message", "teams.message", "customer.reply"}:
        args = [("recipient", True), ("content", True)]
    elif code in {"group.message", "broadcast.send", "social.post"}:
        args = [("title", False), ("content", True)]
    elif code in {"phone.call", "video_call.start"}:
        args = [("recipient", True)]
    elif code in {"calendar.create", "meeting.schedule", "restaurant.book", "doctor.appointment"}:
        args = [("title", True), ("date", True), ("time", False), ("location", False)]
    elif code in {"reminder.create", "notification.create"}:
        args = [("content", True), ("time", True), ("date", False)]
    elif code in {
        "file.open", "file.copy", "file.delete", "file.rename", "file.compress", "document.summarize",
        "document.translate", "document.export_pdf", "recording.transcribe", "photo.edit", "video.edit",
        "ocr.extract",
    }:
        args = [("file", True), ("content", False)]
    elif code in {
        "file.search", "email.search", "invoice.search", "note.search", "message.search", "chat.search",
        "shopping.search", "coupon.search", "event.search", "code.search", "logs.search", "encyclopedia.search",
        "dictionary.lookup", "album.search", "photo.find",
    }:
        args = [("query", True)]
    elif code in {
        "folder.create", "document.create", "spreadsheet.create", "slides.create", "form.create",
        "report.generate", "playlist.create", "issue.create", "branch.create", "release.create", "incident.create",
    }:
        args = [("title", True), ("content", False)]
    elif code in {"weather.query", "hotel.search", "flight.search", "train.search", "pharmacy.search", "parking.find", "gas_station.find"}:
        args = [("location", True), ("date", False)]
    elif code in {"navigation.start", "taxi.call"}:
        args = [("destination", True), ("origin", False)]
    elif code in {"food.order", "movie.ticket", "package.send", "laundry.pickup", "home_repair.book"}:
        args = [("query", True), ("location", False), ("time", False)]
    elif code == "delivery.track":
        args = [("query", True)]
    elif code in {"bank.transfer", "bill.pay", "expense.create"}:
        args = [("recipient", True), ("amount", True), ("content", False)]
    elif code in {"fitness.log", "water.log", "habit.track"}:
        args = [("content", True), ("amount", False), ("date", False)]
    elif code in {"music.play", "podcast.play", "video.play", "audiobook.play", "ebook.open", "radio.play", "image.generate", "subtitle.generate"}:
        args = [("query", True)]
    elif code in {"camera.open", "recording.start", "screen.record"}:
        args = [("duration", False)]
    elif code.startswith(("light.", "ac.", "curtain.", "tv.", "robot_vacuum.", "camera.", "door.", "thermostat.", "humidifier.", "purifier.")):
        if "temperature" in code or "thermostat" in code:
            args = [("device", False), ("temperature", True)]
        elif "brightness" in code:
            args = [("device", False), ("amount", True)]
        elif "channel" in code:
            args = [("device", False), ("query", True)]
        else:
            args = [("device", False)]
    elif code in {"test.run", "deploy.start", "ci.status", "pr.query", "commit.summarize", "database.query", "api.call", "container.restart", "metric.query", "dependency.check"}:
        args = [("query", True)]
    elif code in {"feature_flag.toggle", "setting.wifi.toggle", "setting.bluetooth.toggle"}:
        args = [("name", True), ("mode", True)]
    elif code == "secrets.rotate":
        args = [("name", True)]
    elif code == "translate.text":
        args = [("content", True), ("target", True)]
    elif code in {"summarize.text", "grammar.check", "text.rewrite", "sentiment.analyze", "data.extract"}:
        args = [("content", True)]
    elif code in {"calculator.compute", "unit.convert", "currency.convert"}:
        args = [("query", True)]
    elif code == "citation.format":
        args = [("content", True), ("mode", False)]
    elif code in {"clipboard.copy", "note.create", "todo.create", "todo.update", "approval.submit", "contact.create"}:
        args = [("content", True)]
    elif code in {"clipboard.read", "app.close", "window.switch", "window.screenshot", "voicemail.check"}:
        args = [("name", False)]
    elif code in {"app.open", "system.search", "contact.search", "project.status"}:
        args = [("name", True)]
    elif code in {"volume.set", "brightness.set"}:
        args = [("amount", True)]
    elif code == "password.generate":
        args = [("amount", False)]
    else:
        args = [("query", True)]
    return {name: {"type": "string", "required": required} for name, required in args}


def alias_for(name: str, code: str) -> list[str]:
    tail = code.split(".")[-1].replace("_", " ")
    compact = name.replace(" ", "")
    return list(dict.fromkeys([compact, compact.replace("创建", "新建"), tail, code]))


def arg_phrase(arguments: dict[str, dict[str, object]], include_required: bool = True, omit_first_required: bool = False) -> tuple[str, dict[str, str]]:
    parts: list[str] = []
    expected: dict[str, str] = {}
    skipped_required = False
    for key, spec in arguments.items():
        required = bool(spec.get("required"))
        if omit_first_required and required and not skipped_required:
            skipped_required = True
            continue
        if include_required or not required:
            label = LABELS.get(key, key)
            value = VALUES.get(key, f"示例{key}")
            parts.append(f"{label}：{value}")
            expected[key] = value
    return "，".join(parts), expected


def examples_for(name: str, aliases: list[str], arguments: dict[str, dict[str, object]]) -> list[str]:
    full, _ = arg_phrase(arguments)
    optional, _ = arg_phrase(arguments, include_required=False)
    optional = optional or "稍后补充"
    return [
        f"帮我{name}，{full}",
        f"{aliases[0]}一下，{full}",
        f"需要{name}，{full}",
        f"先{name}，{optional}",
        f"把{name}这件事处理掉，{full}",
    ]


def render_yaml(tools: list[dict[str, object]]) -> str:
    lines = ["tools:"]
    for tool in tools:
        lines.append(f"  - code: {json.dumps(tool['code'], ensure_ascii=False)}")
        lines.append(f"    name: {json.dumps(tool['name'], ensure_ascii=False)}")
        lines.append(f"    category: {json.dumps(tool['category'], ensure_ascii=False)}")
        lines.append(f"    description: {json.dumps(tool['description'], ensure_ascii=False)}")
        lines.append(f"    aliases: {json.dumps(tool['aliases'], ensure_ascii=False)}")
        lines.append("    examples:")
        for example in tool["examples"]:
            lines.append(f"      - {json.dumps(example, ensure_ascii=False)}")
        arguments = tool["arguments"]
        if not arguments:
            lines.append("    arguments: {}")
        else:
            lines.append("    arguments:")
            for arg, spec in arguments.items():
                lines.append(f"      {arg}:")
                lines.append(f"        type: {json.dumps(spec['type'], ensure_ascii=False)}")
                lines.append(f"        required: {str(spec['required']).lower()}")
        lines.append("")
    return "\n".join(lines)


def build_tools() -> list[dict[str, object]]:
    tools: list[dict[str, object]] = []
    for category, items in CATEGORY_TOOLS.items():
        for code, name in items:
            arguments = infer_arguments(code)
            aliases = alias_for(name, code)
            tools.append({
                "code": code,
                "name": name,
                "category": category,
                "description": f"{category}场景下的{name}工具，用于根据用户自然语言指令完成路由和参数抽取。",
                "aliases": aliases,
                "examples": examples_for(name, aliases, arguments),
                "arguments": arguments,
            })
    tools.append({
        "code": "none",
        "name": "非指令输入",
        "category": "兜底",
        "description": "闲聊、知识问答、解释说明、感谢或不需要调用工具的输入。",
        "aliases": ["闲聊", "问答", "无需工具", "none"],
        "examples": ["你是谁", "谢谢你", "解释一下余弦相似度", "为什么天空是蓝色的", "讲个笑话"],
        "arguments": {},
    })
    return tools


def build_rows(tools: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for tool in tools:
        if tool["code"] == "none":
            continue
        full, full_expected = arg_phrase(tool["arguments"])
        optional_only, optional_expected = arg_phrase(tool["arguments"], include_required=False, omit_first_required=True)
        optional_only = optional_only or "信息稍后补充"
        rows.extend([
            {"query": f"请帮我{tool['name']}，{full}", "tool_code": tool["code"], "arguments": full_expected},
            {"query": f"我想{tool['aliases'][0]}，{full}", "tool_code": tool["code"], "arguments": full_expected},
            {"query": f"处理一下{tool['name']}这个需求，{full}", "tool_code": tool["code"], "arguments": full_expected},
            {"query": f"先{tool['name']}，{optional_only}", "tool_code": tool["code"], "arguments": optional_expected},
            {"query": f"不是闲聊，帮我{tool['name']}，{full}", "tool_code": tool["code"], "arguments": full_expected},
        ])
    none_queries = [
        "你是谁", "谢谢你", "解释一下余弦相似度", "为什么天空是蓝色的", "讲个笑话", "怎么学习机器学习",
        "Apollo 这个名字有什么含义", "请说明两阶段路由的原理", "今天心情不错", "什么是向量数据库",
    ]
    while len(none_queries) < 105:
        none_queries.append(f"解释一下第 {len(none_queries) + 1} 个概念是什么")
    for query in none_queries:
        rows.append({"query": query, "tool_code": "none", "arguments": {}})
    return rows


def main() -> None:
    tools = build_tools()
    if len(tools) != 150:
        raise SystemExit(f"expected 150 tools, got {len(tools)}")
    rows = build_rows(tools)
    if len(rows) < 850:
        raise SystemExit(f"expected at least 850 rows, got {len(rows)}")

    (ROOT / "configs" / "tools.yaml").write_text(render_yaml(tools), encoding="utf-8")
    with (ROOT / "data" / "generated_queries.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"tools": len(tools), "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
