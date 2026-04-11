---
title: 使用手册
date: 2026-04-11
---

# 股票 UP 主知识库使用手册

## 1. 安装与环境

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

确保 `.env` 中已配置 `DEEPSEEK_API_KEY`。

## 2. 初始化知识库（首次运行）

```bash
# 1. 导入所有原始素材
python tools/ingest.py --all

# 2. 全量编译（耗时较长，取决于 API 速度）
python tools/compile.py --all

# 3. 查看编译产物
ls concepts/
ls wiki/maps/
cat index.md
```

## 3. 日常使用：更新知识库

### 新增视频转录

假设新视频转录放在 `/some/path/new-video/`，包含若干 `.txt`：

```bash
python tools/ingest.py --source /some/path/new-video/
python tools/compile.py --new-only
python tools/lint.py
```

### 新增 PDF 文章

把 PDF 放到任意目录，然后：

```bash
python tools/ingest.py --articles --source /some/path/
python tools/compile.py --new-only
```

## 4. 问答使用

### 单次提问

```bash
python tools/qa.py "B2买入法的核心条件有哪些"
python tools/qa.py "这个UP主如何看半导体板块"
```

### 交互模式

```bash
python tools/qa.py --interactive
```

## 5. 输出生成

### 保存为 Markdown 文章

```bash
python tools/output.py --format md --question "少妇战法的买入逻辑"
```

结果保存在 `wiki/outputs/YYYY-MM-DD-少妇战法的买入逻辑.md`

### 生成 Marp 幻灯片

```bash
python tools/output.py --format slides --question "B2买入法实战体系"
```

在 Obsidian 中安装 Marp 插件后可直接预览为幻灯片。

### 生成主题分布图

```bash
python tools/output.py --format chart --question "topic-distribution"
```

## 6. 健康检查

每周执行一次：

```bash
python tools/lint.py
```

打开 `wiki/health-check-YYYY-MM-DD.md` 查看：
- 哪些 raw 素材还没被概念引用
- 哪些内部链接失效
- 优化建议

## 7. Obsidian 使用

1. 打开 Obsidian → "Open folder as vault" → 选择 `zgnb/` 文件夹
2. 安装插件推荐：`Marp for Obsidian`（幻灯片预览）
3. 在 Graph View 中可以看到 `concepts/` 和 `wiki/` 的双向链接网络

## 8. 内容分层策略（重要）

- **`raw/articles/`（PDF 总结）**：体系框架、概念定义的主要来源
- **`raw/videos/`（直播转录）**：案例、实时观点、市场点评的主要来源
- **`concepts/`**：LLM 自动维护的词条，通常融合了两类来源
- **`wiki/maps/`**：主题地图，帮助你快速导航到相关概念
- **`wiki/outputs/`**：你自己的问答沉淀

## 9. 故障排查

### `compile.py` 报错 "LLM call failed"
- 检查 `.env` 中 `DEEPSEEK_API_KEY` 是否正确
- 检查网络能否访问 `https://api.deepseek.com`

### `ingest.py` 没有生成 raw 文件
- 确认 `--source` 路径下有 `.txt` 或 `.pdf` 文件
- 使用 `--force` 覆盖已有文件

### `qa.py` 返回"信息不足"
- 说明该概念尚未被 `compile.py` 编译到 `concepts/` 中
- 检查 `index.md` 是否包含相关主题
- 可尝试全量重编译 `compile.py --all`
