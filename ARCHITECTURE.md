# XPath智能提取工具架构图

## 项目整体架构

```mermaid
graph TB
    subgraph "用户接口层"
        CLI[命令行界面]
        Config[配置文件系统]
    end
    
    subgraph "核心处理层"
        AXPE[AsyncXPathExtractor<br/>异步提取类]
        ABXPE[AsyncBatchXPathExtractor<br/>异步批量处理类]
        CM[ConfigManager<br/>配置管理器]
    end
    
    subgraph "数据处理层"
        HTML[HTML解析器<br/>BeautifulSoup]
        LLM[LLM分析器<br/>SiliconFlow API]
        XPath[XPath验证器<br/>lxml]
        AsyncIO[异步IO<br/>aiohttp]
    end
    
    subgraph "输出层"
        CSV[CSV导出器]
        Console[控制台输出]
    end
    
    subgraph "外部服务"
        Web[网页服务]
        API[硅基流动API]
    end
    
    CLI --> AXPE
    CLI --> ABXPE
    CLI --> CM
    Config --> CM
    CM --> ABXPE
    
    AXPE --> HTML
    AXPE --> LLM
    AXPE --> XPath
    AXPE --> AsyncIO
    
    ABXPE --> AXPE
    ABXPE --> CSV
    
    HTML --> Web
    LLM --> API
    AsyncIO --> Web
    CSV --> File[文件系统]
```

## 异步批量处理流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant C as ConfigManager
    participant B as AsyncBatchXPathExtractor
    participant A as AsyncIO
    participant X as AsyncXPathExtractor
    participant W as Web服务
    participant L as LLM服务
    participant F as CSV文件
    
    U->>C: 加载配置文件
    C->>C: 验证配置
    C->>B: 初始化异步批量处理器
    
    U->>B: 启动批量处理
    B->>A: 创建异步任务池
    B->>A: 提交URL任务
    
    loop 并发处理URL
        A->>X: 处理单个URL
        X->>W: 异步获取网页内容
        W-->>X: 返回HTML
        X->>X: 清理HTML
        X->>L: 异步发送LLM分析请求
        L-->>X: 返回XPath结果
        X->>X: 验证XPath
        X-->>A: 返回处理结果
    end
    
    A->>B: 汇总所有结果
    B->>F: 写入CSV文件
    B->>U: 返回处理统计
```

## 类继承关系

```mermaid
classDiagram
    class AsyncXPathExtractor {
        -api_key: str
        -api_base: str
        -model: str
        -client: AsyncOpenAI
        -session: aiohttp.ClientSession
        +fetch_webpage(url) tuple
        +create_dom_summary(html) str
        +extract_xpath_with_llm(html, targets) dict
        +validate_xpath(html, xpath_dict) dict
        +extract_xpath(url, targets) dict
        +close() None
    }
    
    class AsyncBatchXPathExtractor {
        -max_concurrent: int
        -max_http_concurrent: int
        -max_llm_concurrent: int
        -request_timeout: int
        -retry_count: int
        -batch_size: int
        +process_batch(urls, targets) list
        +process_single_url(url, targets) dict
        +export_to_csv(results, filename) bool
        +load_urls_from_file(filename) list
        +close() None
    }
    
    class ConfigManager {
        -config_schema: dict
        +load_config(filename) dict
        +validate_config_file(filename) bool
        +normalize_config(config) dict
    }
    
    AsyncXPathExtractor <|-- AsyncBatchXPathExtractor
    AsyncBatchXPathExtractor ..> ConfigManager : 使用
```

## 数据流图

```mermaid
flowchart TD
    A[输入URL列表] --> B[配置管理器]
    B --> C{验证配置}
    C -->|失败| D[错误处理]
    C -->|成功| E[异步批量处理器]
    
    E --> F[异步任务池]
    F --> G[任务队列]
    
    G --> H[URL处理任务1]
    G --> I[URL处理任务2]
    G --> J[URL处理任务N]
    
    H --> K[异步获取网页]
    I --> K
    J --> K
    
    K --> L[HTML清理]
    L --> M[异步LLM分析]
    M --> N[XPath验证]
    N --> O[结果收集]
    
    O --> P[结果汇总]
    P --> Q[CSV导出]
    Q --> R[最终输出]
    
    style K fill:#f9f,stroke:#333,stroke-width:2px
    style M fill:#f9f,stroke:#333,stroke-width:2px
    style Q fill:#9cf,stroke:#333,stroke-width:2px
```

## 性能优化架构

```mermaid
graph LR
    subgraph "异步优化策略"
        subgraph "并发处理"
            AT[异步任务池<br/>asyncio]
            MHC[HTTP最大并发<br/>max_http_concurrent]
            MLC[LLM最大并发<br/>max_llm_concurrent]
        end
        
        subgraph "连接池"
            HCP[HTTP连接池<br/>aiohttp.ClientSession]
            CSP[连接池大小<br/>connection_pool_size]
        end
        
        subgraph "批处理"
            BS[批处理大小<br/>batch_size]
            BC[批处理控制器]
        end
        
        subgraph "错误处理"
            RT[自动重试<br/>retry_count]
            TO[超时控制<br/>timeout]
            EH[错误隔离<br/>异常捕获]
        end
    end
    
    subgraph "性能监控"
        PS[进度显示]
        TS[时间统计]
        RS[成功率统计]
    end
    
    AT --> MHC
    AT --> MLC
    HCP --> CSP
    BC --> BS
    RT --> TO
    EH --> PS
    PS --> TS
    TS --> RS
```

## 配置文件结构

```mermaid
graph TD
    A[配置文件根] --> B[settings]
    A --> C[target_elements]
    A --> D[urls_file]
    A --> E[output_format]
    
    B --> B1[max_concurrent]
    B --> B2[max_http_concurrent]
    B --> B3[max_llm_concurrent]
    B --> B4[request_timeout]
    B --> B5[llm_timeout]
    B --> B6[retry_count]
    B --> B7[output_file]
    B --> B8[model]
    B --> B9[use_async]
    B --> B10[batch_size]
    B --> B11[connection_pool_size]
    
    C --> C1[元素1]
    C --> C2[元素2]
    C --> C3[元素N]
    
    D --> D1[URL文件路径]
    
    E --> E1[include_content_preview]
    E --> E2[max_content_length]
    E --> E3[include_element_count]
    E --> E4[include_processing_time]
    
    style A fill:#9cf,stroke:#333,stroke-width:2px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#9cf,stroke:#333,stroke-width:2px
```

## 项目文件结构

```mermaid
graph TD
    A[XPathTool/] --> B[async_xpath_extractor.py]
    A --> C[async_batch_extractor.py]
    A --> D[async_main.py]
    A --> E[config_manager.py]
    A --> F[CLAUDE.md]
    A --> G[async_config.json]
    A --> H[README_async.md]
    A --> I[ARCHITECTURE.md]
    A --> J[demo.sh]
    A --> K[performance_test.py]
    A --> L[urls.txt]
    A --> M[test_urls.txt]
    
    style A fill:#9cf,stroke:#333,stroke-width:2px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#f9f,stroke:#333,stroke-width:2px
```