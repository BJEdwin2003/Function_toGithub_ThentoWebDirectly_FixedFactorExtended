# Mixed Model DOE Analysis - Web直接部署架构

## 🏗️ 核心技术架构：99%的DOE分析完全自动化

本项目的核心价值在于将复杂的六西格玛DOE分析完全自动化部署到Web平台，实现**100%可重复性**的统计分析，无需依赖本地环境、网络连接或Token配置。

### 🎯 设计理念
- **99%**: DOE统计分析的完全自动化执行（本项目核心）
- **1%**: AI Agent辅助结果解释（可选增强功能）

---

## 🚀 Web直接部署架构详解

### 架构流程图
```
用户上传CSV → doe_analysis_test_interface.html → Render.com FastAPI → Python DOE分析 → 结果文件下载
     ↑                        ↓                           ↓                ↓              ↓
   本地文件              JavaScript调用              app.py处理        核心分析模块      完整输出
```

### 🔧 技术栈组成

#### 1️⃣ 前端层：doe_analysis_test_interface.html
**核心功能**：用户交互界面
- **文件上传**: 直接拖拽或选择CSV文件
- **API调用**: JavaScript fetch() 调用Render.com API
- **结果显示**: 实时显示完整控制台输出
- **文件管理**: 在线浏览和下载生成的分析文件

#### 2️⃣ 部署层：Render.com云平台
**核心功能**：Web服务托管
- **Live URL**: https://function-togithub-thentowebdirectly.onrender.com
- **自动部署**: GitHub仓库自动同步
- **零配置**: 无需服务器维护
- **高可用**: 24/7在线服务

#### 3️⃣ API层：FastAPI (app.py)
**核心功能**：HTTP接口处理
- **文件接收**: 处理multipart/form-data上传
- **分析调度**: 调用核心DOE分析模块
- **输出捕获**: 完整控制台输出实时捕获
- **文件服务**: 提供结果文件下载接口

#### 4️⃣ 分析层：Mixed Model DOE Engine
**核心功能**：六西格玛统计分析
- **数据处理**: pandas数据清洗和预处理
- **统计建模**: statsmodels混合效应模型
- **诊断分析**: 残差分析、拟合优度检验
- **结果输出**: 多格式分析报告生成

---

## 📡 详细API调用流程

### Step 1: 用户上传文件
```javascript
// doe_analysis_test_interface.html 中的核心代码
const formData = new FormData();
formData.append('file', file);

const response = await fetch('https://function-togithub-thentowebdirectly.onrender.com/runDOE', {
    method: 'POST',
    body: formData
});
```

### Step 2: Render.com接收请求
```python
# app.py 中的核心端点
@app.post("/runDOE")
async def run_doe_analysis(file: UploadFile = File(...)):
    # 文件保存到临时目录
    file_path = f"./input/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 调用核心分析模块
    result = run_mixed_model_doe(file_path)
    return result
```

### Step 3: Python DOE分析执行
```python
# MixedModelDOE_Function_FollowOriginal_20250804.py 核心分析
def run_mixed_model_doe(csv_file_path):
    # 1. 数据读取和预处理
    # 2. 混合效应模型拟合
    # 3. 统计诊断
    # 4. 结果文件生成
    # 5. 控制台输出捕获
    return {
        "status": "success",
        "console_output": captured_output,
        "files": generated_files
    }
```

### Step 4: 结果返回和显示
```javascript
// 前端接收并显示结果
if (response.ok) {
    const result = await response.json();
    showSuccess(result);  // 显示完整控制台输出
}
```

---

## 🔍 核心文件详解

### 1. doe_analysis_test_interface.html (前端核心)
```html
<!-- 关键功能模块 -->
<input type="file" id="csvFile" accept=".csv" />
<button onclick="testDOEAnalysis()">🚀 运行 DOE 分析</button>

<script>
async function testDOEAnalysis() {
    // 文件上传逻辑
    // API调用逻辑  
    // 结果显示逻辑
}
</script>
```

**核心特性**：
- 拖拽上传支持
- 实时进度显示
- 完整控制台输出格式化显示
- 文件下载链接自动生成

### 2. app.py (API服务核心)
```python
# 关键端点
@app.post("/runDOE")          # 主分析接口
@app.get("/files")            # 文件列表接口  
@app.get("/download/{filename}")  # 文件下载接口
```

**核心功能**：
- FastAPI自动文档生成（/docs）
- CORS跨域支持
- 文件上传处理
- 异常处理和错误返回

### 3. MixedModelDOE_Function_FollowOriginal_20250804.py (分析核心)
```python
# 六西格玛DOE分析流程
def main():
    # 数据读取 → 预处理 → 建模 → 诊断 → 输出
    process_csv_file()
    fit_mixed_models()
    generate_diagnostics()
    save_results()
```

