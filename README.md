对话式数据分析系统
项目简介
对话式数据分析系统是一个基于大语言模型的智能数据分析平台，支持通过自然语言对话的方式对数据进行分析和可视化。系统采用前后端分离架构，后端使用FastAPI和LangGraph构建工作流，前端使用Vue 3和Element Plus构建用户界面。

技术栈
后端
语言：Python 3.10+
框架：FastAPI
工作流：LangGraph
ORM：SQLAlchemy
数据库：MySQL
大模型：Qwen API
前端
语言：JavaScript
框架：Vue 3
UI库：Element Plus
状态管理：Pinia
路由：Vue Router
数据可视化：ECharts
HTTP客户端：Axios
功能特性
文件上传：支持CSV和Excel文件上传
数据预览：展示上传的数据内容
对话分析：通过自然语言对话进行数据分析
数据可视化：自动生成图表展示分析结果
会话管理：保存分析会话和历史记录
数据清洗：支持对数据进行清洗操作
项目结构
PlainText



├── backend/            # 后端代码│   ├── backend/        # 主代码目录│   │   ├── app/        # 应用代码│   │   │   ├── api/    # API接口│   │   │   ├── core/   # 核心配置│   │   │   ├── models/ # 数据库模型│   │   │   ├── utils/  # 工具函数│   │   │   └── workflows/ # LangGraph工作流│   │   ├── .env        # 环境变量配置│   │   ├── main.py     # 后端入口│   │   └── requirements.txt # 依赖文件├── frontend/           # 前端代码│   ├── public/         # 静态资源│   ├── src/            # 源代码│   │   ├── api/        # API调用│   │   ├── components/ # 组件│   │   ├── router/     # 路由│   │   ├── store/      # 状态管理│   │   ├── utils/      # 工具函数│   │   ├── views/      # 页面│   │   ├── App.vue     # 根组件│   │   └── main.js     # 前端入口│   ├── package.json    # 前端依赖│   └── vue.config.js   # 前端配置└── .gitignore          # Git忽略文件
环境要求
Python：3.10+
Node.js：14.0+
MySQL：5.7+
安装和运行
后端安装和运行
进入后端目录：

Bash



运行
cd backend/backend
安装依赖：

Bash



运行
pip install -r requirements.txt
配置环境变量： 修改 .env 文件，配置数据库连接和大模型API密钥：

PlainText



# MySQL配置MYSQL_USER=rootMYSQL_PASSWORD=123456MYSQL_HOST=127.0.0.1MYSQL_PORT=3306MYSQL_DB=graduation_db# 大模型配置QWEN_API_KEY=your_api_key
启动后端服务：

Bash



运行
uvicorn main:app --reload
后端服务将在 http://localhost:8000 运行。

前端安装和运行
进入前端目录：

Bash



运行
cd frontend
安装依赖：

Bash



运行
npm install
配置前端代理： 修改 vue.config.js 文件，确保代理配置正确：

JavaScript



module.exports = {  devServer: {    port: 8080,    proxy: {      '/': {        target: 'http://localhost:8000',        changeOrigin: true,        pathRewrite: {          '^/': ''        }      }    }  }}
启动前端服务：

Bash



运行
npm run serve
前端服务将在 http://localhost:8080 运行。

核心功能
1. 文件上传
支持CSV和Excel文件上传
自动解析文件内容
生成数据预览
2. 对话分析
通过自然语言对话进行数据分析
支持复杂的分析请求
保持对话上下文
3. 数据可视化
自动生成图表展示分析结果
支持多种图表类型
交互式图表操作
4. 会话管理
保存分析会话
支持会话切换
历史会话记录
5. 数据清洗
支持对数据进行清洗操作
自动生成清洗代码
展示清洗前后的对比
API接口
后端主要接口
接口路径	方法	功能
/health	GET	健康检查
/upload	POST	文件上传
/api/v1/session/send_message	POST	发送分析请求
/api/v1/session/clean	POST	数据清洗
/api/v1/analysis-task/create-and-execute	POST	创建并执行分析任务
前端API调用
文件上传：src/api/upload.js
会话管理：src/api/session.js
部署说明
后端部署
构建生产环境：

Bash



运行
pip install gunicorngunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
配置反向代理： 使用 Nginx 或 Apache 配置反向代理，将请求转发到后端服务。

前端部署
构建生产版本：

Bash



运行
npm run build
部署静态文件： 将 dist 目录下的文件部署到 Nginx 或 Apache 服务器。

许可证
MIT License

联系方式
如有问题或建议，请联系项目维护者。

注意：本项目为毕业设计项目，仅供学习和研究使用。
