import ctypes
import os
import jieba
import multiprocessing
import time
import matplotlib.pyplot as plt


# 读取日志，提取搜索记录
def log_to_file(origin_file_path, process_file_path):
    file_list = os.listdir(origin_file_path)
    print(file_list)
    data_after_process = open(process_file_path, 'w', encoding="utf-8")
    dataCount = 0  # 统计数据量
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
                    dataCount = dataCount + 1  # 统计数据量
                    # if dataCount%2 == 0:
                    #     data_after_process.write(items)
                    #     data_after_process.write('\n')
                count += 1
            count = 0
            # data_to_write = data_origin_line.split('\t')[1]
            # data_to_write_new = data_to_write.replace('[', '').replace(']', '')
            # data_after_process.write(data_to_write_new)
            # data_after_process.write('\n')
    print("Data process finish")
    print(dataCount)


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
    for line in processed_data.readlines():
        # 逐行读入将，去掉换行
        value_line = line
        # 如果找到了种子关键词则为成功
        if seed_word in value_line:
            is_contain = True
            # 写入文件
            f_relate.write(value_line)
    if not is_contain:
        print("搜索的数据中不包含该种子关键字", seed_word, "请重新输入")
        processed_data.close()
        f_relate.close()
        return False
    else:
        print(seed_word, '相关搜索记录提取完毕')
        processed_data.close()
        f_relate.close()
        return True


# 统计词频
# 传入：关键词的搜索记录文本路径、分词后的存储路径、词频排序后的存储路径
def statistic(word_searching_log, word_apart_file, word_statistics):
    with open(word_searching_log, encoding="utf-8") as word_input_file:
        text = word_input_file.read()
    # 分词
    word_apart_outcome = [word for word in jieba.cut(text) if word not in stop_words]
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
    # 遍历中介关键词，查找竞争关键词
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
                    # 对于每个非中介关键词,非种子关键字的分词
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
        # 竞争关键字不与任何一个中介关键字相同
        for array_item in mid_word_array:
            if comp_item[0] == array_item:
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
    # 多进程共享的竞争度字典
    comp_rank = multiprocessing.Manager().dict()
    # 多进程
    processesArray = []
    # 对于每一个竞争关键词,计算竞争度
    for k_line in k_log:
        k_word = k_line.split('\n')[0]
        if len(k_word) <= 1: continue
        # 多进程优化
        thread = multiprocessing.Process(target=processComp,
                                         args=(s, seed_word, k_word, a_log, processed_search_log, comp_rank, lock))
        processesArray.append(thread)

    # 启动所有进程
    for p in processesArray:
        p.start()
    # 等待所有进程完成
    for p in processesArray:
        p.join()

    # 竞争度排序
    comp_ranked = sorted(comp_rank.items(), key=lambda x: x[1], reverse=True)
    for item in comp_ranked:
        comp_result_file.write((str(item[0]) + ' comp:' + str(item[1])))
        comp_result_file.write('\n')
    print(seed_word, '竞争性关键词comp测度计算完毕')


# 多进程计算竞争度
# 传入: 种子关键词搜索记录条数,种子关键词,中间关键字文本文件,整体搜索记录,竞争度集合,锁
def processComp(s, seed_word, k_word, a_log, processed_search_log, comp_rank, processLock):
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

    with processLock:
        comp_rank[k_word] = comp_k
    return comp_rank


# compKey算法结束