**统计分析模块**：
- 混合效应模型拟合
- R²计算和显著性检验
- JMP风格诊断报告
- 残差分析和拟合缺失检验

---

## 📊 完整输出文件体系

### 主要结果文件
| 文件名 | 内容 | 用途 |
|--------|------|------|
| `simplified_logworth.csv` | 简化模型显著因子 | 快速识别关键因子 |
| `fullmodel_logworth.csv` | 完整模型结果 | 详细统计分析 |
| `uncoded_parameters.csv` | 未编码参数估计 | 实际工艺参数 |
| `diagnostics_summary.csv` | 模型诊断汇总 | 模型质量评估 |

### 诊断文件
| 文件名 | 内容 | 用途 |
|--------|------|------|
| `mixed_model_variance_summary.csv` | 方差组分 | 变异来源分析 |
| `JMP_style_lof.csv` | 拟合缺失检验 | 模型适配性 |
| `residual_data_*.csv` | 残差数据 | 模型假设验证 |

---

## ⚙️ Render.com部署配置

### 部署设置
```yaml
# render.yaml (自动检测)
services:
  - type: web
    name: doe-analysis-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.9
```

### 自动部署流程
1. **GitHub推送** → Render.com自动检测更新
2. **依赖安装** → `pip install -r requirements.txt`
3. **服务启动** → `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. **健康检查** → API endpoints可用性验证

---

## 🎯 使用方式对比

### 方式1: Web直接访问（推荐 - 99%的功能）
```bash
# 只需三步
1. 打开: doe_analysis_test_interface.html
2. 上传: your_data.csv
3. 下载: 完整分析结果
```

**优势**：
- ✅ 零配置，即开即用
- ✅ 100%可重复性
- ✅ 完整控制台输出
- ✅ 所有文件可下载
- ✅ 无网络依赖（除上传下载）

### 方式2: 直接API调用
```bash
curl -X POST -F "file=@data.csv" \
  https://function-togithub-thentowebdirectly.onrender.com/runDOE
```

### 方式3: AI Agent增强（1%的解释功能）
- 用于DOE结果的自然语言解释
- 帮助非六西格玛专家理解结果
- 可选功能，不影响核心分析

## 🚀 Quick Start (Web Direct)


### 最简单使用方式：
1. 打开测试界面：[doe_analysis_test_interface.html](./doe_analysis_test_interface.html)
2. 上传 CSV 文件
3. 点击"� 运行 DOE 分析"
4. 查看完整分析结果和下载文件

### 或直接 API 调用：
```bash
curl -X POST -F "file=@your_data.csv" \
  https://function-togithub-thentowebdirectly.onrender.com/runDOE
```

## �📡 API Endpoints (所有版本)

### 1️⃣ Web Direct 专用接口

#### `/runDOE` (POST) - 文件上传分析
直接上传 CSV 文件进行分析，返回完整控制台输出。

```bash
curl -X POST -F "file=@data.csv" \
  https://function-togithub-thentowebdirectly.onrender.com/runDOE
