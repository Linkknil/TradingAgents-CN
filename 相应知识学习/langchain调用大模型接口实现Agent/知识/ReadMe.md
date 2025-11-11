#1. Langchain

  - 1.1 为什么通过调用大模型接口就能获取到数据，何必用langchain呢？

  直接调用代码

```
curl https://api.deepseek.com/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <DeepSeek API Key>" \
-d '{
      "model": "deepseek-chat",
      "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
      ],
      "stream": false
    }'
``` 

LangChain 的作用并不是简单地“帮你调 API”，而是提供了一整套“构建基于大模型应用”的工具。

```
1.统一封装多种模型和数据源

  你不必关心不同厂商 API 的细节（OpenAI、Anthropic、DeepSeek、百度文心等），只需要换一下配置，代码逻辑基本不变。
支持的接口远不止 LLM，还有向量数据库、检索系统、API、文件等。

2. 提供可复用的模块
  Prompt 模板（PromptTemplate）：可以统一管理和拼接 prompt，而不是到处写字符串。
  Memory（记忆模块）：能帮模型记住上下文对话，或者持久化存储。
  Chains：将多个调用步骤组合成流程，比如“先检索 → 再问答 → 再总结”。
  Agents：让模型像“智能体”一样，会根据任务动态决定调用哪些工具（如搜索、计算器、数据库）。

3.支持 RAG（检索增强生成）
  如果你的场景是“让大模型回答和你数据相关的问题”，你需要：
  向量化你的文档
  存入向量数据库（如 FAISS、Pinecone）
  用户提问时先检索，再把结果喂给大模型
  LangChain 提供了一套现成的组件和最佳实践，省去你自己造轮子的麻烦。

4. 提高可维护性与可扩展性
  如果你只是在玩具项目里“调 API”，当然直接调用就够了。
  但当你的应用需要：
  多个数据源
  动态调用不同模型
  上下文记忆
  更复杂的工作流（比如调用外部 API 或数据库）
  这时 LangChain 就像一个中间层，让项目结构更清晰，后期维护和扩展更容易。
  ```

# Langchain和API调用的时机

只做一次性调用/小脚本：直接 API。
要加记忆、工具、RAG、流程编排、可切换模型：LangChain 省心很多，后期维护成本低。