# 总控函数
# 传入：种子关键词
def forCompKey(seed_word):
    # 统计搜索记录
    seedWord = seed_word
    # starts = time.time() # 统计时间
    data_relate = './datas/SeedWordSearchLog/' + seed_word + ".txt"
    result = {}
    if not os.path.exists(data_relate):
        if record_search_log(seed_word=seedWord):
            # ends = time.time() # 统计时间
            # step_array.append("提取搜索记录") # 统计时间
            # step_cost.append(ends-starts) # 统计时间

            # 根据统计的搜索记录进行分词、词频统计

            # starts = time.time()  # 统计时间
            wordSearchLog = './datas/SeedWordSearchLog/' + seedWord + '.txt'
            wordApartFile = './datas/WordApartFile/' + seedWord + '_apart.txt'
            wordStatistics = './datas/WordStatistics/' + seedWord + '_statistics.txt'
            statistic(word_searching_log=wordSearchLog, word_apart_file=wordApartFile, word_statistics=wordStatistics)
            # ends = time.time()  # 统计时间
            # step_array.append("统计词频")  # 统计时间
            # step_cost.append(ends - starts)  # 统计时间

            # starts = time.time()  # 统计时间
            midWord = './datas/MidWord/' + seedWord + '_midWord.txt'
            findMidWords(seed_word=seedWord, word_mid=midWord)
            # ends = time.time()  # 统计时间
            # step_array.append("提取中介关键词")  # 统计时间
            # step_cost.append(ends - starts)  # 统计时间

            # starts = time.time()  # 统计时间
            compWord = './datas/CompWord/' + seedWord + '_compWord.txt'
            findCompWords(seed_word=seedWord, word_comp=compWord)
            # ends = time.time()  # 统计时间
            # step_array.append("提取竞争关键词")  # 统计时间
            # step_cost.append(ends - starts)  # 统计时间

            # starts = time.time()  # 统计时间
            compResult = './datas/Result/' + seedWord + '_result.txt'
            result = calculateComp(seed_word=seedWord, comp_result=compResult)
            # ends = time.time()  # 统计时间
            # step_array.append("计算竞争度")  # 统计时间
            # step_cost.append(ends - starts)  # 统计时间
            return result
        else:
            print('传入的关键词', seedWord, '无搜索记录')
    else:
        compResult = './datas/Result/' + seedWord + '_result.txt'
        count = 0
        with open(compResult, 'r', encoding='utf-8') as file:
            for line in file:
                result[count] = line
                count += 1
        return result



if __name__ == "__main__":
    # 读取日志并提取搜索记录处理数据
    log_to_file('./datas/Sogou', './datas/ProcessedData/ProcessedData.txt')

    # 定义停用词
    stop_words = set()
    with open('./datas/StopWords/baidu_stopwords.txt', 'r', encoding='utf-8') as file:
        for line in file:
            stop_words.add(line.strip())

    # 变量锁
    lock = multiprocessing.Lock()

    seed_word_array = ['英雄', '王者荣耀', 'qq', '微信', '阴阳师', '湖南', '陕西', '公务员', '白金', '篮球']
    # seed_word_array = ['英雄']
    time_array = []  # 统计各词用时
    # step_array = []
    # step_cost = []
    final_result = {}
    for items in seed_word_array:
        start = time.time()
        final_result[items] = forCompKey(items)
        end = time.time()
        print('用时', end - start, '秒')
        time_array.append(end - start)
    # 新建一个列表存放提取后的元组
    comp_rank_tuples = []

    # 遍历原始字典
    for seed_keyword, comp_list in final_result.items():
        # 遍历每个竞争关键词的竞争度
        for idx, item in comp_list.items():
            # 提取种子关键词、竞争关键词和竞争度，组成元组
            comp_values = (seed_keyword, item.split(' ')[0], float(item.split(':')[1]))
            # 将元组存入新的列表
            comp_rank_tuples.append(comp_values)

    # 输出结果
    print(comp_rank_tuples)

    # plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签（中文乱码问题）
    # plt.bar(seed_word_array, time_array)
    # # 在每个柱子上显示数字
    # for i, v in enumerate(time_array):
    #     plt.text(i, v, str(int(v)), ha='center', va='bottom', fontsize=10)
    # # 设置标题
    # plt.title("700W数据量各词用时(单位:秒)", fontsize=30, loc='center', color='r')
    # plt.savefig("./pic/700w.jpg")
    # plt.show()

    # plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签（中文乱码问题）
    # plt.bar(step_array, step_cost)
    # # 在每个柱子上显示数字
    # for i, v in enumerate(step_cost):
    #     plt.text(i, v, str(int(v)), ha='center', va='bottom', fontsize=10)
    # # 设置标题
    # plt.title("700W数据量各步骤用时(单位:秒)", fontsize=30, loc='center', color='r')
    # plt.savefig("./pic/700wPerStep.jpg")
    # plt.show()
