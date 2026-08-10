const express = require('express');
const axios = require('axios');
const OpenAI = require('openai');
const { getLlmConfig } = require('../config/llm');
const { HttpsProxyAgent } = require('https-proxy-agent');
const router = express.Router();

const { Jieba } = require('@node-rs/jieba-win32-x64-msvc');
const jieba = new Jieba();

// const Segment = require('segment');
// const segment = new Segment();
// segment.useDefault();

let fetch;
(async () => { fetch = (await import('node-fetch')).default; })();

// 基本配置
const comment_url = "https://api.aicu.cc/api/v3/search/getreply?uid={uid}&pn={pn}&ps=100&mode=0&keyword=";
const user_info_url = "https://api.bilibili.com/x/web-interface/card?mid=";
function createLlmClient() {
    const config = getLlmConfig();
    if (!config.apiKey) {
        return null;
    }
    return new OpenAI({ baseURL: config.baseURL, apiKey: config.apiKey });
}

//词频统计
// 停用词列表
const STOP_WORDS = new Set([
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她', '它', '我们', '你们', '他们', '这个', '那个', '什么', '怎么', '为什么', '因为', '所以', '但是', '如果', '虽然', '然后', '还是', '或者', '以及', '以后', '之前', '现在', '已经', '正在', '可以', '应该', '需要', '想要', '希望', '觉得', '认为', '知道', '明白', '理解', '喜欢', '讨厌', '支持', '反对','回复'
]);

function countWords(comments,name) {
    const wordMap = new Map();
    STOP_WORDS.add(name);
    
    comments.forEach(comment => {
        if (!comment.comment || typeof comment.comment !== 'string') {
            return;
        }
        

        // 替换原 segment 的分词逻辑
        const words = jieba.cut(comment.comment, true);  // false 表示不使用 HMM 模型

        // 使用 segment 进行分词
        // const words = segment.doSegment(comment.comment, {
        //     simple: true  // 返回简单的字符串数组
        // });
        
        words.forEach(word => {
            const cleanWord = word.trim();
            
            if (cleanWord.length >= 2 && 
                /[\u4e00-\u9fa5]/.test(cleanWord) && 
                !STOP_WORDS.has(cleanWord) &&
                !/^[\d\s\p{P}]+$/u.test(cleanWord)) {
                
                wordMap.set(cleanWord, (wordMap.get(cleanWord) || 0) + 1);
            }
        });
    });
    return Array.from(wordMap.entries())
        .map(([word, value]) => ({ word, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 20);
}

// 获取用户基本信息
async function getUserInfo(uid) {
    try {
        // 配置代理
        const proxyUrl = 'http://127.0.0.1:7890';
        const httpsAgent = new HttpsProxyAgent(proxyUrl);
        
        const url = user_info_url + uid;
        const response = await axios.get(url, {
            timeout: 10000,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
            },
            httpsAgent: httpsAgent,
            proxy: false
        });
        
        if (response.data && response.data.code === 0 && response.data.data && response.data.data.card) {
            const card = response.data.data.card;
            return {
                name: card.name || '',
                face: card.face || ''
            };
        } else {
            console.log('获取用户信息失败或用户不存在');
            return {
                name: '',
                face: ''
            };
        }
    } catch (error) {
        console.error('获取用户信息时发生错误:', error.message);
        return {
            name: '',
            face: ''
        };
    }
}

// 获取所有评论数据
async function getAllComments(uid) {
    const allReplies = [];
    let page = 1;
    let hasMore = true;
    const MAX_PAGES = 200; // 最多请求200页
    
    // 配置代理
    const proxyUrl = 'http://127.0.0.1:7890';
    const httpsAgent = new HttpsProxyAgent(proxyUrl);
    
    while (hasMore && page <= MAX_PAGES) {
        try {
            const url = comment_url.replace('{uid}', uid).replace('{pn}', page);
            const response = await axios.get(url, {
                timeout: 10000,
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
                },
                httpsAgent: httpsAgent,
                proxy: false
            });
            // 修正数据结构的访问方式
            if (response.data && response.data.code === 0 && response.data.data && response.data.data.replies) {
                const replies = response.data.data.replies;
                if (replies.length === 0) {
                    hasMore = false;
                } else {
                    // 根据实际返回的数据结构提取评论和时间戳
                    const pageReplies = replies.map(reply => ({
                        comment: reply.message || '',
                        timestamp: reply.time || Date.now()
                    }));
                    
                    allReplies.push(...pageReplies);
                    console.log(`第${page}页获取成功，获得${pageReplies.length}条评论`);
                    page++;
                    
                    // 检查是否已经是最后一页
                    if (response.data.data.cursor && response.data.data.cursor.is_end === true) {
                        hasMore = false;
                    } else if (replies.length < 100) {
                        hasMore = false;
                    }
                }
            } else {
                // 如果code不为0或没有数据，结束获取
                console.log(`第${page}页返回状态异常或无数据`);
                hasMore = false;
            }
            
            // 添加延时避免请求过于频繁
            await new Promise(resolve => setTimeout(resolve, 500));
            
        } catch (error) {
            console.error(`获取第${page}页数据失败:`, error.message);
            hasMore = false;
        }
    }
    
    return allReplies;
}


function calculateTokens(text) {
    let tokens = 0;
    for (const char of text) {
        // 判断是否为中文字符（Unicode 范围大致为 4E00-9FFF）
        if (char.match(/[\u4e00-\u9fff]/)) {
            tokens += 1; // 中文字符
        } else {
            tokens += 0.6; // 英文字符或其他
        }
    }
    return tokens;
}

