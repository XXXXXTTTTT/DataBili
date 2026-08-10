import pymysql
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings
from config import DB_CONFIG


#忽略所有警告
warnings.filterwarnings("ignore", category=UserWarning)

# 数据库连接配置

#本地
db_config = DB_CONFIG


# 数值型特征，去掉 `name` 和 `avatar_url` 等非数值列
NUMERCIAL_FEATURES = ['uid','followers', 'total_view', 'total_like', 'total_coin', 
                          'total_favorite', 'total_share', 'total_comment', 
                          'total_danmaku', 'total_duration', 'total_videos']
    
#最终聚类使用特征
FEATURES = ['log_followers', 'log_view', 'like_rate', 'engagement_rate', 'duration_engagement']


#从数据库中获取数据

def load_data_from_db():
    # 创建数据库连接
    conn = pymysql.connect(**db_config)
    query = """
        SELECT 
            uid, followers, total_view, total_like, total_coin, 
            total_favorite, total_share, total_comment, total_danmaku, 
            total_duration, total_videos
        FROM up_profile;
    """
    
    # 执行查询并加载数据
    df = pd.read_sql(query, conn)
    conn.close()  # 关闭数据库连接
    return df

#根据UID从数据库中获取数据

def get_data_from_db(uid):
    # 创建数据库连接
    conn = pymysql.connect(**db_config)
    
    # 使用参数化查询来防止 SQL 注入
    query = """
        SELECT 
            uid, followers, total_view, total_like, total_coin, 
            total_favorite, total_share, total_comment, total_danmaku, 
            total_duration, total_videos
        FROM up_profile
        WHERE uid = %s;
    """
    
    # 执行查询并加载数据
    df = pd.read_sql(query, conn, params=(uid,))
    conn.close()  # 关闭数据库连接
    
    if df.empty:
        print(f"错误: 未找到 uid 为 {uid} 的数据。")
        return None
    else:
        return df

#获取UP主显示信息
def get_showInfo_from_db(uid):
    # 创建数据库连接
    conn = pymysql.connect(**db_config)
    
    # 使用参数化查询来防止 SQL 注入
    query = """
        SELECT 
            uid, name, avatar_url,followers, total_view, total_like, total_coin, 
            total_favorite, total_share, total_comment, total_danmaku, 
            total_duration, total_videos
        FROM up_profile
        WHERE uid = %s;
    """
    
    # 执行查询并加载数据
    df = pd.read_sql(query, conn, params=(uid,))
    conn.close()  # 关闭数据库连接
    
    if df.empty:
        print(f"错误: 未找到 uid 为 {uid} 的数据。")
        return None
    else:
        return df

#处理数据

def compute_features(df: pd.DataFrame):
    """对原始数据进行特征处理，构造新特征"""
    # 复制数据以防止修改原数据
    df = df.copy()


    
    
    # 确保只选择数值型列
    df = df[NUMERCIAL_FEATURES]
    
    # 构造新特征
    
    
    #粉丝量对数
    df['log_followers'] = np.log10(df['followers'] + 1)
    
    #播放量对数
    df['log_view'] = np.log10(df['total_view'] + 1)
    
    #点赞率(点赞/总播放量)
    df['like_rate'] = df['total_like'] / df['total_view'].replace(0, np.nan)  # 防止除零错误
    
    
    # 每个互动行为的权重
    weights = {
        "total_coin": 0.3,      # 投币权重最高
        "total_share": 0.2,     # 分享
        "total_comment": 0.2,   # 评论
        "total_danmaku": 0.2,   # 弹幕
        "total_favorite": 0.1,  # 收藏
        "total_like": 0.05      # 点赞权重最低
    }
    
    # 视播放量为0的UP主为1，避免除零(防止有些UP把视频全删了的情况)
    df['total_view'] = df['total_view'].replace(0, 1)  
    
    # 综合互动率
    df['engagement_rate'] = (
        df['total_coin'] * weights['total_coin'] +
        df['total_share'] * weights['total_share'] +
        df['total_comment'] * weights['total_comment'] +
        df['total_danmaku'] * weights['total_danmaku'] +
        df['total_favorite'] * weights['total_favorite'] +
        df['total_like'] * weights['total_like']
    ) / df['total_view'].replace(0, np.nan)  # 使用播放量做标准化


    #中间量平均视频时长
    df['avg_duration'] = df['total_duration'] / df['total_videos'].replace(0, np.nan)

    # 复合特征：视频时长和互动率的结合
    df['duration_engagement'] = (df['avg_duration'] * df['engagement_rate']) / (df['avg_duration'] + 1)

    # 删除含有缺失值的行
    df.dropna(inplace=True)
    
    # 2. 对所有特征进行标准化
    # scaler = StandardScaler()
    # scaled_features = scaler.fit_transform(df[['followers', 'total_view', 'like_rate', 'engagement_rate', 'duration_engagement']])
    
    # 标准化后的数据
    # scaled_df = pd.DataFrame(scaled_features, columns=['followers', 'total_view', 'like_rate', 'engagement_rate', 'duration_engagement'])
    # return scaled_df

    return df

#特征标准化

def norm_data(df):
    # 提取聚类特征列
    X = df[FEATURES]

    # 标准化特征数据
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, scaler


def save_processed_data(df: pd.DataFrame, filename="cluster_ready.csv"):
    """保存处理后的数据到 CSV 文件"""
    # 只保留聚类所需的特征
    
    # cluster_data = df[['followers', 'total_view', 'like_rate', 'engagement_rate', 'duration_engagement']]
    cluster_data = df[['uid', 'log_followers', 'log_view', 'like_rate', 'engagement_rate', 'duration_engagement']]
    
    # 保存为 CSV 文件
    cluster_data.to_csv(filename, index=False)
    print(f"数据处理完毕并已保存为 {filename}")



#API接口
def main():
    # 步骤 1：从数据库获取数据
    df = load_data_from_db()

    # 步骤 2：特征处理
    df_processed = compute_features(df)

    # 步骤 3：保存处理后的数据
    save_processed_data(df_processed)

#测试脚本
if __name__ == '__main__':
    main()


