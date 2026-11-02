架构
    数据仓库：存储的是原始数据
    元数据库：
        mysql 数据库： 全量的元数据（表信息、字段信息、指标信息、字段指标）
        向量数据库：字段信息、指标信息
        ES：字段取值
    智能体： 
        完成自然语言转sql、并执行返回结果

元数据的数据同步：
    梳理元数据，形成配置文件
    脚本程序定义：
        根据元数据配置文件的路径解析配置文件，转换为配置文件对象
        判断配置文件对象的表信息是否存在
            _save_table_info_to_mysql
                将配置文件的表信息转换为list[TableInfoEntity],list[ColumnInfoEntity]
                分别将数据写入到mysql数据库中，判断每一个字段是否在数据库中存在，如果存在则进行修改操作，不存在则添加
                返回字段信息列表：list[ColumnInfoEntity]
            _save_column_infos_to_qdrant
                根据返回的字段信息将字段信息写入到qdrant
                    将字段信息转换为points字典对象，每一个字段有多个数据点（name,description,alias）,一个别名一个数据点
                    组装ids、embedding_text、payloads
                    批量的向量化文本embeddings
                    创建qrant集合（如果集合存在，则不创建）
                    批量的写入到qdrant
            _save_column_infos_to_es
                根据返回的字段信息将字段信息写入到es中
                    将表的配置文件的所有字段信息转换为字典，key为字段id,值为sync的值
                    循环字段列表信息，判断字段的sync是否为True
                        如果为True：查询该表的字段数据并写入到es中               
        判断配置文件对象的指标信息是否存在
            _save_metric_info_to_mysql
                将指标配置信息解析成list[MetricInfoEntity],list[ColumnMetricEntity]
                将两个列表信息写入到mysql数据库，并返回list[MetricInfoEntity]
        _save_metric_infos_to_qdrant
            将指标信息写入到向量数据库中
                    将指标信息转换为points字典对象，每一个字段有多个数据点（name,description,alias）,一个别名一个数据点
                    组装ids、embedding_text、payloads
                    批量的向量化文本embeddings
                    创建qrant集合（如果集合存在，则不创建）
                    批量的写入到qdrant

智能体创建
    定义state、runtime context 、graph
    分词节点：
        用户问题根据jieba分词设置的词性进行分词，分词的数据+用户问题写入到state   
    字段召回：
        根据用户的问题使用大模型进行扩词，将扩词的内容与分词的内容合并
        循环关键词：每一个关键词进行向量检索，存储到字典中
        将字段转换为list，返回状态
    指标召回：同上
    取值召回：同上
    合并节点：
        将字段列表转换为字典
        循环指标列表获取到每一个指标的关联字段列表
            循环关联 字段列表，如果字段不在字段字典中，则查询根据字段id查询mysql，获得字段信息，并存入到字段字典中
        循环取值列表
            判断取值的字段id是否在字段字典中，如果不在， 则查询根据字段id查询mysql，获得字段信息，并存入到字段字典中
        根据表id将字段数据进行分组
        根据表id获取表的主外键字段信息
        构建TableInfoState对象列表
        构建MetricInfoState对象列表
    字段清洗（过滤）：剔除无关的字段和表
        使用大模型进行表和字段的过滤，返回需要保留的表id和字段id
        根据大模型返回的数据，剔除table_info_state的数据
    指标过滤： 同上
    生成sql语句：
        根据用户问题、当前时间、表信息、指标信息，使用大模型生成sql语句
    执行sql语句
        从上下文获取数据仓库的数据交互层对象dw_mysql_repository
        执行查询操作，参数为生成的sql语句
        将执行的结果返回
