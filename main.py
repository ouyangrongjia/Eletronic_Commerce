import os
import jieba

# 定义停用词
stop_words = set()
with open('./datas/StopWords/baidu_stopwords.txt', 'r', encoding='utf-8') as file:
    for line in file:
        stop_words.add(line.strip())


# 读取日志，提取搜索记录
def log_to_file(origin_file_path, process_file_path):
    file_list = os.listdir(origin_file_path)
    print(file_list)
    data_after_process = open(process_file_path, 'w', encoding="utf-8")
    for file in file_list:
        datas_file_origin = open((origin_file_path + '/' + file), encoding="ANSI", errors='ignore')
        data_origin_lines = datas_file_origin.readlines()
        for data_origin_line in data_origin_lines:
            data_sig = data_origin_line.split()
            count = 0
            for items in data_sig:
                # 排除用户ID等无关信息
                if count > 3:
                    data_after_process.write(items)
                    data_after_process.write('\n')
                count += 1
            count = 0
            # data_to_write = data_origin_line.split('\t')[1]
            # data_to_write_new = data_to_write.replace('[', '').replace(']', '')
            # data_after_process.write(data_to_write_new)
            # data_after_process.write('\n')
    print("Data process finish")


# compKey算法
# 1.遍历所有搜索记录，提取出与种子关键词相关的中介关键词
# 2.计算出所有包含s与sa的查询搜索量。
# 3.确定不同时与s出现，但与某一个中间关键词同时出现的竞争性关键词kM，然后计算每个竞争关键词的竞争度
# 4.将结果写入文本文件中

# 统计与种子关键字相关的搜索记录
# 传入：种子关键词
def record_search_log(seed_word):
    processed_data = open('./datas/ProcessedData/ProcessedData.txt', 'r', encoding="utf-8")
    data_relate = './datas/SeedWordSearchLog/' + seed_word + ".txt"

    # 创建写入文件，将与种子关键字相关的内容写入文件中
    f_relate = open(data_relate, 'w', encoding='utf-8')
    # 判断是否不包含种子关键字
    is_contain = False
    # 判断是否包含种子关键字
    for line in processed_data:
        # 逐行读入将，去掉换行
        value_line = line
        value_line.replace("\t", "")
        value_line.replace("\n", "")
        # 逐条匹配，如果找到了字符串则为成功
        if seed_word in value_line:
            is_contain = True
            # 写入文件
            f_relate.write(value_line)
    if not is_contain:
        print("搜索的数据中不包含该种子关键字", seed_word, "请重新输入")
        return False
    else:
        print(seed_word, '相关搜索记录提取完毕')
        return True


# 统计词频
# 传入：关键词的搜索记录文本路径、分词后的存储路径、词频排序后的存储路径
def statistic(word_searching_log, word_apart_file, word_statistics):
    with open(word_searching_log, encoding="utf-8") as word_input_file:
        text = word_input_file.read()
    # 分词
    word_apart_outcome = [word for word in jieba.cut(text) if word not in stop_words]
    # word_apart_outcome = ltp.pipeline(text, tasks=["cws"], return_dict=False)[0]
    result = open(word_apart_file, 'w', encoding="utf-8")
    result.write(' '.join(word_apart_outcome))
    print('写入分词结果', word_apart_file, '成功')

    # 统计词频
    counts = {}
    for word in word_apart_outcome:
        if len(word) > 1 and word != '\n' and word != '\t':
            counts[word] = counts.get(word, 0) + 1

    # 词频排序统计
    ls_sorted = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    with open(word_statistics, 'w', encoding="utf-8") as statistic_result:
        statistic_result.write('\n'.join('%s %s' % x for x in ls_sorted))
    print('写入词频排序', word_statistics, '成功')

    # 关闭文件流
    word_input_file.close()
    result.close()
    statistic_result.close()


# 查找中介关键字
# 传入:种子关键字、中介关键字的存储路径
def findMidWords(seed_word, word_mid):
    mid_keywords = []
    # 打开词频排序文件
    statisticsFile = open('./datas/WordStatistics/' + seed_word + '_statistics.txt', 'r', encoding='utf-8')
    # 打开中介关键字文件
    mid_file = open(word_mid, 'w', encoding='utf-8')
    for line in statisticsFile:
        # 词频文件中数据以 词汇 词频 出现，以“”分割并获取词汇
        line_mid_word = line.split(" ")[0]
        first = line_mid_word[0]
        # 过滤掉仅有一个字和以数字作为开头的中介关键字
        if (len(line_mid_word) <= 1) or ('0' <= first <= '9'):
            continue
        # 中介关键字不能包含或者被包含在种子关键字
        if (not (seed_word in line_mid_word)) and (not (line_mid_word in seed_word)):
            # 将中介关键字保存到list中
            mid_keywords.append(line_mid_word)
            # 写入文件中
            mid_file.write(line_mid_word)
            mid_file.write('\n')
        # 找够了就break
        if len(mid_keywords) >= 10:
            print('种子关键字 ', seed_word, '的中介关键字统计完毕')
            break
    # 关闭文件流
    statisticsFile.close()
    mid_file.close()


