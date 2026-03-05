# Moesekai 插件

AstrBot 插件，用于访问 Moesekai 相关网站并获取截图，提供个人信息查询和榜线预测功能。

## 功能特点

### 1. 个人信息查询
- 获取玩家的个人信息截图
- 支持国服（cn）和日服（jp）
- 通过 Playwright 访问 sekaiprofile 网站并截图

### 2. 榜线预测
- 获取不同区服的榜线预测截图
- 支持国服（cn）和日服（jp）
- 实现了缓存机制，减少重复请求
- 通过 Playwright 访问 sekairanking 网站并截图

## 安装说明

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
python -m playwright install
```

### 2. 配置插件

在插件配置文件中设置以下参数：

- `sekaiprofile.token`：访问 sekaiprofile 网站的令牌（个人信息功能需要）
- 其他配置项可根据需要调整

### 3. 放置插件

将 `moesekai_plugin` 文件夹复制到 AstrBot 的插件目录中。

## 使用方法

### 个人信息查询

**带空格格式：**
```
区服 个人信息
区服 grxx
区服 profile
```

**无空格格式：**
```
区服个人信息
区服grxx
区服profile
```

### 榜线预测

**带空格格式：**
```
区服 sk预测
区服 榜线预测
区服 skp
区服 prediction
区服 预测
区服 pjsk sk predict
区服 pjsk board predict
```

**无空格格式：**
```
区服sk预测
区服榜线预测
区服skp
区服prediction
区服预测
区服pjskskpredict
区服pjskboardpredict
```

### 强制刷新榜线预测

**带空格格式：**
```
区服 skp refresh
```

**无空格格式：**
```
区服skprefresh
```

## 支持的区服

- `cn`：国服
- `jp`：日服

## 技术实现

- **网页访问**：使用 Playwright 库进行网页访问和截图
- **命令处理**：通过 `SekaiCmdHandler` 类处理命令输入
- **缓存管理**：实现了截图缓存机制，减少重复请求
- **配置管理**：通过 `_conf_schema.json` 提供详细的配置选项
- **生命周期管理**：实现了初始化和终止钩子

## 注意事项

1. **首次使用**：第一次使用时，Playwright 会下载所需的浏览器，可能需要一些时间
2. **网络连接**：插件需要访问外部网站，确保网络连接正常
3. **配置验证**：确保 `sekaiprofile.token` 已正确配置，否则个人信息功能无法使用
4. **缓存机制**：榜线预测结果会缓存，默认 300 秒，可通过 `refresh` 参数强制刷新

## 常见问题

- **截图失败**：检查网络连接和 Playwright 浏览器是否正确安装
- **个人信息无法获取**：检查 `sekaiprofile.token` 是否正确配置
- **命令无响应**：检查命令格式是否正确，确保包含区服前缀

## 版本信息

- 版本：0.0.2
- 作者：xmlq (修改)
- 描述：访问 moesekai 并截图

## 插件声明

- 该插件修改自 [astrbot_plugin_moesekai](https://github.com/xuanmingLQ/astrbot_plugin_moesekai.git)
- 原作者：xuanmingLQ
- 此插件根据AI制作

## 版本更新

详细的版本更新历史请查看 [CHANGELOG.md](CHANGELOG.md) 文件。