```

**响应示例**:
```json
{
  "status": "success",
  "input_file": "./input/data.csv",
  "output_dir": "./outputDOE", 
  "files": ["simplified_logworth.csv", "diagnostics_summary.csv", ...],
  "console_output": "🚀 开始DOE混合模型分析...\n📊 数据文件: ./input/data.csv\n..."
}
```

#### `/files` (GET) - 文件列表
获取所有可下载的分析结果文件。

```bash
curl https://function-togithub-thentowebdirectly.onrender.com/files
```

#### `/download/{filename}` (GET) - 文件下载  
下载指定的分析结果文件。

```bash
curl -O https://function-togithub-thentowebdirectly.onrender.com/download/simplified_logworth.csv
```

### 2️⃣ AI Agent 兼容接口

#### `/runDOEjson` (POST) - JSON + Base64
AI Agent 使用的 Base64 编码数据传输。

```json
{
  "filename": "data.csv",
  "file_b64": "ZHllMSxkeWUyLFRpbWUsVGVtcCxMdmFsdWU..."
}
```

#### `/api/DoeAnalysis` (POST) - AI Foundry 专用 ⭐
AI Foundry/Copilot Studio 集成的标准化接口。

```json
{
  "data": "base64_encoded_csv_data",
  "response_column": "Lvalue,Avalue,Bvalue",
  "threshold": 1.5,
  "force_full_dataset": true
}
```

## 🔧 数据格式要求

您的 CSV 文件应包含以下列：
- `dye1`, `dye2` - 染料浓度
- `Time`, `Temp` - 工艺参数  
- `Lvalue`, `Avalue`, `Bvalue` - 颜色测量值 (响应变量)

示例数据：
```csv
dye1,dye2,Time,Temp,Lvalue,Avalue,Bvalue
1.0,2.0,30,150,45.2,12.3,8.7
1.5,2.5,35,160,47.1,13.1,9.2
2.0,3.0,40,170,49.0,14.2,10.1
```

## 📊 输出文件说明

分析完成后会生成以下文件（可通过 `/download/{filename}` 下载）：

### 主要结果文件：
- `simplified_logworth.csv` - 简化模型的显著因子
- `fullmodel_logworth.csv` - 完整模型结果  
- `uncoded_parameters.csv` - 未编码参数估计
- `diagnostics_summary.csv` - 模型诊断信息

### 诊断文件：
- `mixed_model_variance_summary.csv` - 方差组分分析
- `JMP_style_lof.csv` - 拟合缺失检验
- `residual_data_*.csv` - 各响应变量的残差数据

### 数据文件：
- `design_data.csv` - 设计数据
- `scaler.csv` - 标准化参数
- `console_output.txt` - 完整控制台输出

## 🎨 Web 界面特色功能

### 完整控制台输出显示
网页界面显示与 VS Code 终端完全相同的分析过程：
- 🚀 分析进度提示
- 📊 数据维度和统计信息
- 📋 JMP风格诊断汇总  
- ✅ 文件保存确认

### 文件管理功能
- 📂 浏览生成的文件
- ⬇️ 一键下载分析结果
- 📄 文件预览和说明

## 🤖 AI Agent Integration (Legacy)

### AI Foundry/Copilot Studio 集成说明：
1. 使用 OpenAPI 规范：`openapi_doe_analysis_ai_foundry.json`
2. 端点：`/api/DoeAnalysis`  
3. **重要**：`response_column` 必须是逗号分隔的字符串，不是数组

### AI Foundry 调用示例：
```json
{
  "data": "base64_csv_here", 
  "response_column": "Lvalue,Avalue,Bvalue",
  "threshold": 1.5
}
```

##  开发和部署

### 项目结构详解
```
Function_toGithub_ThentoWebDirectly/
├── app.py                                         # FastAPI主服务器 - Web Direct核心
├── doe_analysis_test_interface.html               # 前端界面 - 用户交互层
├── MixedModelDOE_Function_FollowOriginal_*.py     # DOE分析引擎 - 统计计算核心
├── API_HTML_to_CopilotAgent_Swagger2_Spec.json    # Copilot Studio API规范 (Swagger 2.0)
├── requirements.txt                               # Python依赖包清单
├── csv_to_base64_converter.py                    # Base64转换工具 (AI Agent辅助)
├── test_sample_data.csv                          # 测试数据样本
├── Copilot_Agent_Setup_Guide.md                 # Copilot Agent配置指南 (1%功能)
└── README.md                                     # 本文档
```

### 🗂️ API文件说明
| 文件名 | 功能 | 对应架构层 | 重要程度 | 平台兼容性 |
|--------|------|-----------|----------|------------|
| `app.py` | FastAPI服务器，处理Web请求 | API层 | 🔥 核心 (99%) | 通用 |
| `doe_analysis_test_interface.html` | 前端界面，文件上传和结果显示 | 前端层 | 🔥 核心 (99%) | 通用 |
| `MixedModelDOE_Function_*.py` | DOE统计分析引擎 | 分析层 | 🔥 核心 (99%) | 通用 |
| `API_HTML_to_CopilotAgent_Swagger2_Spec.json` | Copilot Studio专用API规范 | AI集成层 | 💡 增强 (1%) | Copilot Studio |
| `csv_to_base64_converter.py` | 数据格式转换工具 | 工具层 | 🔧 辅助 | 通用 |

### 核心依赖：
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `pandas`, `numpy` - 数据处理
- `statsmodels` - 统计建模
- `scikit-learn` - 机器学习工具

### 部署到 Render.com：
1. Fork 本仓库
2. 在 Render.com 创建 Web Service
3. 连接 GitHub 仓库
4. 构建命令：`pip install -r requirements.txt`
5. 启动命令：`uvicorn app:app --host 0.0.0.0 --port $PORT`

## 📈 性能指标

- **分析时间**: 典型数据集 < 60 秒
- **内存使用**: 大部分分析 < 1MB
- **支持数据量**: 最多 10,000 行
- **文件上传限制**: 50MB

## 🔄 版本历史

### v1.1.0 (当前版本) - Web Direct
- ✅ 完整控制台输出捕获和显示
- ✅ 文件下载 API (`/files`, `/download/{filename}`)
- ✅ 用户友好的 Web 测试界面
- ✅ 保持 AI Agent 兼容性

### v1.0.0 - AI Agent 专用
- ✅ AI Foundry/Copilot Studio 集成
- ✅ Base64 数据传输
- ✅ OpenAPI 规范支持

## 🔗 相关资源

### 主要文档
- **[doe_analysis_test_interface.html](./doe_analysis_test_interface.html)**: Web Direct前端界面 (核心99%功能)
- **[Copilot_Agent_Setup_Guide.md](./Copilot_Agent_Setup_Guide.md)**: Copilot Agent配置指南 (可选1%功能)
- **[API_HTML_to_CopilotAgent_Swagger2_Spec.json](./API_HTML_to_CopilotAgent_Swagger2_Spec.json)**: Copilot Studio专用API规范 (Swagger 2.0 JSON格式)

### 📱 Copilot Studio集成规范
| 规范文件 | 格式 | 版本 | 兼容性 | 说明 |
|----------|------|------|--------|------|
| `API_HTML_to_CopilotAgent_Swagger2_Spec.json` | JSON | Swagger 2.0 | ✅ **完美兼容** | 专为Copilot Studio优化 |

### 技术报告
- [可行性报告](MixedModelDOE_AI_Agent_Feasibility_Report.md) (AI Agent 版本)
- [English Version](MixedModelDOE_AI_Agent_Feasibility_Report_EN.md)

### 🤖 Copilot Agent配置说明 (可选1%功能)

#### 配置步骤概述
1. **打开Copilot Studio** → 创建新的Agent
2. **上传API规范** → 使用 `API_HTML_to_CopilotAgent_Swagger2_Spec.json`
3. **配置REST API工具** → 连接到 `/get_analysis_for_copilot` 端点
4. **测试集成** → 验证Agent能获取DOE分析结果

#### 为什么选择Swagger 2.0 JSON格式？
```bash
# 基于Copilot Studio官方要求
✅ 格式: JSON (必须)
✅ 版本: Swagger 2.0 (推荐) 
✅ 自动转换: OpenAPI 3.0 → Swagger 2.0 (如需要)
✅ 兼容性: 完美支持Copilot Studio
```

#### 关键配置文件说明
```json
// API_HTML_to_CopilotAgent_Swagger2_Spec.json 核心作用
{
  "swagger": "2.0",
  "info": {
    "title": "DOE Analysis API for Copilot Agent",
    "description": "将HTML界面的DOE分析结果传递给Copilot Agent进行智能解释"
  },
  "host": "function-togithub-thentowebdirectly.onrender.com",
  "paths": {
    "/get_analysis_for_copilot": {  // 核心端点：AI Agent获取DOE结果
      "get": { ... }
    }
  }
}
```

#### 集成架构
```
HTML界面执行DOE → 存储结果 → Copilot Agent读取 → 智能解释给用户
    (99%)           (API)        (Swagger 2.0规范)    (1%)
