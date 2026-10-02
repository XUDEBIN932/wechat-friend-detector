# 微信好友变动检测示例

这是一个本地演示项目，用于比较两次微信好友导出数据，自动识别“删除好友”和“新增好友”。

说明：
- 本项目不连接微信官方 API，也不访问微信账号私密数据。
- 适合对“导出的好友列表快照”做差异比对。
- 适合学习自动化监控/日志/告警思路。

## 功能
- 比较旧快照和新快照
- 检测删除好友
- 检测新增好友
- 输出 JSON 报告
- 支持周期性监控目录中的快照文件

## 目录结构
```text
.
├── README.md
├── requirements.txt
├── friend_detector.py
├── data/
│   ├── friends_before.json
│   └── friends_after.json
└── .gitignore
```

## 安装依赖
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 使用方法

### 1) 比较两个快照
```bash
python friend_detector.py --before data/friends_before.json --after data/friends_after.json
```

### 2) 只输出 JSON 报告
```bash
python friend_detector.py --before data/friends_before.json --after data/friends_after.json --output report.json
```

### 3) 监控目录中的快照文件
```bash
python friend_detector.py --watch data --pattern "*.json" --interval 10
```

## 导出数据格式
建议将微信好友信息保存成 JSON 数组，每个对象包含以下字段中的一个或多个：

```json
[
  {
    "username": "wxid_1234567890",
    "nickname": "小明",
    "remark": "老板",
    "city": "上海"
  },
  {
    "username": "wxid_abcdef",
    "nickname": "小红",
    "remark": "同学"
  }
]
```

如果你有真实导出的 CSV / JSON 文件，也能直接适配到这个脚本里。

## 结果示例
```json
{
  "deleted": [
    {"username": "wxid_999", "nickname": "老王", "remark": "朋友"}
  ],
  "added": [
    {"username": "wxid_888", "nickname": "新朋友"}
  ],
  "unchanged_count": 120,
  "deleted_count": 1,
  "added_count": 1
}
```

## 说明
- 这个脚本不依赖微信客户端或微信后台接口。
- 它适合用于实验、学习和本地监控脚本的开发。
- 若你要做“真实生产级监控”，需要部署在你自己的数据采集和存储环境中，并遵守相关隐私和平台规则。
