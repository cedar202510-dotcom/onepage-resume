# onepage-resume

把用户提供的简历素材整理为"一页可投递简历"，并输出可编辑 HTML（可进一步导出 PDF）。

## 特性

- **事实不失真**：时间、公司、数字、头衔不乱改
- **一页可投递**：自动调整密度，确保单页输出
- **三套风格**：`stripe`（条带标题）/ `compact`（高密度极简）/ `sidebar`（左右分栏）
- **交互确认**：可选模块（荣誉、课程、附加信息等）先确认再生成
- **在线编辑**：生成的 HTML 支持实时编辑、拖拽排序、主题换色、上传头像
- **一键导出 PDF**：浏览器打印即得，无需额外工具

## 适用场景

- 已有长简历，想压缩成一页投递版
- 只有零散经历，想快速整理成标准结构
- 需要多套样式对比后再定稿

## 你需要准备什么

1. 简历文字内容（可直接粘贴文本、Markdown、混合中英文）
2. 可选头像（图片 URL 或本地路径，也可生成后上传）
3. 想要的风格（`stripe` / `compact` / `sidebar`）
4. 强调色（Hex，如 `#1f4e8c`）

## 风格预览

直接在浏览器打开 `style-gallery.html` 即可对比三种风格。

## 使用流程

1. 上传或粘贴简历素材
2. 查看风格预览并选择样式
3. 系统抽取并整理结构化信息
4. 确认可选项（课程、荣誉、奖项、附加信息等）
5. 生成一页 HTML
6. 浏览器打印为 PDF

## 渲染命令

```bash
python3 scripts/render_onepage_resume.py \
  --input resume.json \
  --output resume.html \
  --style stripe \
  --accent "#1f4e8c"
```

`sidebar` 风格示例：

```bash
python3 scripts/render_onepage_resume.py \
  --input resume.json \
  --output resume.html \
  --style sidebar \
  --accent "#1f4e8c"
```

## 导出 PDF

- 用浏览器打开 `resume.html`
- 打印 → 另存为 PDF
- 勾选"背景图形"
- 页边距建议 8mm–12mm
- 确认单页输出

## 目录说明

| 文件/目录 | 说明 |
|---|---|
| `SKILL.md` | 技能工作流定义（技能市场入口） |
| `scripts/` | 渲染脚本 |
| `references/` | 抽取规则、排版规则、确认清单 |
| `assets/` | 示例 JSON 数据 |
| `agents/` | Agent 配置 |
| `style-gallery.html` | 风格预览页 |

## 事实与质量原则

- 不编造经历和数据
- 不随意改写时间、公司、学校、岗位
- 信息过长时优先"压缩表达"，不是"删关键事实"
- 可选模块会先询问是否保留
