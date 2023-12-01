import os.path
import redis
from datashape import null
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from main import record_search_log, statistic, findMidWords, findCompWords, calculateComp

app = Flask(__name__)
num = redis.Redis(host='localhost', port=6379, db=11, decode_responses=True)
num.set('count', 0)
CORS(app, resources=r'/*')
r = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
for i in range(10):
    r[i] = redis.Redis(host='localhost', port=6379, db=i, decode_responses=True)

@app.route('/')
def hello_world():  # put application's code here
    return render_template('Main.html')

@app.route('/getResult', methods=['GET'])
def forCompKey():
    # 统计搜索记录
    seed_word = str(request.args.get('seed_word'))
    print(seed_word)
    seedWord = seed_word
    result = {}
    data_relate = './datas/SeedWordSearchLog/' + seed_word + ".txt"
    if not os.path.exists(data_relate):
        # 根据统计的搜索记录进行分词、词频统计
        if record_search_log(seed_word=seedWord):
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
            count = 0

            with open(compResult, 'r', encoding='utf-8') as file:
                for line in file:
                    result[count] = line
                    count += 1

            return jsonify({"success": 'success', "msg": "请求成功", "data": result})
        else:
            return jsonify({"error": 'error', "msg": "请求失败，输入关键词没有相关搜索记录"})
    else:
        compResult = './datas/Result/' + seedWord + '_result.txt'
        count = 0
        with open(compResult, 'r', encoding='utf-8') as file:
            for line in file:
                result[count] = line
                count += 1
    print(result[0])
    a = int(num.get('count'))
    # a是用户不重复搜索种子关键词的次数
    print(result)
    b = 0
    # b等于1就说明数据库中有该种子关键词了，不存入
    for j in range(a):
        if r[j].get('seedWord') == seedWord:
            b = 1
            break

    if b != 1:
        if r[a].get('seedWord') != seedWord:
            r[a].set('seedWord', seedWord)
            r[a].delete('compWord')
            for i in range(10):
                r[a].append('compWord', result[i])
            a = int(num.get('count')) + 1

    num.set('count', a)
    return jsonify({"success": 'success', "msg": "请求成功", "data": result})


@app.route('/returnEvaluateResult', methods=['PUT'])
def update_comp_key():
    seed_word = str(request.args.get('seed_word'))
    comp_word = str(request.args.get('comp_word'))
    comp_key = str(request.args.get('comp_key'))
    return jsonify({"success": 'success', "msg": "请求成功"})

# @app.route('/search', methods=['GET'])
# def search_by_seed_word():
#     seed_word = str(request.args.get('seed_word'))
#     print(seed_word)
#     processed_data = open('./datas/ProcessedData/ProcessedData.txt', 'r', encoding="utf-8")
#     data_relate = './datas/SeedWordSearchLog/' + seed_word + ".txt"
#     seed_word_log = []
#     # 创建写入文件，将与种子关键字相关的内容写入文件中
#     f_relate = open(data_relate, 'w', encoding='utf-8')
#     # 判断是否不包含种子关键字
#     is_contain = False
#     # 判断是否包含种子关键字
#     for line in processed_data.readlines():
#         # 逐行读入将，去掉换行
#         value_line = line
#         # 逐条匹配，如果找到了字符串则为成功
#         if seed_word in value_line:
#             is_contain = True
#             seed_word_log.append(value_line.replace("\n", ""))
#             # 写入文件
#             f_relate.write(value_line)
#     if not is_contain:
#         print("搜索的数据中不包含该种子关键字", seed_word, "请重新输入")
#         return jsonify({"error": 'error', "msg": "请求失败"})
#     else:
#         print(seed_word, '相关搜索记录提取完毕')
#         print(seed_word_log)
#         return jsonify({"success": 'success', "msg": "请求成功", "data": seed_word_log})

if __name__ == '__main__':
    app.run()