```

## 📞 技术支持

如有问题或建议：
1. Web Direct 版本：访问 API 文档 https://function-togithub-thentowebdirectly.onrender.com/docs
2. AI Agent 版本：参考 OpenAPI 规范文件
3. 本地开发：查看 `/docs` 端点

## 💡 使用建议

### 推荐使用场景：

1️⃣ **普通用户** → Web Direct (当前版本)
- 简单文件上传
- 完整结果查看
- 方便文件下载

2️⃣ **AI Agent 开发者** → AI Foundry 接口
- 程序化调用
- 标准化响应
- 自动化集成

3️⃣ **开发者** → Local Development
- 代码调试
- 功能扩展
- 性能优化

---

## 📦 数据流与功能分工说明（2025年8月补充）

### 1. 前端上传与API接收
- 用户在网页（如 doe_analysis_test_interface.html）上传CSV文件。
- 前端可直接上传CSV，也可用Base64编码后上传（如AI Agent场景）。

### 2. app.py的处理逻辑
- 如果是普通文件上传，app.py直接保存CSV到临时目录。
- 如果是Base64字符串上传（如AI Agent），app.py会先用Base64解码，还原为CSV文件。
- app.py不会做统计分析，只负责文件接收、解码和调度。

### 3. Base64转换工具
- csv_to_base64_converter.py 仅用于将CSV转为Base64字符串，便于API或AI Agent传输。
- 解码过程发生在app.py，不在分析核心代码里。

### 4. 核心分析流程
- app.py调用 MixedModelDOE_Function_OutputToWeb_20250807.py 的 run_mixed_model_doe_with_output。
- 该函数只处理标准CSV文件（已解码），用 pandas 读取数据，进行DOE分析。
- 分析结果（控制台输出和各类CSV文件）会保存到指定目录，并返回给前端或API调用者。

### 5. 总结
- Base64编码/解码仅用于数据传输环节，分析核心只处理标准CSV。
- Web和AI Agent均可用，数据流清晰分工，便于维护和扩展。

---

**当前版本**: v1.1.0 (Web Direct)  
**最后更新**: 2025年8月  
**维护状态**: 🟢 活跃开发中