# 查找竞争关键字
# 传入:种子关键字、竞争关键字存储路径
def findCompWords(seed_word, word_comp):
    mid_word_file = open('./datas/MidWord/' + seed_word + '_midWord.txt', 'r', encoding='utf-8')
    processed_data_file = open('./datas/ProcessedData/ProcessedData.txt', 'r', encoding='utf-8')
    word_comp_file = open(word_comp, 'w', encoding='utf-8')
    mid_word_array = []
    comp_word = {}
    for line_in_mid in mid_word_file:
        mid_word = line_in_mid.split('\n')[0]
        if len(mid_word) <= 1:
            continue
        mid_word_array.append(mid_word)
        for line_in_process in processed_data_file:
            # 对于每条包含中介关键词但不包含种子关键词的记录
            if (mid_word in line_in_process) and (not (seed_word in line_in_process)):
                # 对该记录进行分词
                line_apart = [word for word in jieba.cut(line_in_process) if word not in stop_words]
                for word in line_apart:
                    # 对于每个非中介关键词的分词
                    if (not (word in mid_word)) and (not (mid_word in word)) and (
                            not (seed_word in word) and (not (word in seed_word))):
                        # 记录潜在的竞争关键词
                        if len(word) > 1 and word != '\n' and word != '\t':
                            comp_word[word] = comp_word.get(word, 0) + 1
    # 对竞争关键词集合进行排序，筛选出前十个作为竞争关键词
    comp_sorted = sorted(comp_word.items(), key=lambda x: x[1], reverse=True)
    count = 0
    for comp_item in comp_sorted:
        isSame = False
        for array_item in mid_word_array:
            if comp_item[0] == array_item:
                print(comp_item[0], '和中介关键词冲突')
                isSame = True
        if not isSame:
            word_comp_file.write(comp_item[0])
            word_comp_file.write('\n')
            count += 1
        if count >= 10:
            break
    print(seed_word, '的竞争关键词筛选完毕')
    # 关闭文件流
    mid_word_file.close()
    processed_data_file.close()
    word_comp_file.close()


# 计算竞争度
# 传入:种子关键字、竞争度结果存储路径
def calculateComp(seed_word, comp_result):
    # 竞争性关键字
    k_log = open('./datas/CompWord/' + seed_word + '_compWord.txt', 'r', encoding='utf-8').readlines()
    # 中间关键字
    a_log = open('./datas/MidWord/' + seed_word + '_midWord.txt', 'r', encoding='utf-8').readlines()
    # 种子关键字搜索记录
    seed_search_log = open('./datas/SeedWordSearchLog/' + seed_word + '.txt', 'r', encoding='utf-8').readlines()
    # 种子关键词搜索记录条数
    s = len(seed_search_log) - 1
    # 整体搜索记录
    processed_search_log = open('./datas/ProcessedData/ProcessedData.txt', 'r', encoding='utf-8').readlines()
    # 竞争度结果存储路径
    comp_result_file = open(comp_result, 'w', encoding='utf-8')
    # 竞争度集合
    comp_rank = {}

    # 对于每一个竞争关键词,计算竞争度
    for k_line in k_log:
        k_word = k_line.split('\n')[0]
        if len(k_word) <= 1: continue
        comp_k = 0
        # 对于每一个中介关键字
        for a_line in a_log:
            a_word = a_line.split('\n')[0]
            if len(a_word) <= 1: continue
            ka = 0
            a = 0
            sa = 0
            # 对于每一条搜索记录，统计a,sa,ka
            for search_line in processed_search_log:
                if a_word in search_line:
                    a = a + 1
                if (a_word in search_line) and (seed_word in search_line):
                    sa = sa + 1
                if (a_word in search_line) and (k_word in search_line):
                    ka = ka + 1
            # compKey算法
            wak = sa / s
            comp_k += wak * (ka / (a - sa))
        print('种子关键词', seed_word, '的竞争性关键词', k_word, ' 的竞争度为', comp_k)
        comp_rank[k_word] = comp_k
    # 竞争度排序
    comp_ranked = sorted(comp_rank.items(), key=lambda x: x[1], reverse=True)
    for item in comp_ranked:
        comp_result_file.write((str(item[0]) + ' comp:' + str(item[1])))
        comp_result_file.write('\n')
    print(seed_word, '竞争性关键词comp测度计算完毕')
    return comp_ranked


# 总控函数
# 传入：种子关键词
def forCompKey(seed_word):
    # 统计搜索记录
    seedWord = seed_word
    if record_search_log(seed_word=seedWord):
        # 根据统计的搜索记录进行分词、词频统计
        wordSearchLog = './datas/SeedWordSearchLog/' + seedWord + '.txt'
        wordApartFile = './datas/WordApartFile/' + seedWord + '_apart.txt'
        wordStatistics = './datas/WordStatistics/' + seedWord + '_statistics.txt'
        statistic(word_searching_log=wordSearchLog, word_apart_file=wordApartFile, word_statistics=wordStatistics)
        midWord = './datas/MidWord/' + seedWord + '_midWord.txt'
        findMidWords(seed_word=seedWord, word_mid=midWord)
        compWord = './datas/CompWord/' + seedWord + '_compWord.txt'
        findCompWords(seed_word=seedWord, word_comp=compWord)
        compResult = './datas/Result/' + seedWord + '_result.txt'
        calculateComp(seed_word=seedWord, comp_result=compResult)
    else:
        print('传入的关键词', seedWord, '无搜索记录')


# 读取日志并提取搜索记录处理数据
# log_to_file('./datas/Sogou', './datas/ProcessedData/ProcessedData.txt')

# seed_word_array = ['英雄', '王者荣耀', '微信', 'qq', '阴阳师', '湖南', '陕西', '白金', '公务员', '篮球']
# for items in seed_word_array:
#     forCompKey(items)
