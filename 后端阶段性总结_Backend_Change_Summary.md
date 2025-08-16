# 后端阶段性总结（中英双语）

---

## 一、改动原因（中文）
1. 兼容前端动态选择 X（预测因子）和 Y（响应变量），不再硬编码，支持用户自定义。
2. 增强数据安全性和健壮性，防止非法输入、路径穿越、文件不存在等问题。
3. 保持原有分析主流程和接口风格，最小化对原有代码的改动，便于维护和升级。
4. 为后续前端扩展（如下拉选择、参数传递）做好接口和参数准备。

---

## 二、主要逻辑调整（中文）
1. 参数化建模入口，支持外部传入 predictors、response_vars、group_keys，并自动过滤无效或非法列。
2. 数据校验机制，后端正则校验列名，防止非法字符和注入风险。
3. 接口兼容性，API 路由和参数格式兼容多种调用方式。
4. 异常处理与输出，错误信息标准化为 JSON，控制台输出和分析结果均保存到文件并返回。

---

## 三、思路与原则（中文）
- 以“最小改动、最大兼容”为原则，优先保证原有主流程和接口不变。
- 新功能均以可扩展方式嵌入，不影响原有分析逻辑。
- 前后端分离，接口参数和数据格式清晰，便于前端开发和后续维护。
- 所有安全相关问题均有防护，保证生产环境稳定可靠。

---

# Backend Change Summary (English)

---

## 1. Reasons for Changes
1. Support dynamic selection of X (predictors) and Y (response variables) from the frontend, no more hardcoding, user-defined modeling.
2. Enhance data safety and robustness, prevent illegal input, path traversal, and file-not-found errors.
3. Preserve original analysis workflow and API style, minimize code changes for maintainability and upgrade.
4. Prepare for future frontend expansion (dropdown selection, parameter passing) with clear API and parameter support.

---

## 2025-08-15 FastAPI Backend Update Summary

### Update Logic & Reasoning
- Problem: FastAPI app was referenced before being defined, causing 'app is not defined' error.
- Solution: Moved the app = FastAPI(...) definition and all related imports to the top of the file, ensuring all route decorators and middleware use a properly defined app instance.
- Goal: Maintain robust backend structure, support new endpoints, and ensure all API routes are registered correctly.

### Key Python Updates
1. App Definition Order:
	- Moved app = FastAPI(...) and all FastAPI imports to the top of the file.
	- Ensured all @app.post, @app.get decorators reference a valid app instance.

2. Backend Column Name Validation:
	- Added validate_column_names function using regex to allow only letters, numbers, underscores, and spaces in column names.
	- Integrated this validation in the /DOE_InputExtended endpoint for both predictors and response_vars.

3. New Endpoint /DOE_InputExtended:
	- Accepts JSON body with predictors, response_vars, file_path, and output_dir.
	- Performs backend validation and returns error if any column name is invalid.
	- Calls main analysis function and returns results or error.

4. General Refactor:
	- Preserved original workflow and file paths.
	- Improved error handling and response consistency.

### Impact
- Backend is now robust, extensible, and ready for frontend integration.
- All endpoints are registered and functional.
- Column name validation is enforced server-side for data integrity.

---

## 2025-08-15 FastAPI 后端更新摘要（中文）

### 更新思路与原因
- 问题：FastAPI 的 app 在定义前被引用，导致 'app is not defined' 错误。
- 解决：将 app = FastAPI(...) 及相关 import 移到文件顶部，确保所有路由和中间件都引用已定义的 app 实例。
- 目标：保持后端结构健壮，支持新接口，确保所有 API 路由正确注册。

### 主要 Python 变更
1. app 定义顺序：
	- app = FastAPI(...) 及相关 import 移到文件顶部。
	- 所有 @app.post, @app.get 装饰器均引用有效 app 实例。

2. 后端列名校验：
	- 新增 validate_column_names 函数，正则只允许字母、数字、下划线和空格。
	- 在 /DOE_InputExtended 接口对 predictors 和 response_vars 均做校验。

3. 新接口 /DOE_InputExtended：
	- 支持 JSON body 传 predictors、response_vars、file_path、output_dir。
	- 后端校验列名，发现非法列名直接返回错误。
	- 调用主分析函数并返回结果或错误。

4. 通用重构：
	- 保持原有主流程和文件路径。
	- 错误处理和响应更规范。

### 影响
- 后端更健壮、可扩展，支持前端集成。
- 所有接口均已注册并可用。
- 列名校验在服务端强制执行，保证数据安全。

---

## 2. Main Logic Adjustments
1. Parameterized modeling entry, allowing external predictors, response_vars, group_keys, and auto-filtering invalid/illegal columns.
2. Data validation: backend regex checks column names, prevents illegal characters and injection risks.
3. API compatibility: routes and parameter formats support multiple invocation methods.
4. Exception handling and output: errors standardized as JSON, console output and results saved to files and returned.

---

## 3. Principles and Approach
- "Minimal change, maximal compatibility" principle, original workflow and API unchanged as much as possible.
- All new features are extensible and do not affect original analysis logic.
- Clear separation of frontend and backend, with well-defined API parameters and data formats for easy frontend development and future maintenance.
- All security-related issues (path, filename, data format) are protected for stable production use.

---

If you need detailed code change points or further extension suggestions, feel free to request.
