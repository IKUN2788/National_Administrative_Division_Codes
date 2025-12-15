# 🐍 Python 爬虫实战：2025年最新全国行政区划代码抓取（解决反爬与动态加载）

> **摘要**：本文详细介绍如何使用 Python 编写一个健壮的爬虫，从目标网站抓取中国最新的省、市、县三级行政区划代码。我们将重点攻克 SSL 验证错误、动态 JS 链接解析以及服务器反爬限制等技术难点，最终输出结构化的 CSV 和 JSON 数据。

---

## 📅 项目背景

在数据分析、物流配送、用户注册等场景中，一份最新、准确的**全国行政区划代码（省市区三级联动数据）**是必不可少的基础数据。虽然国家统计局每年会发布相关数据，但通过编程自动获取并整理成易用的格式（如 JSON/CSV）仍然是一个常见的技术需求。

本项目旨在解决以下核心问题：
1.  **数据完整性**：覆盖全国所有省份（包括港澳台及新疆兵团等特殊区域）。
2.  **层级关系**：精确构建 省 -> 市 -> 县/区 的树状结构。
3.  **技术攻坚**：解决目标网站的 SSL 握手失败、动态 JavaScript 链接展开以及访问频率限制问题。

---

## 🛠️ 技术栈与环境

*   **语言**：Python 3.x
*   **核心库**：
    *   `requests`：处理 HTTP/HTTPS 请求。
    *   `re`：正则表达式，用于高效解析 HTML 和 JS 代码。
    *   `csv` & `json`：数据持久化。
    *   `time` & `random`：模拟人类行为，规避反爬。

---

## 💡 核心功能实现

### 1. 健壮的网络请求层（Session & Retry）

在抓取过程中，我们遇到了 `SSL: WRONG_VERSION_NUMBER` 和服务器连接重置等问题。为了提高稳定性，我们没有直接使用 `requests.get`，而是构建了一个带有重试机制的 `Session`。

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 配置重试策略
session = requests.Session()
retries = Retry(
    total=5, 
    backoff_factor=1, 
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retries)

# 挂载适配器，同时支持 HTTP 和 HTTPS
session.mount('http://', adapter)
session.mount('https://', adapter)

# 设置通用的 Headers 和 Cookies（模拟浏览器）
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "Referer": "https://www.suchajun.com/..."
})
```

### 2. 混合解析策略（正则大法好）

目标网站的页面结构存在两种情况：
*   **标准链接**：普通的 `<a>` 标签，直接提取 `href`。
*   **JS 动态链接**：部分省份（如辽宁、甘肃）的下级城市通过 `javascript:void(0)` 触发，数据隐藏在 `data-code` 属性中。

我们需要同时处理这两种情况：

```python
# 模式1：标准链接匹配
pattern_level2_link = r'<div class="col"><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></div>\s*<div class="col">(\d+)</div>'

# 模式2：JS 动态链接匹配（关键！）
# 提取 data-code 属性，自行拼接 URL
pattern_level2_js = r'<div class="col">.*<a href="javascript:void\(0\);" class="city" data-code="(\d+)">([^<]+)</a></div>'

# 逻辑判断
if matches_level2_link:
    # 处理标准链接...
elif matches_level2_js:
    # 处理 JS 链接，手动构造 URL
    # link = f"{base_url}/richang/xingzhengquhuadaima/{code}"
```

### 3. 反反爬虫策略

为了避免被服务器识别为机器人并封禁 IP，我们采取了“慢即是快”的策略：

1.  **随机延迟**：每次请求前随机休眠 `3.0` 到 `6.0` 秒。
2.  **验证页面检测**：如果被重定向到验证码页面，脚本会检测并报警（虽然通过增加延迟已基本规避）。
3.  **数据清洗**：对提取的链接进行 `strip()` 和 `rstrip(':')` 处理，防止畸形 URL 导致请求失败。

---

## 📊 数据输出格式

脚本运行完成后，会生成两个文件：

### 1. `administrative_divisions.csv`
适合导入数据库或 Excel 分析，包含父子级联关系。

| Level | Name | Code | Link | Parent Code |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 辽宁省 | 210000 | .../210000 | |
| 2 | 沈阳市 | 210100 | .../210100 | 210000 |
| 3 | 和平区 | 210102 | .../210102 | 210100 |

### 2. `administrative_divisions.json`
树状结构，适合前端组件（如级联选择器 Cascader）直接使用。

```json
[
    {
        "name": "辽宁省",
        "code": "210000",
        "level": 1,
        "children": [
            {
                "name": "沈阳市",
                "code": "210100",
                "level": 2,
                "children": [
                    {
                        "name": "和平区",
                        "code": "210102",
                        "level": 3
                    }
                    // ... 更多区县
                ]
            }
        ]
    }
]
```

---

## 🚀 如何运行

### 第一步：安装依赖

确保目录下有 `requirements.txt` 文件，然后运行：

```bash
pip install -r requirements.txt
```

### 第二步：运行脚本

```bash
python main.py
```

*注意：由于设置了较长的随机延迟以保护账号和 IP，抓取全国完整数据可能需要 30 分钟以上。请耐心等待，或在代码中修改 `target_provinces` 列表进行局部测试。*

---

## 📝 总结

通过本次实战，我们不仅获取了有价值的数据，更重要的是实践了处理复杂网络环境和非标准 HTML 结构的技巧。特别是 **Regex 处理 JS 动态数据** 和 **Session 重试机制**，是编写高可用爬虫的必备技能。

希望这篇文章对你有所帮助！如果代码运行遇到问题，欢迎留言交流。