function extractCommentsWithTokenLimit(replies, tokenLimit = 64000) {
    const comments = [];
    let totalTokens = 0;
    for (const item of replies) {
        const comment = item.comment || "";
        const commentTokens = calculateTokens(comment);

        // 检查是否会超过 token 限制
        if (totalTokens + commentTokens <= tokenLimit) {
            comments.push(comment);
            totalTokens += commentTokens;
        } else {
            // 如果当前评论会导致超出，尝试截取部分内容
            let remainingTokens = tokenLimit - totalTokens;
            if (remainingTokens > 0) {
                let partialComment = "";
                let currentTokens = 0;

                for (const char of comment) {
                    const charTokens = char.match(/[\u4e00-\u9fff]/) ? 0.6 : 0.3;
                    if (currentTokens + charTokens <= remainingTokens) {
                        partialComment += char;
                        currentTokens += charTokens;
                    } else {
                        break;
                    }
                }
                comments.push(partialComment);
            }
            break; // 超出限制后停止处理
        }
    }
    return comments;
}

// 调用 DeepSeek API 分析用户特征
async function analyzeUserComments(replies) {
    const re_array = extractCommentsWithTokenLimit(replies,60000);
    const prompt = `现在你是一名b站的数据分析师.你将接受指定格式的数据,并且确保返回指定格式的数据.
接收信息:
${JSON.stringify({ re_array }, null, 2)}

这些数据是,用户的所有评论内容.请你根据用户的评论内容,进行分析这个用户的特点.
请注意请对用户的分析不要千篇一律使用固定套词.
请总结所有的comment内容.为这个用户生成1~5个标签(随机一些)形式:
"user_keyword": ["word1","word2","word3"]

作为一个放松的活跃的社区,请为用户的评论进行打分,尽量给的细致一些(满分10分,可以是小数),评判依据如下:
加分项:
提供有价值的知识或科普,幽默有趣引发共鸣,有创见的观点或深度分析.优质互动回复他人提问,分段清晰的长评论
减分项:
无意义水评（如"第一""666"）,过度玩梗影响理解,引战/攻击言论,剧透未预警,广告/引流信息,阴阳怪气(这个请你重点注意),以及带有讽刺和负面情绪较重,戾气较重.严格扣分.如果有类似辱骂的言论,必须给低分.

请酌情给分,不要都得差不多的6~7分,有着鲜明的给分理由.并且给出评语,评语内容多少,根据评论数量,和能发掘的信息来进行合理处理.格式:
"friendly_score": {
    "score":value,
    "comment":""
},

最后综合分析推测用户兴趣所在,给出分析和推测.格式:
"interest":""

# 最终确保返回的数据格式!!!!!!
{
    "user_keyword": ["word1","word2","word3"],
    "friendly_score": {
        "score":value,
        "comment":""
    },
    "interest":""
}`;

    try {
        const openai = createLlmClient();
        if (!openai) {
            throw new Error('未配置 DEEPSEEK_API_KEY');
        }
        const completion = await openai.chat.completions.create({
            messages: [
                { role: "system", content: "You are a professional data analyst. Return only valid JSON format." },
                { role: "user", content: prompt }
            ],
            model: getLlmConfig().model,
            temperature: 0.7,
            type: 'json_object'
        });
        
        const content = completion.choices[0].message.content;
        
        // 尝试解析JSON
        try {
            return JSON.parse(content);
        } catch (parseError) {
            // 如果直接解析失败，尝试提取JSON部分
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
            throw new Error('无法解析AI返回的数据');
        }
        
    } catch (error) {
        console.error('DeepSeek API 调用失败:', error);
        // 返回默认分析结果
        return {
            user_keyword: ["普通用户"],
            friendly_score: {
                score: 5.0,
                comment: "分析过程中出现错误，给出默认评分"
            },
            interest: "暂无法分析用户兴趣"
        };
    }
}

// 主要的路由处理
router.get('/', async (req, res) => {
    try {
        const { uid } = req.query;
        
        if (!uid) {
            return res.json({
                code: 1,
                message: "缺少uid参数"
            });
        }
        
        console.log(`开始分析用户 ${uid} 的评论数据...`);
        
        // 1. 获取用户基本信息
        const userInfo = await getUserInfo(uid);
        console.log(`获取用户基本信息: ${userInfo.name}`);
        
        // 2. 获取所有评论数据
        const replies = await getAllComments(uid);
        if (replies.length === 0) {
            return res.json({
                code: -1,
                message: "未找到用户或用户无评论数据",
                uid: uid,
                name: userInfo.name,
                face: userInfo.face
            });
        }
        
        console.log(`获取到 ${replies.length} 条评论`);
        
        // 3. 统计词频
        const word_count = countWords(replies,userInfo.name);

        console.log(word_count);
        // 4. 调用 DeepSeek 分析
        const aiAnalysis = await analyzeUserComments(replies);
        
        // 5. 组装最终结果，包含用户基本信息
        const result = {
            code: 0,
            uid: uid,
            name: userInfo.name,
            face: userInfo.face,
            replies: replies,
            word_count: word_count,
            user_keyword: aiAnalysis.user_keyword || ["普通用户"],
            friendly_score: aiAnalysis.friendly_score || {
                score: 5.0,
                comment: "默认评分"
            },
            interest: aiAnalysis.interest || "暂无法确定兴趣"
        };
        
        console.log(`用户 ${uid} 分析完成`);
        res.json(result);
        
    } catch (error) {
        console.error('处理请求时发生错误:', error);
        res.json({
            code: 1,
            message: "服务器内部错误",
            error: error.message
        });
    }
});

module.exports = router;
